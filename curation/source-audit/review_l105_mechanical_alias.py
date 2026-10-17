"""Register one source-checked course-title alias; preserve all knowledge records.

The alias review is linked to its existing supporting claim. It is not a new
semantic approval of claims or a trading implementation.
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

BASE='0.1.0-review-b30e6980504f'
SPECS=[
    ('机械化操作','机械操作','lower-l105-c-stage-mechanical-follow-structural-joints',
     ['volume_2-5332cd1b6038-p0382-b003'],['机械化操作'],
     '第105课标题远离聪明、机械操作，紧接正文定义机械化操作的本质；名称映射限本课股票操作概念，不把104机械化思维批评或国家机械工程合并。'),
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
            title=db.execute('SELECT * FROM passages WHERE id=?',('volume_2-5332cd1b6038-p0382-b001',)).fetchone()
            assert title['unit_id']=='lesson-105' and title['role']=='author_body' and title['speaker']=='缠中说禅'
            assert '远离聪明、机械操作' in title['text'] and p['unit_id']==title['unit_id']
            sources.append({'passage_id':title['id'],'evidence_id':None,'source_type':'course_title_context',
                'quote':title['text'],'pdf_page':title['pdf_page'],'role':title['role'],'speaker':title['speaker'],
                'published_at':title['published_at'],'source_text_sha256':hashlib.sha256(title['text'].encode()).hexdigest()})
            before=json.loads(row['aliases']);after=before+[alias]
            proposals.append({'concept_id':row['id'],'label':label,'before':before,'after':after,
                'supporting_claim_id':cid,'source_evidence':sources,'reason':reason})
        now=datetime.now(timezone.utc)
        backup=KB.parent/'backups'/(now.strftime('%Y%m%dT%H%M%S%fZ')+'-alias-l105-mechanical')
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
                 'Codex 主代理 / 阶段D第105课标题别名',now.isoformat(),j(checks),'reviewed',item['reason']))
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
        'aliases':proposals,'observed_before':{'query':'机械操作','search_results':[],'concept_status':'unknown_concept'},'claims_evidence_passages_relations_unchanged':True,'counts':counts,
        'backup_directory':str(backup),'independent_review_claimed':False,
        'limits':['仅为第105课标题与正文的同一操作概念增名称映射；标题是来源上下文，没有新造命题证据ID。','不引入交易程序或合并104物理思维/国家安全的机械化语境。']}
    path=Path(__file__).with_name('stage-d-l105-mechanical-alias.json')
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'base_graph_version':BASE,'graph_version':version,'aliases_added':1,
        'claims_evidence_passages_relations_unchanged':True,'backup_directory':str(backup)},ensure_ascii=False))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
