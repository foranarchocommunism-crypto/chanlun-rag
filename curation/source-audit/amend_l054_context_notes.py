"""Correct two stale API caveats using a current read-only context audit."""
import hashlib,json,shutil,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
sys.path.insert(0,str(AGENT/'tools'))
from graph_release import refresh_version
def j(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 proof=read(AUDIT/'stage-h-annotation-split-verification.json');base=proof['graph_version'];assert proof['pass'] and all(not r['missing'] for r in proof['short_answer_context_live_audit'])
 c=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
 try:
  assert json.loads(c.execute("select value from metadata where key='graph_version'").fetchone()[0])==base
  specs=[('upper-l054-c-stage-rare-second-buy-below-first-or-second-sell-above-first-approved','近邻API上下文未覆盖跨页整组问题，研究时须连读PDF408/409及本条条件。'),('upper-l054-c-stage-second-center-guarantee-no-larger-level-wording-reader-item-two','当前API邻段不自动覆盖整个跨页问题须按ID联读。')]
  changes=[]
  for id,old in specs:
   r=dict(c.execute('select * from claims where id=?',(id,)).fetchone());assert r['review_status']=='reviewed' and r['review_note'].count(old)==1
   new='2026-10-21专项复核：当前evidence返回PDF408至410，已核包含完整编号问题；仍须按问题编号/本条条件联读，不能把读者前提冒作者明说。'
   changes.append(dict(id=id,before_review_note=r['review_note'],after_review_note=r['review_note'].replace(old,new)))
  unchanged={t:[tuple(r) for r in c.execute(f'select * from {t} order by id')] for t in ['documents','pages','units','passages','figures','concepts','evidence','relations']};before_claims={r['id']:dict(r) for r in c.execute('select * from claims')}
  now=datetime.now(timezone.utc);backup=KB.parent/'backups'/(now.strftime('%Y%m%dT%H%M%S%fZ')+'-context-note-amendment');backup.mkdir(parents=True,exist_ok=False)
  with sqlite3.connect(backup/'graph.sqlite') as target:c.backup(target)
 finally:c.close()
 shutil.copy2(KB/'manifest.json',backup/'manifest.json');write(backup/'plan.json',dict(base_graph_version=base,changes=changes,proof='stage-h-annotation-split-verification.json'))
 c=sqlite3.connect(KB/'graph.sqlite');c.row_factory=sqlite3.Row
 try:
  c.execute('begin immediate');assert json.loads(c.execute("select value from metadata where key='graph_version'").fetchone()[0])==base
  for r in changes:
   assert c.execute('select review_note from claims where id=?',(r['id'],)).fetchone()[0]==r['before_review_note'];c.execute('update claims set review_note=? where id=?',(r['after_review_note'],r['id']))
   checks=dict(review_type='stale_context_caveat_correction',claim_text_conditions_evidence_unchanged=True,proof_graph_version=base,complete_question_context_verified=True)
   rid='review-'+hashlib.sha256((r['id']+j(checks)).encode()).hexdigest()[:16]
   c.execute('insert into reviews values(?,?,?,?,?,?,?)',(rid,r['id'],'Codex 主代理 / 第54课完整问题上下文专项核对',now.isoformat(),j(checks),'reviewed','现有接口已包含完整编号问题；只纠正旧review_note中工具缺口描述，不改变作者短答/问题条件/出处。'))
  for t,rows in unchanged.items():assert [tuple(r) for r in c.execute(f'select * from {t} order by id')]==rows
  allowed={r['id']:r for r in changes}
  for id,row in before_claims.items():
   after=dict(c.execute('select * from claims where id=?',(id,)).fetchone());expected=dict(row)
   if id in allowed:expected['review_note']=allowed[id]['after_review_note']
   assert after==expected
  version=refresh_version(c);counts={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']};c.commit()
 except Exception:c.rollback();raise
 finally:c.close()
 report=dict(stage='H-context-caveat-correction',base_graph_version=base,graph_version=version,backup_directory=str(backup),changes=changes,proof_file='stage-h-annotation-split-verification.json',proof='现有evidence的三条编号短答均返回所需全部PDF408/409问题段；未修改任何查询代码。',claim_text_conditions_exceptions_and_all_evidence_unchanged=True,all_source_rows_unchanged=True,counts=counts,delivery_scope='shared_knowledge_base_only',**{'pass':True})
 write(AUDIT/'stage-h-l054-context-notes-amended.json',report)
 manifest=read(KB/'manifest.json');manifest.update(graph_version=version,counts=counts,updated_at=now.isoformat());write(KB/'manifest.next.json',manifest);(KB/'manifest.next.json').replace(KB/'manifest.json');print(j(dict(graph_version=version,review_notes_corrected=2,evidence_changed=0,query_code_changed=False)))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
