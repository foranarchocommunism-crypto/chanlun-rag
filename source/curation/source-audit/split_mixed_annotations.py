"""One-off reviewed source segmentation, with explicit evidence migration.

Default writes a reviewable plan only. --apply consumes that exact plan.
PDFs, pages and geometry stay unchanged; anonymous notes get role=unknown.
"""
import argparse,gzip,hashlib,json,shutil,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
sys.path.insert(0,str(AGENT/'tools'))
from graph_release import refresh_version
BASE='0.1.0-review-135f4fcad3e3'
def j(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def sha(x):return hashlib.sha256(x).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ro():
 c=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;return c
def geometry(c,p):
 path=c.execute('select geometry_path from pages where document_id=? and pdf_page=?',(p['document_id'],p['pdf_page'])).fetchone()[0]
 return json.loads(gzip.decompress((KB/path).read_bytes()))['chars']
def coords(chars,indices):
 boxes=[];raw=[];last=None
 for i in dict.fromkeys(indices):
  ch,x0,top,x1,bottom=chars[i]
  if last is None or abs(top-last)>3:
   if raw:raw.append('\n')
   boxes.append([x0,top,x1,bottom]);last=top
  else:
   b=boxes[-1];b[:]=[min(b[0],x0),min(b[1],top),max(b[2],x1),max(b[3],bottom)]
  raw.append(ch)
 return boxes,''.join(raw)
def build():
 c=ro()
 try:
  meta={r['key']:json.loads(r['value']) for r in c.execute('select * from metadata')};assert meta['graph_version']==BASE
  specs=[('volume_1-a53e99c37ca5-p0316-b004','（注：禅师的意思为进行式非完成式）'),('volume_1-a53e99c37ca5-p0432-b001','（备注：从0206的2541开始算，一般30分中枢大致相当于日线笔中枢、月线3k重合中枢，对应的是月线的5均线）')]
  items=[]
  for pid,note in specs:
   p=dict(c.execute('select * from passages where id=?',(pid,)).fetchone());assert p['text'].count(note)==1
   begin=p['text'].index(note);end=begin+len(note);mapping=json.loads(p['normalized_map']);chars=geometry(c,p)
   ranges=[(0,begin,'author_prefix'),(begin,end,'unknown_annotation')]+([(end,len(p['text']),'author_suffix')] if end<len(p['text']) else [])
   parts=[]
   for n,(a,b,kind) in enumerate(ranges):
    q=dict(p);q['id']=pid if n==0 else pid+f'-s{n:02d}';q['block_index']=p['block_index']+n
    assert not c.execute('select 1 from passages where id=?',(q['id'],)).fetchone() or n==0
    selected=mapping[a:b];boxes,raw=coords(chars,selected);q.update(text=p['text'][a:b],raw_text=raw,boxes=j(boxes),normalized_map=j(selected),source_char_indices=j(list(dict.fromkeys(selected))))
    if kind=='unknown_annotation':q.update(role='unknown',speaker=None,published_at=None)
    assert ''.join(chars[i][0] for i in selected)==q['text'];parts.append(dict(kind=kind,original_begin=a,original_end=b,after=q))
   assert ''.join(x['after']['text'] for x in parts)==p['text'] and sum([json.loads(x['after']['normalized_map']) for x in parts],[])==mapping
   refs=[dict(r) for r in c.execute('select * from evidence where passage_id=? order by id',(pid,))];migrations=[]
   for e in refs:
    status=c.execute('select review_status from claims where id=?',(e['claim_id'],)).fetchone()[0]
    hits=[s for s in parts if s['original_begin']<=e['quote_start'] and e['quote_end']<=s['original_end']]
    if len(hits)==1:
     s=hits[0];assert s['kind']!='unknown_annotation' or status!='reviewed'
     new=dict(e);new.update(passage_id=s['after']['id'],quote_start=e['quote_start']-s['original_begin'],quote_end=e['quote_end']-s['original_begin'])
     assert s['after']['text'][new['quote_start']:new['quote_end']]==e['quote'];migrations.append(dict(before=e,after=[new],claim_status=status,action='retain_author_quote_and_coordinates'))
    else:
     assert status=='pending' and e['quote_start']==0 and e['quote_end']==len(p['text'])
     new=[]
     for n,s in enumerate(parts):
      q=s['after'];nm=json.loads(q['normalized_map']);boxes,_=coords(chars,nm)
      new.append(dict(e,id=e['id'] if n==0 else 'evidence-'+sha((e['id']+':split:'+q['id']).encode())[:16],passage_id=q['id'],quote=q['text'],quote_start=0,quote_end=len(q['text']),source_spans=j([dict(document_id=p['document_id'],pdf_page=p['pdf_page'],char_indices=nm,boxes=boxes,coordinate_system='pdf_points_top_left')]),figure_ids='[]'))
     migrations.append(dict(before=e,after=new,claim_status=status,action='reject_mixed_candidate_preserve_all_source_parts'))
   items.append(dict(before=p,parts=parts,evidence_migrations=migrations))
  return dict(format='source-annotation-split-v1',base_graph_version=BASE,schema_version=meta['schema_version'],visual_review=dict(pdf='volume_1.pdf',pages=[316,432],reviewer='Codex 主代理，实际查看整页，未知夹注不归作者'),items=items,expected_added_passages=3,expected_added_evidence=2,expected_reviewed_evidence_relocated=1,expected_rejected_candidates=['candidate-ce7b8fbb2d590dfe'],limits=['只修两处确证混合夹注，不宣称全书所有身份已通过最终审计。','原始完整passage行和依赖evidence保存于本计划、备份及知识包provenance；作者命题语义/引文/源字符坐标不改，尾句只迁移段ID/段内偏移。'])
 finally:c.close()
def apply(plan):
 assert plan==build(),'计划或当前来源变化'
 now=datetime.now(timezone.utc);backup=KB.parent/'backups'/(now.strftime('%Y%m%dT%H%M%S%fZ')+'-annotation-split');backup.mkdir(parents=True,exist_ok=False)
 c=ro()
 try:
  old_claims={r['id']:dict(r) for r in c.execute("select * from claims where review_status='reviewed'")};old_evidence={r['id']:dict(r) for r in c.execute("select e.* from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'")}
  old_source={t:{r['id']:dict(r) for r in c.execute(f'select * from {t}')} for t in ['documents','pages','figures','passages']}
  with sqlite3.connect(backup/'graph.sqlite') as target:c.backup(target)
 finally:c.close()
 shutil.copy2(KB/'manifest.json',backup/'manifest.json');write(backup/'plan.json',plan)
 c=sqlite3.connect(KB/'graph.sqlite');c.row_factory=sqlite3.Row;moved=[];rejected=[];newids=[]
 try:
  c.execute('pragma foreign_keys=on');c.execute('begin immediate');assert json.loads(c.execute("select value from metadata where key='graph_version'").fetchone()[0])==BASE
  for item in plan['items']:
   for n,part in enumerate(item['parts']):
    q=part['after']
    if n==0:c.execute('update passages set '+','.join(k+'=?' for k in q if k!='id')+' where id=?',tuple(v for k,v in q.items() if k!='id')+(q['id'],))
    else:c.execute('insert into passages('+','.join(q)+') values('+','.join('?' for _ in q)+')',tuple(q.values()));newids.append(q['id'])
   for migration in item['evidence_migrations']:
    old=migration['before']
    for n,e in enumerate(migration['after']):
     if n==0:c.execute('update evidence set '+','.join(k+'=?' for k in e if k!='id')+' where id=?',tuple(v for k,v in e.items() if k!='id')+(e['id'],))
     else:c.execute('insert into evidence('+','.join(e)+') values('+','.join('?' for _ in e)+')',tuple(e.values()))
    if migration['claim_status']=='pending':
     assert migration['action']=='reject_mixed_candidate_preserve_all_source_parts'
     c.execute("update claims set review_status='rejected',ambiguity_status='mixed_annotation_source_rejected',review_note=? where id=?",('原技术词召回候选混含未知注释，不能整体作为作者命题；保原claim文本和按来源分拆证据，原完整引文另保provenance。',old['claim_id']));rejected.append(old['claim_id'])
    elif migration['after'][0]!=old:moved.append(old['id'])
    checks=dict(review_type='source_annotation_segmentation',semantic_claim_changed=False,source_geometry_changed=False,old_passage_id=item['before']['id'],evidence_id=old['id'],new_passage_ids=[e['passage_id'] for e in migration['after']],base_graph_version=BASE)
    rid='review-'+sha((old['claim_id']+j(checks)).encode())[:16]
    c.execute('insert into reviews values(?,?,?,?,?,?,?)',(rid,old['claim_id'],'Codex 主代理 / 两处混合夹注来源拆分',now.isoformat(),j(checks),'rejected' if migration['claim_status']=='pending' else 'reviewed','源身份及段内偏移专项迁移；不改变已复核作者命题/引文/原页字符坐标，旧依赖完整保provenance。'))
  for item in plan['items']:
   c.execute('delete from passage_fts where passage_id=?',(item['before']['id'],))
   for part in item['parts']:c.execute('insert into passage_fts(passage_id,text) values(?,?)',(part['after']['id'],part['after']['text']))
  assert moved==['evidence-66e71b5de52ad2a9'] and rejected==plan['expected_rejected_candidates'] and len(newids)==3
  for id,row in old_claims.items():assert dict(c.execute('select * from claims where id=?',(id,)).fetchone())==row
  for id,row in old_evidence.items():
   current=dict(c.execute('select * from evidence where id=?',(id,)).fetchone())
   if id in moved:assert {k:v for k,v in current.items() if k not in ['passage_id','quote_start','quote_end']}=={k:v for k,v in row.items() if k not in ['passage_id','quote_start','quote_end']}
   else:assert current==row
  changed_parents={i['before']['id'] for i in plan['items']}
  for t,rows in old_source.items():
   for id,row in rows.items():
    if t=='passages' and id in changed_parents:continue
    assert dict(c.execute(f'select * from {t} where id=?',(id,)).fetchone())==row
  assert not c.execute('pragma foreign_key_check').fetchall()
  assert c.execute('select count(*) from passages p left join passage_fts f on f.passage_id=p.id where f.passage_id is null or f.text!=p.text').fetchone()[0]==0
  c.execute("insert or replace into metadata values('source_segmentation_revision','1')");c.execute("insert or replace into metadata values('source_segmentation_lineage',?)",(j('provenance/source-segmentation-001.json'),))
  version=refresh_version(c);counts={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']};c.commit()
 except Exception:c.rollback();raise
 finally:c.close()
 report=dict(stage='H-source-attribution-correction',graph_version=version,schema_version=plan['schema_version'],base_graph_version=BASE,backup_directory=str(backup),lineage_file='provenance/source-segmentation-001.json',counts=counts,split_parent_ids=sorted(changed_parents),new_passage_ids=newids,reviewed_claims_unchanged=len(old_claims),reviewed_quotes_and_source_coordinates_unchanged=len(old_evidence),reviewed_evidence_relocated=moved,rejected_mixed_candidates=rejected,all_other_source_rows_unchanged=True,pages_and_geometry_unchanged=True,reviewed_semantic_approval_not_repeated=True,**{'pass':True})
 out=KB/'provenance';out.mkdir(exist_ok=True);write(out/'source-segmentation-001.json',dict(report=report,plan=plan))
 manifest=read(KB/'manifest.json');manifest.update(graph_version=version,counts=counts,source_segmentation_revision=1,source_segmentation_lineage=report['lineage_file'],updated_at=now.isoformat());write(KB/'manifest.next.json',manifest);(KB/'manifest.next.json').replace(KB/'manifest.json')
 write(AUDIT/'stage-h-annotation-split-applied.json',report);print(j(report))
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');p=argparse.ArgumentParser();p.add_argument('--apply',type=Path);args=p.parse_args()
 if args.apply:apply(read(args.apply))
 else:
  plan=build();path=AUDIT/'stage-h-annotation-split-plan.json';write(path,plan);print(j(dict(plan=str(path),base=BASE,parent_passages=2,new_passages=3,reviewed_evidence_to_relocate=1,rejected_mixed_candidates=plan['expected_rejected_candidates'])))
