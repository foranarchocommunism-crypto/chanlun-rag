"""Materialize the primary agent's early-pilot completion; source DB is read-only."""
import hashlib, json, re, sqlite3, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
OUT = Path(__file__).resolve().parent
AUDIT = AGENT / 'curation/source-audit'
BASE = 'c_stage_l062_l063'
VERSION = '0.1.0-review-a837c6e53243'
DOC = 'volume_2-5332cd1b6038'
PDF_SHA = '5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
REVIEWER = 'Codex 主代理 / 早期试点62至63课逐段与原图复核'
def j(v): return json.dumps(v, ensure_ascii=False, separators=(',', ':'))
def sha(v): return hashlib.sha256(v).hexdigest()
db = sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro', uri=True)
db.row_factory = sqlite3.Row
meta = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert meta['graph_version'] == VERSION and meta['schema_version'] == '1.1.0'
assert sha((KB/'sources/volume_2.pdf').read_bytes()) == PDF_SHA
ps = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id IN ('lesson-062','lesson-063') ORDER BY pdf_page,block_index,id")}
assert Counter(p['unit_id'] for p in ps.values()) == {'lesson-062':11, 'lesson-063':22}
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
old_e = [dict(r) for r in db.execute("SELECT e.* FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'")]
labels = {r['id']: r['label'] for r in db.execute('SELECT * FROM concepts')}
canonical = {a:r['label'] for r in db.execute('SELECT * FROM concepts') for a in [r['label']]+json.loads(r['aliases'])}
figs = [dict(r) for r in db.execute("SELECT * FROM figures WHERE document_id=? AND pdf_page IN(6,7,9,11) ORDER BY pdf_page,id",(DOC,))]
assert len(figs)==6
def pid(s):
 p,b=s.split('-',1);return f'{DOC}-p{int(p):04d}-{b}'
def fid(s): return f'{DOC}-{s}'
notes, rows, issues = {}, [], []
retained = defaultdict(list)
for e in old_e:
 if e['passage_id'] in ps: retained[e['passage_id']].append(e['claim_id'])
for k,v in retained.items():retained[k]=sorted(set(v))

def note(shorts, category, reading, reverse):
 for s in shorts.split():
  assert pid(s) in ps
  notes[pid(s)]=dict(category=category,reading=reading,reverse=reverse)
def issue(lesson,slug,shorts,description,action,blocker=False):
 issues.append(dict(id=f'lower-l{lesson:03d}-c-stage-pending-{slug}',lesson_numbers=[lesson],status='pending',passage_ids=[pid(s) for s in shorts.split()],description=description,suggested_action=action,blocks_full_semantic_extraction_completion=blocker,reviewer=REVIEWER))
def c(lesson,slug,shorts,text,concepts,level,check,conditions=(),exceptions=(),figures=(),quotes=None):
 cid=f'lower-l{lesson:03d}-c-stage-{slug}'
 assert cid not in old and cid not in {r['id'] for r in rows}
 ev=[]
 for i,s in enumerate(shorts.split()):
  p=ps[pid(s)];q=(quotes or {}).get(s,p['text'])
  assert p['unit_id']==f'lesson-{lesson:03d}' and p['speaker']=='缠中说禅' and p['role'] in ('author_body','author_commentary','author_reply')
  ev.append(dict(passage_id=p['id'],quote=q,quote_start=p['text'].index(q),figure_ids=[fid(f) for f in figures] if i==0 else []))
 reasons={1:'基础核心：定义及不能省略的条件。',2:'主要方法：影响识别与操作选择。',3:'补充深化：方法的适用边界。',4:'背景细节：作者历史判断或经验自述。'}
 context='；'.join(f"PDF{ps[e['passage_id']]['pdf_page']} {ps[e['passage_id']]['role']} {ps[e['passage_id']]['published_at']}" for e in ev)
 row=dict(id=cid,text=text,kind='explicit',conditions=list(conditions),exceptions=list(exceptions),concepts=list(dict.fromkeys(canonical.get(x,x) for x in concepts.split('|'))),ambiguity_status='none',review_note=f'语境：第{lesson}课；{context}。适用条件：'+('；'.join(conditions) or '本条所述对象、时点和原段语境')+'。'+check+'。本次先完整通读33段及6至12页，再分解条件、对照既有19命题与6整图、回查引文和反例；同一主代理复核，不称独立复核。固定汇编未核原博客。',reviewer=REVIEWER,importance_level=level,importance_reason=reasons[level]+check,evidence=ev,relations=[])
 if figures:row['figure_review_note']='实际查看6至12页及六张整图；'+ '；'.join(f['note'] for f in figs if f['id'] in ev[0]['figure_ids'])+'。后加或原发未核图只作定位/对照，文字独立支持命题。'
 rows.append(row)
 return cid

