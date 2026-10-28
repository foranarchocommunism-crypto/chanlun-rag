"""Fill ten master-log omissions after actual page/figure inspection; no DB writes."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
def j(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return [json.loads(l) for l in p.read_text(encoding='utf-8-sig').splitlines() if l.strip()]
def main():
 before=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json'));db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 try:
  version=json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0]);assert version=='0.1.0-review-307029129712'
  figures={r['id']:dict(r) for r in db.execute('SELECT * FROM figures')};seen={}
  for directory in ['upper','lower']:
   for r in load(AGENT/f'curation/{directory}/figure_reviews.jsonl'):
    id=r.get('id',r.get('figure_id'))
    if id:seen[id]=r
  missing=sorted(set(figures)-set(seen));assert len(missing)==10
  descriptions={
   'volume_1-a53e99c37ca5-p0001-fig1':'实际查看封面竹叶装饰图；不承载作者技术定义或行情判断，不用作命题证据，装饰制作人/原发未核。',
   'volume_2-5332cd1b6038-p0001-fig1':'实际查看下册封面竹叶装饰图；不承载作者技术判断，不用作命题证据，装饰制作人/原发未核。',
   'p0050-fig1':'实际查看向上笔开始的S/X序列，分别示X笔之间有/无重合；是特征序列文字的示意，不以红色绘制风格证明原始作者身份。',
   'p0050-fig4':'实际查看向下笔开始的反向S/X序列，S向上笔之间有/无重合两图；不把S序列与向上段的X序列互换，图原发未核。',
   'p0050-fig2':'实际查看黑白情况1/情况2转化图，并见“顶分型后的新特征序列”；只作正文两种精确情况的导航，不用简图替代完整联合条件。',
   'p0050-fig3':'实际查看黑白不构成顶分型例图及右端标注；不把视觉折返一律当标准特征序列顶分型，原始绘制者未核。',
   'p0051-fig1':'实际查看第一种情况红绿顶/底分型两图，元素1与2有重合无缺口；有网站水印但无可核日期，不能自动认证作者或仅因彩色归后加。',
   'p0051-fig2':'实际查看第二种情况图1/图2，元素1与2间有缺口，随后反向序列出相反分型；保正文后一序列不一定封闭缺口、只需分型，不从图造额外补缺口条件。',
   'p0055-fig1':'本次重新实际查看1分钟上证图1至5，低3标4285.02、前高4501.22；MACD(12,26,9)中红绿箭头指黄白线或绿柱面积。旧67批已有实际图审说明，但汇总日志漏记；只确认作者所说比较用途，不认定图上所有点必可成交。原位图/制作者未核。',
   'p0058-fig1':'实际查看8月3日附文1分钟图延伸至6/7及右端4561，3仍4285.02，多处红绿MACD箭头；左上08011318为光标而非全图截止。图原发未核，保解盘语境，不将未给逐笔确认过程当成交证明。',
  }
  assert set(missing)=={k if k.startswith('volume_') else 'volume_2-5332cd1b6038-'+k for k in descriptions}
  links={id:[] for id in figures}
  for r in db.execute("SELECT e.claim_id,e.figure_ids FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'"):
   for id in json.loads(r['figure_ids']):links[id].append(r['claim_id'])
  records=[]
  for id in missing:
   f=figures[id];suffix=id.split(f['document_id']+'-')[1];n=descriptions.get(id,descriptions.get(suffix));assert n
   prefix='volume_1' if f['document_id'].startswith('volume_1') else 'volume_2'
   image=AGENT/'build/final-figure-audit'/('p0055-fig1.png' if suffix=='p0055-fig1' else prefix+'-'+suffix+'.png');assert image.is_file()
   same_page=[r[0] for r in db.execute("SELECT DISTINCT e.claim_id FROM evidence e JOIN claims c ON c.id=e.claim_id JOIN passages p ON p.id=e.passage_id WHERE c.review_status='reviewed' AND p.document_id=? AND p.pdf_page=?",(f['document_id'],f['pdf_page']))]
   records.append(dict(**f,reviewer='Codex 主代理 / 最终图审日志对账与漏记补录',visual_review_complete=True,visual_review_note=n,graph_version=version,logged_at=datetime.now(timezone.utc).isoformat(),render_sha256=sha(image),linked_claim_ids=sorted(set(links[id])),same_page_claim_ids_for_navigation_only=same_page,same_page_is_evidence_support=False,source_authorship_confirmed=False,old_review_proof='curation/lower/batch_004_l067_full_review.jsonl#lower-l067-chart-arrows-comparison' if suffix=='p0055-fig1' else None))
 finally:db.close()
 out=AUDIT/'stage-h-final-figure-log-completion.jsonl';assert not out.exists();out.write_text(''.join(j(r)+'\n' for r in records),encoding='utf-8')
 for directory in ['upper','lower']:
  selected=[r for r in records if r['document_id'].startswith('volume_1' if directory=='upper' else 'volume_2')]
  with (AGENT/f'curation/{directory}/figure_reviews.jsonl').open('a',encoding='utf-8') as f:
   for r in selected:f.write(j(r)+'\n')
  for r in selected:seen[r['id']]=r
 assert set(seen)==set(figures) and all(id in seen for id,v in links.items() if v)
 assert dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json'))==before
 legacy=[id for id,r in seen.items() if not r.get('visual_review_complete')]
 assert all(any(s in (seen[id].get('note','')+' '+seen[id].get('review_method','')) for s in ['已查看','实际查看','复看']) for id in legacy)
 report=dict(graph_version=version,records_added=10,figures_with_viewing_records=528,reviewed_evidence_linked_figures=sum(bool(v) for v in links.values()),linked_figures_without_viewing_record=[],legacy_field_variants_with_explicit_viewing_notes=len(legacy),source_authorship_confirmed_by_this_step=False,database_and_manifest_unchanged=True,final_sha256=before,**{'pass':True})
 (AUDIT/'stage-h-final-figure-log-completion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(j(report))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8');main()
