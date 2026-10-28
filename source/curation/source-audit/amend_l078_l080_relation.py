"""Correct one newly published overstrong relation, preserving every claim.

The initial batch is archived by exact bytes. The final batch and builder both
use related; a new review makes the graph correction auditable and atomic.
"""
import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT=Path(__file__).resolve().parents[2]
KB=AGENT.parent/'shared-knowledge/v0.1.0'
sys.path.insert(0,str(AGENT/'tools'))
from curation_contract import digest, j, validate_records
from graph_release import refresh_version, update_manifest

def main():
    base='0.1.0-review-f74f3c05f891'
    batch=AGENT/'curation/lower/c_stage_l078_l080.reviewed.jsonl'
    archive=batch.with_name('c_stage_l078_l080.initial-reviewed.jsonl')
    raw=batch.read_bytes();initial_hash=hashlib.sha256(raw).hexdigest()
    assert initial_hash=='bd33e1b6fea9d22d824147a56365b6010d23184988f770460f1a60115789fa4e'
    records=[json.loads(x) for x in raw.decode('utf-8').splitlines() if x.strip()]
    cid='lower-l080-c-stage-feature-sequence-three-elements-general'
    index=next(i for i,r in enumerate(records) if r['id']==cid)
    record=records[index]
    old_support=json.loads(j(record['relations']))
    assert old_support==[{'source':'特征序列','target':'分型','type':'requires'}]
    record['relations'][0]['type']='related'
    db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:
        assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])==base
        validate_records(db,KB,[(record,batch,index+1)])
        before_claims=[tuple(r) for r in db.execute('SELECT * FROM claims ORDER BY id')]
        before_evidence=[tuple(r) for r in db.execute('SELECT * FROM evidence ORDER BY id')]
        relation=dict(db.execute("SELECT * FROM relations WHERE id='relation-e8ad5ab70e5ab8c8'").fetchone())
        assert json.loads(relation['claim_ids'])==[cid] and relation['type']=='requires'
        new_id='relation-'+digest(relation['source']+':related:'+relation['target'])
        assert not db.execute('SELECT 1 FROM relations WHERE id=?',(new_id,)).fetchone()
        now=datetime.now(timezone.utc)
        backup=KB.parent/'backups'/(now.strftime('%Y%m%dT%H%M%S%fZ')+'-relation-l078-l080')
        backup.mkdir(parents=True,exist_ok=False)
        with sqlite3.connect(backup/'graph.sqlite') as target:db.backup(target)
        shutil.copy2(KB/'manifest.json',backup/'manifest.json')
    finally:db.close()
    assert not archive.exists()
    archive.write_bytes(raw)
    corrected_raw=('\n'.join(j(r) for r in records)+'\n').encode('utf-8')
    corrected_hash=hashlib.sha256(corrected_raw).hexdigest()
    batch.write_bytes(corrected_raw)
    reason='三个元素才可能有分型只支持两概念关联，不能推出特征序列必须有分型；删除本批过强requires并改related。'
    checks={'review_type':'relation_support_correction','semantic_approval_scope':'仅所列关系强度',
      'before':relation,'after':{**relation,'id':new_id,'type':'related'},'reason':reason,
      'initial_curation_sha256':initial_hash,'initial_curation_archive':archive.name,
      'curation_file':batch.name,'line':index+1,'batch_sha256':corrected_hash,
      'claim_record_sha256':hashlib.sha256(j(record).encode()).hexdigest(),
      'base_graph_version':base,'claims_and_evidence_unchanged':True,
      'independent_review_claimed':False,'semantic_entailment_automatically_proven':False}
    db=sqlite3.connect(KB/'graph.sqlite');db.row_factory=sqlite3.Row
    try:
        db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
        assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])==base
        db.execute('UPDATE relations SET id=?,type=? WHERE id=?',(new_id,'related',relation['id']))
        db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?)',('review-'+digest(cid+j(record)),cid,
          'Codex 主代理 / 阶段C第78至80课关系复核',now.isoformat(),j(checks),'reviewed',reason))
        assert [tuple(r) for r in db.execute('SELECT * FROM claims ORDER BY id')]==before_claims
        assert [tuple(r) for r in db.execute('SELECT * FROM evidence ORDER BY id')]==before_evidence
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        version=refresh_version(db);db.commit()
        counts={t:db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
    except Exception:
        db.rollback();batch.write_bytes(raw)
        raise
    finally:db.close()
    update_manifest(KB,version,counts=counts,updated_at=now.isoformat())
    report={'stage':'C-relation-correction','base_graph_version':base,'graph_version':version,
      'before':relation,'after':{**relation,'id':new_id,'type':'related'},'reason':reason,
      'source_passage_id':f'volume_2-5332cd1b6038-p0173-b003','claims_and_evidence_unchanged':True,
      'initial_batch_archive':str(archive),'initial_batch_sha256':initial_hash,'final_batch_sha256':corrected_hash,
      'backup_directory':str(backup),'counts':counts,'independent_review_claimed':False}
    (Path(__file__).parent/'stage-c-l078-l080-relation-amendment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