figure_notes={
 'p0006-fig1':('later_annotation','后加彩色解释图；图内署名FHSL 20080727，晚于62课2007-06-30；新添a至g及完整笔标注属于第三方解释，不能替代正文图3至5与结合律条件。实际整图查看。'),
 'p0006-fig2':('unverified','实际查看黑白图1至9：1顶/2底，3共用K，4顶底间无独立K，5有独立K，6包含，7四类非包含三K，8基本线段，9线段破坏基本形式。正文逐号援引，但汇编位图与原博客一致性/原始绘制者未核；图8/9不是完整线段算法。'),
 'p0007-fig1':('later_annotation','实际整图查看：陈仁制作，水印2009-10-12 0:31:56及同日另时分，晚于62课；分型/方向/多K包含公式为后加说明，不能据图新增作者原文未写的算法。延续上一来源复核纠正的日期。'),
 'p0009-fig1':('later_annotation','实际整图查看，红题署名alon、含密集文字与多色分解/中枢；编号延伸至120，超出63课7月2日110/111讨论。第三方后加整理图，具体制作日期未核，不作当时作者预知路径或对所有图注认可的证据。'),
 'p0011-fig1':('unverified','实际整图查看：1分钟上证图编号97至111，110为小顶、111低点标3724.19；MACD(12,26,9)下有两红箭头比较绿柱面积。左上光标06271000不等全图截止时间；右端横轴已至7月2日。与7月2日解盘文字对应，位图原发及绘制者未核。'),
 'p0011-fig2':('later_annotation','实际整图查看：1分钟上证重绘图，110/111、111低点标3724.35，内嵌7月2日15:32:58引文框及另一MACD指标；是后加整理版，制作者/日期未核。不能将3724.35静合原图3724.19，亦不能把红框注释自动当作者原图证言。'),
}
operations=[]
for f in figs:
 status,n=figure_notes[f['id'].split(DOC+'-')[1]]
 after=dict(origin_status=status,note=n)
 operations.append(dict(table='figures',id=f['id'],before={k:f[k] for k in after},after=after,reason='本次主代理实际原页/整图查看；来源状态与图意分开'))
 f.update(after)
 # Rendering is reproducible from the fixed PDF and stored bbox.
 image_path=OUT/f'{BASE}.visual'/f"{f['id'].split(DOC+'-')[1]}.png"
 f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=n,render_sha256=sha(image_path.read_bytes()),source_pdf_sha256=PDF_SHA,lesson_number=62 if f['pdf_page']<=7 else 63)

