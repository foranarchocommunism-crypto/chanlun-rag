"""Add one source-checked ambiguity annotation; keep claim text and citations."""
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

BASE='0.1.0-review-d536de7be067'
TARGET='lower-l098-c-stage-divergence-return-then-classify'
SOURCES=[TARGET,'upper-l024-c-stage-standard-divergence-retrace-b-center',
         'lower-l099-c-stage-completed-type-next-at-least-larger-center',
         'lower-l099-c-stage-healthy-intermediate-in-last-center']
NOTE=('跨课范围复核：第24课明确区分趋势背驰回B中枢与盘整背驰可能形成三买、未必同等回跌；'
      '第98课此段无论盘整背驰或真正背驰都回原中枢的概括，与此前说明存在对象范围差异；'
      '第99课另以走势类型完成为前提说后续至少高一级中枢。仅固定汇编尚不足以统一这些范围，'
      '保留原句及各课证据，不因日期自动撤回；不把盘整背驰一律必回原中枢作为已无歧义规则。')

def stable_tables(db):
    result={}
    for table in ['documents','pages','units','passages','figures','concepts','evidence','relations']:
        h=hashlib.sha256()
        for row in db.execute(f'SELECT * FROM {table} ORDER BY id'):
            h.update(j(dict(row)).encode());h.update(b'\n')
        result[table]=h.hexdigest()
    return result

def main():
    db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:
        assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])==BASE
        assert json.loads((KB/'manifest.json').read_text(encoding='utf-8'))['graph_version']==BASE
        claims={r['id']:dict(r) for r in db.execute('SELECT * FROM claims')}
        before=claims[TARGET];assert before['review_status']=='reviewed' and before['ambiguity_status']=='none'
        sources=[]
        for cid in SOURCES:
            assert claims[cid]['review_status']=='reviewed'
            evidence=[]
            for e in db.execute('SELECT * FROM evidence WHERE claim_id=? ORDER BY id',(cid,)):
                p=db.execute('SELECT * FROM passages WHERE id=?',(e['passage_id'],)).fetchone()
                assert p['speaker']=='缠中说禅' and p['role'] in ['author_body','author_reply','author_commentary']
                assert p['text'][e['quote_start']:e['quote_end']]==e['quote']
                evidence.append({'evidence_id':e['id'],'passage_id':p['id'],'pdf_page':p['pdf_page'],
                    'role':p['role'],'speaker':p['speaker'],'quote':e['quote'],
                    'source_text_sha256':hashlib.sha256(p['text'].encode()).hexdigest()})
            assert evidence;sources.append({'claim_id':cid,'text':claims[cid]['text'],'evidence':evidence})
        assert '并不一定都要大幅下跌' in ''.join(e['quote'] for s in sources for e in s['evidence'])
        assert '无论是盘整背驰还是真正的背驰' in ''.join(e['quote'] for e in sources[0]['evidence'])
        original_tables=stable_tables(db)
        now=datetime.now(timezone.utc);backup=KB.parent/'backups'/(now.strftime('%Y%m%dT%H%M%S%fZ')+'-return-scope-l024-l098-l099')
        backup.mkdir(parents=True,exist_ok=False)
        with sqlite3.connect(backup/'graph.sqlite') as target:db.backup(target)
        shutil.copy2(KB/'manifest.json',backup/'manifest.json')
    finally:db.close()
    after={**before,'ambiguity_status':'return_guarantee_cross_lesson_scope','review_note':before['review_note']+'。'+NOTE}
    checks={'review_type':'source_checked_cross_lesson_ambiguity','base_graph_version':BASE,
        'claim_id':TARGET,'before':{k:before[k] for k in ['ambiguity_status','review_note']},
        'after':{k:after[k] for k in ['ambiguity_status','review_note']},'sources':sources,
        'claim_text_conditions_evidence_unchanged':True,'independent_review_claimed':False}
    db=sqlite3.connect(KB/'graph.sqlite');db.row_factory=sqlite3.Row
    try:
        db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
        assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])==BASE
        assert dict(db.execute('SELECT * FROM claims WHERE id=?',(TARGET,)).fetchone())==before
        db.execute('UPDATE claims SET ambiguity_status=?,review_note=? WHERE id=?',
            (after['ambiguity_status'],after['review_note'],TARGET))
        db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?)',
            ('review-'+digest('cross-lesson-return-scope:'+TARGET),TARGET,
             'Codex 主代理 / 阶段D第24/98/99课跨课范围复核',now.isoformat(),j(checks),'reviewed',NOTE))
        assert {r['id']:dict(r) for r in db.execute('SELECT * FROM claims')}=={**claims,TARGET:after}
        assert stable_tables(db)==original_tables
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        version=refresh_version(db);db.commit()
        counts={t:db.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
                for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
    except Exception:
        db.rollback();raise
    finally:db.close()
    update_manifest(KB,version,counts=counts,updated_at=now.isoformat())
    report={'stage':'D-cross-lesson-ambiguity','base_graph_version':BASE,'graph_version':version,
        'changes':[checks],'counts':counts,'backup_directory':str(backup),
        'all_other_claims_unchanged':True,'source_evidence_concepts_relations_unchanged':True,
        'pending_not_closed':True,'limits':['只补一个已复核命题的歧义标记及说明。','未声称三课范围已统一或任何一课已被明确撤回。']}
    Path(__file__).with_name('stage-d-l024-l098-l099-return-scope.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'base_graph_version':BASE,'graph_version':version,'claims_annotated':1,
        'text_and_evidence_unchanged':True,'backup_directory':str(backup)},ensure_ascii=False))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
