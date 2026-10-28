"""Register exactly two source-checked aliases; preserve all knowledge records.

The alias review is linked to its existing supporting claim. It is not a new
semantic approval of claims and does not merge religious or mathematical terms.
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
from curation_contract import digest, j
from graph_release import refresh_version, update_manifest

BASE='0.1.0-review-6116140b24d9'
SPECS=[
    ('布林通道','BOLL','lower-l090-c-stage-boll-three-bands-strong-zones',
     ['volume_2-5332cd1b6038-p0262-b006'],['布林通道','BOLL'],
     '作者明确给布林通道的指标缩写BOLL；只作同一市场指标的名称映射，不新增指标参数。'),
    ('中阴阶段','中阴身阶段','lower-l088-c-stage-intermediate-stage-definition',
     ['volume_2-5332cd1b6038-p0239-b007','volume_2-5332cd1b6038-p0241-b005'],['中阴身','中阴阶段'],
     '同课先借中阴身的阶段作比、后称中阴阶段，映射仅限市场阶段全称；不把宗教中阴身裸词作为全领域同义词。'),
]

def snapshot(db):
    return {t:[tuple(r) for r in db.execute(f'SELECT * FROM {t} ORDER BY id')]
            for t in ['claims','evidence','passages','relations']}

def main():
    db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:
        assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])==BASE
        assert json.loads((KB/'manifest.json').read_text(encoding='utf-8'))['graph_version']==BASE
        originals=snapshot(db);proposals=[]
        all_concepts=[dict(r) for r in db.execute('SELECT * FROM concepts')]
        occupied={value for r in all_concepts for value in [r['label']]+json.loads(r['aliases'])}
        for label,alias,cid,pids,terms,reason in SPECS:
            row=dict(db.execute('SELECT * FROM concepts WHERE label=?',(label,)).fetchone())
            assert alias not in occupied
            c=db.execute('SELECT * FROM claims WHERE id=?',(cid,)).fetchone()
            assert c and c['review_status']=='reviewed' and row['id'] in json.loads(c['concept_ids'])
            sources=[]
            for pid in pids:
                p=db.execute('SELECT * FROM passages WHERE id=?',(pid,)).fetchone()
                e=db.execute('SELECT * FROM evidence WHERE claim_id=? AND passage_id=?',(cid,pid)).fetchone()
                assert p and e and p['speaker']=='缠中说禅' and p['role']=='author_body'
                assert p['text'][e['quote_start']:e['quote_end']]==e['quote']
                sources.append({'passage_id':pid,'evidence_id':e['id'],'quote':e['quote'],
                    'pdf_page':p['pdf_page'],'source_text_sha256':hashlib.sha256(p['text'].encode()).hexdigest()})
            assert all(term in ''.join(s['quote'] for s in sources) for term in terms)
            before=json.loads(row['aliases']);after=before+[alias]
            proposals.append({'concept_id':row['id'],'label':label,'before':before,'after':after,
                'supporting_claim_id':cid,'source_evidence':sources,'reason':reason})
        now=datetime.now(timezone.utc)
        backup=KB.parent/'backups'/(now.strftime('%Y%m%dT%H%M%S%fZ')+'-aliases-l088-l090')
        backup.mkdir(parents=True,exist_ok=False)
        with sqlite3.connect(backup/'graph.sqlite') as target:db.backup(target)
        shutil.copy2(KB/'manifest.json',backup/'manifest.json')
    finally:db.close()
    db=sqlite3.connect(KB/'graph.sqlite');db.row_factory=sqlite3.Row
    try:
        db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
        assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])==BASE
        for item in proposals:
            assert json.loads(db.execute('SELECT aliases FROM concepts WHERE id=?',(item['concept_id'],)).fetchone()[0])==item['before']
            db.execute('UPDATE concepts SET aliases=? WHERE id=?',(j(item['after']),item['concept_id']))
            checks={'review_type':'source_checked_concept_alias','base_graph_version':BASE,**item,
                'claim_semantics_approval_changed':False,'independent_review_claimed':False}
            db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?)',
                ('review-'+digest('concept-alias:'+item['concept_id']+j(item['after'])),item['supporting_claim_id'],
                 'Codex 主代理 / 阶段D两项已核别名',now.isoformat(),j(checks),'reviewed',item['reason']))
        assert snapshot(db)==originals
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        version=refresh_version(db);db.commit()
        counts={t:db.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
                for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
    except Exception:
        db.rollback();raise
    finally:db.close()
    update_manifest(KB,version,counts=counts,updated_at=now.isoformat())
    report={'stage':'D-source-checked-aliases','base_graph_version':BASE,'graph_version':version,
        'aliases':proposals,'claims_evidence_passages_relations_unchanged':True,'counts':counts,
        'backup_directory':str(backup),'independent_review_claimed':False,
        'limits':['只新增BOLL与中阴身阶段两项名称映射。','不新增指标参数，不把宗教裸词无条件合并。']}
    path=Path(__file__).with_name('stage-d-l088-l090-aliases.json')
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'base_graph_version':BASE,'graph_version':version,'aliases_added':2,
        'claims_evidence_passages_relations_unchanged':True,'backup_directory':str(backup)},ensure_ascii=False))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