c(62,'figure8-basic-segment-figure9-one-two-segment-combination','7-b004','第62课以图8示线段的基本形态，以图9示线段破坏，并明确图9只是两线段组合的其中一种形态。','线段|线段破坏',2,'只记录作者对示意图的指称；至少三笔是必要条件，图中折线不构成任意三笔充分成段或完整结束判据；后续严格定义仍需联读。',figures=['p0006-fig2'],quotes={'7-b004':ps[pid('7-b004')]['text'].split('有人可能要说',1)[0]})
c(63,'ideal-operability-not-practical-per-trade-reconstruction','8-b004','作者区分理想化、数学化的可操作性与实际操作的便利；逐笔从最原始成交定义、寻找中枢和走势类型不便，因而需要不同周期图形的变通研究。','走势中枢|走势类型|成交分笔|周期K线图',2,'质因数分解只是作者类比，不把不能完成之强语当本项目计算复杂度结论；不称周期图改变对象定义。')
c(63,'one-decomposition-remember-only-last-unfinished-one-minute-type','8-b007 9-b000','把已经完成的走势类型标到较大周期图后，在一种分解的角度，1分钟图上只需记住最近一个未完成的1分钟走势类型；分解多样时实际需要知道更多。','分解多样性|完成|走势分解|周期K线图',1,'完成后上移标记与一种分解两个前提同时保留，不宣称所有分解只需一个未完对象或只留一条历史。',conditions=['已完成的走势类型已在较大周期图相应记号','只站在一种分解的角度'],exceptions=['分解的多样性使实际需要知道的内容更多'])
c(63,'mark-child-for-intuition-other-level-marks-personal-choice','9-b001','在大周期图标次级别走势能直观看清该级别中枢和走势类型的形成；5分钟图也可标30分钟乃至年线走势，这是个人记号选择。','周期K线图|次级别|走势类型|走势中枢',2,'图周期不必等于标注对象级别；不把5分钟必须标5分钟、或无需任何记忆分析能力即可完全不标当规则。')
c(63,'coarse-overview-then-fine-observation-fractals-all-periods','9-b002','观察一只股票可先从日、周、月、季、年图粗看，再换更细周期精察；分型、笔、线段在大周期图同样可用，粗看通常不逐步精分。','周期K线图|分型|笔|线段',2,'概略选股与严格逐段分解不同任务；1秒看懂及一见钟情是作者熟练直觉修辞，不作耗时指标或心理学实证。')
c(63,'center-oscillation-profit-not-necessarily-less-same-level-oneway-up','10-b001','作者在纯理论角度指出，中枢震荡股票产生的利润不一定少于相应级别单边上涨的股票。','中枢震荡|上涨|利润率|操作级别',3,'保纯理论、不一定、相应级别；这是作者方法论判断，无账户绩效比较，不推出所有震荡盈利更多或无交易成本。')
c(63,'small-capital-choose-good-character-large-capital-change-cost','10-b002','作者要求小资金选择股性好的股票；对于大资金，他认为股性可改造，但改造代价和所需能量不同。','股性|交易容量|资金管理',2,'大小资金条件和不同代价同时保留；任何股都可改造为作者强说法，不作任意账户可控盘或可盈利承诺。')
c(63,'july2-110-small-top111-small-bottom-divergence-case','10-b005','在7月2日解盘例中，作者把110点称为线段里的小顶背驰，把111点称为小底背驰。','背驰|线段|确认',2,'历史具体编号与线段内部尺度保留；不将110/111泛作所有同编号点或独立完整1分钟走势的顶底背驰。',figures=['p0011-fig1','p0011-fig2'])
c(63,'111-green-macd-area-comparison-not-previous-arrow-proof','10-b005','作者要求看不懂111小底背驰者比较MACD中两红箭头所指的绿柱面积；对为何此前不算及箭头处笔、底分型的组成，要求回看62、63课自行研究。','MACD柱波|背驰|笔|底分型',1,'本段给面积比较与学习任务，未逐K完整解答为什么前面不是；不能把后加图框或只见一根缩柱当全部结构已证。',figures=['p0011-fig1','p0011-fig2'])
c(63,'july2-107-stand-atleast-center-oscillation-conditional','10-b006 11-b000','7月2日例中，作者说若能站稳图中107点，则至少该中枢震荡有保证；具体中枢划分本段留给读者按递归定义练习。','确认|中枢震荡|走势中枢',1,'若站稳与至少保留；原段未给完整中枢区间和分解答案，不由107单价推已成趋势或擅造三类买点。',conditions=['7月2日所述图例','能站稳107这一点'],figures=['p0011-fig1'])
c(63,'july2-3919-first-pressure-neckline-then-fiveweek-average','11-b000','7月2日作者仍以3919为第一压力，并称它此时相当于颈线位置，再上面是5周均线。','经验压力线|均线系统|确认',2,'历史时点3919与107及5周均线各有角色；未写有效突破定义，不把碰价当站稳或普适数值。')
c(63,'july2-five-month-average-support-triangle-platform-watch-effective-break','11-b000','7月2日作者把当日反弹归于5月均线支持，并以该线是否有效跌破判断三角形或平台型的后续选择。','均线系统|三角形整理|平台式调整|确认',2,'保原5月均线而非改5日，与同段5周压力不同；为历史观察和条件前瞻，不据本段补未明说的突破阈值或已完成形态。')
c(63,'novice-oscillation-watch-half-flat-or-small-practice','11-b001','在该震荡行情，作者建议没有基础者最好观望，半仓或空仓均可；若要学习练习，可以只用少量资金。','中枢震荡|仓位|操作熟练程度',1,'限缺乏基础者和该震荡语境，保可以和最好，不把半仓当统一最优比例或强制参与。')
c(63,'novice-oscillation-rather-sell-early-than-late','12-b000','作者对初学者给出震荡操作原则：宁愿卖早，也不卖晚。','中枢震荡|操作节奏|卖点|操作熟练程度',2,'初学者与震荡两个范围保留；非成交保证或舍弃所有买卖点规则，也不证明任何提前卖出均优于持有。')
c(63,'novice-avoid-authors-volatile-holdings-prefer-milder-stock','12-b001','在自述其持股以零成本赚筹码的背景下，作者劝技术或承受能力不足者不要参与其波动较大的持股，应找股性温和些的股票。','股性|操作熟练程度|仓位',2,'零成本与持股波动为作者自述，未核账户，不变成推荐名单或所有投资者零成本保证；对谁避免参与的条件不能删。')

relations={
 'lower-l062-c-stage-figure8-basic-segment-figure9-one-two-segment-combination':[('线段破坏','线段','qualifies')],
 'lower-l063-c-stage-one-decomposition-remember-only-last-unfinished-one-minute-type':[('走势分解','分解多样性','qualifies')],
 'lower-l063-c-stage-mark-child-for-intuition-other-level-marks-personal-choice':[('周期K线图','次级别','qualifies')],
 'lower-l063-c-stage-small-capital-choose-good-character-large-capital-change-cost':[('股性','交易容量','qualifies')],
 'lower-l063-c-stage-novice-oscillation-watch-half-flat-or-small-practice':[('仓位','操作熟练程度','qualifies')],
}
for r in rows:r['relations']=[dict(source=a,target=b,type=t) for a,b,t in relations.get(r['id'],[])]
note('6-b000 8-b001 10-b004','source_header','课程/解盘标题及记载时间已核。','标题只作来源定位。')
note('6-b001 8-b002 10-b003','personal_context','旅行、住宿、饮食、音乐及作息背景完整阅读。','保源文，不作技术命题或行程外部核实。')
note('6-b002','author_theory_self_assessment','作者称石猴解释不够严密，并以几何为理论有效性自评。','未认可读者全部解释；自称几何有效不作为本项目数学证明。')
note('6-b003 6-b004 7-b000 7-b001 7-b002 7-b003','existing_claim_retained','既有12条已复核定义覆盖周期、高低双条件、顶底称谓、相邻笔/独立K、至少三笔、包含方向及四类和组合。','旧陈述、量词、条件、例外、引文、偏移、坐标全部保留；只将8个空图关联补到正文所引黑白图。顶和低原字不修；至少三笔非充分，图4最好与实际必须分开。')
note('7-b004 8-b000','author_theory_self_assessment','图8/9指称已单列；余下推导所有图形理论/波浪理论的强语保留为作者自评。','无完整推导不能作为本项目已证完备性或他理论错误的证明。')
note('8-b003 8-b005 8-b006','existing_claim_retained','旧7条中关于递归存在性、图周期不是中枢级别、基础图选择及递归链的命题保留。','一般能得1分钟为2007时点背景，不当当下行情软件上限；递归存在性是作者理论解释，图/物分开。')
note('8-b004','practical_operability_boundary','理想数学定义可操作与实际逐笔计算便利性的差异已单列。','质因数分解为作者类比，不据此推出一般计算复杂性结论；变通图形研究不替换递归定义。')
note('8-b007 9-b000 9-b001','existing_claim_retained','旧已完成走势标到大周期图/大周期MACD便利命题保留，另补一种分解、未完成和记号选择条件。','不把软件MACD参数上限删成随意可精确等价，不造参数倍乘公式或把图周期等于中枢级别。')
note('9-b002 9-b003 10-b000','teaching_rhetoric','先粗后细技术已取；性、419与直觉等类比完整读过。','不把修辞或所谓科学研究1秒升为本项目心理/生理实证。')
note('10-b001 10-b002','existing_claim_retained','旧选适合自身操作级别买点并按该级别操作命题保留；补震荡相对收益及资金/股性边界。','原只有坏操作者/股票废纸及可改造任何股票是强修辞，不作风险或绩效保证。')
note('10-b005 10-b006 11-b000','historical_case','7月2日图例、绿色柱面积比较、107条件及3919/5周/原5月分层补录。','作者留的笔/分型与具体中枢练习未被本段完整回答；不借后加整理图替作者答题，不伪造完整区间。')
note('11-b001 12-b000 12-b001','operation_scope','初学者震荡可观望/小资金练习、卖早与温和股性等条件补录。','0成本持仓仅自述，无账户成交核实。')

issue(62,'figure-origin-and-early-segment-definition','6-b003 7-b001 7-b004','六十二课黑白图8/9仅基本形态；至少三笔不是充分定义，两彩色图为后加。','严密线段划分需联读65/67/71/72/81，不把图9某一种形态当全部算法；原博客/位图作者未核。')
issue(63,'110-111-pen-fractal-and-center-homework-not-fully-given','10-b005 10-b006 11-b000','作者要求研究箭头处笔和底分型，并留下具体递归中枢练习；本段没有逐K答案。','64课后续110/111讲解另设来源联读，不能以匿名整理图作作者答案；原111价3724.19与后加3724.35分开。',True)
issue(63,'historical-execution-precision-and-strong-profit-claims','10-b001 10-b002 11-b000 12-b001','相对利润/任意股性可改造/0成本自述及107站稳、3919/5周/5月为历史有条件陈述。','未核外部行情/交易绩效及有效站稳阈值，忠实保存作者语境，不作当前投资建议或统一保证。')

# Figure associations are an explicit, narrowly permitted amendment, not a reimport
# of early reviewed records (which would regenerate their evidence identities).
amendments=[]
for e in old_e:
 if e['claim_id'].startswith('lower-l062-') and e['passage_id'] in ps and not json.loads(e['figure_ids']):
  amendments.append(dict(evidence_id=e['id'],claim_id=e['claim_id'],before_figure_ids=[],after_figure_ids=[fid('p0006-fig2')],reason='正文所引黑白图1至9已实际复核；旧证据ID/原引文/偏移/源坐标不变'))
assert len(amendments)==8
ledger=[]
for id,p in ps.items():
 linked=[r for r in rows if any(e['passage_id']==id for e in r['evidence'])]
 assert id in notes,(id,p['text'])
 n=notes[id]
 ledger.append(dict(passage_id=id,lesson_number=int(p['unit_id'][-3:]),document_id=DOC,pdf_page=p['pdf_page'],role=p['role'],speaker=p['speaker'],published_at=p['published_at'],source_text_sha256=sha(p['text'].encode()),result='new_claim' if linked else n['category'],claim_ids=[r['id'] for r in linked],related_existing_claim_ids=retained[id],existing_semantics_and_quote_geometry_not_mutated=True,figure_link_amendments=[x['evidence_id'] for x in amendments if x['evidence_id'] in {e['id'] for e in old_e if e['passage_id']==id}],pending_issue_ids=[x['id'] for x in issues if id in x['passage_ids']],reviewer=REVIEWER,rounds={'1_read_and_scope':n['reading'],'2_atomic_conditions':[dict(claim_id=r['id'],conditions=r['conditions'],exceptions=r['exceptions']) for r in linked],'3_normalization':{'concept_labels':sorted({v for r in linked for v in r['concepts']}),'related_existing_claim_ids':retained[id]},'4_reverse_check':n['reverse']+'；'+'；'.join(r['review_note'] for r in linked)}))
for f in figs:
 f['linked_new_claim_ids']=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])]
 f['linked_existing_claim_ids']=sorted({e['claim_id'] for e in old_e if f['id'] in json.loads(e['figure_ids'])}|{a['claim_id'] for a in amendments if f['id'] in a['after_figure_ids']})
summary=dict(stage='H early pilot completion',schema_version=meta['schema_version'],graph_version=VERSION,lessons=[62,63],document_id=DOC,reviewer=REVIEWER,claims=len(rows),evidence=sum(len(r['evidence']) for r in rows),passages_read=len(ledger),existing_reviewed_claims_retained=19,existing_evidence_figure_links_added=len(amendments),source_passages_snapshot_sha256=sha(j(sorted(ps.values(),key=lambda p:p['id'])).encode()),whole_lesson_semantic_read_complete=True,technical_extraction_complete=False,four_round_review=True,independent_review_claimed=False,visual_pdf_pages=list(range(6,13)),figure_objects_viewed=6,figure_origin_counts=dict(Counter(f['origin_status'] for f in figs)),pending=[i['id'] for i in issues],new_concepts=sorted({v for r in rows for v in r['concepts']}-set(labels.values())),database_mode='ro',formal_import=False,delivery_scope='shared_knowledge_base_only')
for suffix,data in [('reviewed.jsonl',rows),('coverage.jsonl',ledger),('pending.jsonl',issues),('figures.jsonl',figs)]:
 target=OUT/f'{BASE}.{suffix}';assert not target.exists(),target
 target.write_text(''.join(j(r)+'\n' for r in data),encoding='utf-8')
target=OUT/f'{BASE}.summary.json';assert not target.exists();target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plan=dict(base_graph_version=VERSION,source_pdf_sha256=PDF_SHA,reviewer=REVIEWER,figure_operations=operations,evidence_figure_amendments=amendments,passage_texts_roles_maps_geometry_changes=[],existing_claim_semantic_changes=[],source_passages_snapshot_sha256=summary['source_passages_snapshot_sha256'])
target=AUDIT/'stage-h-l062-l063-amendment-plan.json';assert not target.exists();target.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
