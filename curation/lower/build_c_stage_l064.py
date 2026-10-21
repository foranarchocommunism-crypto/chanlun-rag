"""Finish the early pilot64 ledger from the primary agent's full source reading."""
import hashlib,json,re,sqlite3,sys
from collections import Counter,defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';OUT=Path(__file__).resolve().parent;AUDIT=AGENT/'curation/source-audit'
BASE='c_stage_l064';VERSION='0.1.0-review-2ac69fd77eec';DOC='volume_2-5332cd1b6038';PDF_SHA='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
REVIEWER='Codex 主代理 / 早期试点64课全文、附带文章答疑和原图四轮复核'
def j(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'))
def sha(v):return hashlib.sha256(v).hexdigest()
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')};assert meta['graph_version']==VERSION
assert sha((KB/'sources/volume_2.pdf').read_bytes())==PDF_SHA
ps={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id='lesson-064' ORDER BY pdf_page,block_index,id")};assert len(ps)==223
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
oe=[dict(r) for r in db.execute("SELECT e.* FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'")]
canonical={a:r['label'] for r in db.execute('SELECT * FROM concepts') for a in [r['label']]+json.loads(r['aliases'])}
canonical.update({'合力':'市场合力','分力':'市场分力'})
figs=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 12 AND 32 ORDER BY pdf_page,id',(DOC,))];assert len(figs)==5
def pid(s):
 p,b=s.split('-',1);return f'{DOC}-p{int(p):04d}-{b}'
def fid(s):return f'{DOC}-{s}'
rows,notes,pending=[],{},[];retained=defaultdict(list)
for e in oe:
 if e['passage_id'] in ps:retained[e['passage_id']].append(e['claim_id'])
for k,v in retained.items():retained[k]=sorted(set(v))
def note(shorts,category,reading,reverse):
 for s in shorts.split():assert pid(s) in ps,s;notes[pid(s)]=dict(category=category,reading=reading,reverse=reverse)
def issue(slug,shorts,text,action,blocking=False):pending.append(dict(id='lower-l064-c-stage-pending-'+slug,lesson_numbers=[64],status='pending',passage_ids=[pid(s) for s in shorts.split()],description=text,suggested_action=action,blocks_full_semantic_extraction_completion=blocking,reviewer=REVIEWER))
def c(slug,shorts,text,concepts,level,check,conditions=(),exceptions=(),figures=(),quotes=None):
 cid='lower-l064-c-stage-'+slug;assert cid not in old and cid not in {r['id'] for r in rows}
 ev=[]
 for i,s in enumerate(shorts.split()):
  p=ps[pid(s)];q=(quotes or {}).get(s,p['text']);assert p['speaker']=='缠中说禅' and p['role'] in ('author_body','author_commentary','author_reply')
  ev.append(dict(passage_id=p['id'],quote=q,quote_start=p['text'].index(q),figure_ids=[fid(f) for f in figures] if i==0 else []))
 context='；'.join(f"PDF{ps[e['passage_id']]['pdf_page']} {ps[e['passage_id']]['role']} {ps[e['passage_id']]['published_at']}" for e in ev)
 reasons={1:'基础核心：定义及不可省略的条件。',2:'主要方法：影响判断和操作选择。',3:'补充深化：方法边界与历史案例。',4:'背景细节：作者历史意见或经验自述。'}
 r=dict(id=cid,text=text,kind='explicit',conditions=list(conditions),exceptions=list(exceptions),concepts=list(dict.fromkeys(canonical.get(x,x) for x in concepts.split('|'))),ambiguity_status='none',review_note='语境：第64课及其后附各日文章/答疑；'+context+'。适用条件：'+('；'.join(conditions) or '本条指明的对象、级别、时点和原段范围')+'。'+check+'。四轮：通读223段与PDF12至32；拆分联合条件及作者/读者身份；比对既有16条及62/63/67/72；回查引文、图像和范围反例。同一主代理，不称独立/人工复核；固定汇编未核原博客。',reviewer=REVIEWER,importance_level=level,importance_reason=reasons[level]+check,evidence=ev,relations=[])
 if figures:r['figure_review_note']='实际查看PDF12至32共21页及五整图；'+ '；'.join(f['note'] for f in figs if f['id'] in ev[0]['figure_ids'])+'。原发未核或后加图只作定位对照，命题有作者文字独立支持。'
 rows.append(r);return cid

specs={
 'p0012-fig1':('unverified','实际整图查看：1分钟原图105至111，106标3919.31，111标3724.19；数个红绿箭头及MACD对应64正文。105/108/109等时间点各自保存，位图原发/制作者未核。'),
 'p0013-fig1':('later_annotation','实际整图查看：1分钟重绘图108至111，111标3724.35，附作者正文文字和框/箭头及另一MACD指标；后加整理者和日期未核，不能把内嵌文字或111数值改作作者原始图证。'),
 'p0014-fig1':('later_annotation','实际整图查看：5分钟重绘图102至111，111标3724.35，内嵌104至105/105至110比较文字；横轴右端已到07/03，晚于64课7月2日晚。左上光标2007/07/02不是全图截止，不用后续K证明当时已知。'),
 'p0021-fig1':('later_annotation','实际整图查看：5分钟重绘图至7月6日，低点3563.72；框内并列作者7月6日正文、读者夜雨提问及CCTV回答。CCTV“没有构成大级别买点”不能归作者；整理者/日期未核，图中他人标注不替作者取证。'),
 'p0022-fig1':('later_annotation','实际整图查看：日线图三种调整假设，另绘“实际走势三角形调整”；右端已到8月并标5235.16/5050，晚于7月8日文章，光标7月9日也不代表截止。后验对照及两虚线假设不是作者当时已经实现的预言，原制作者未核。'),
}
ops=[]
for f in figs:
 status,n=specs[f['id'].split(DOC+'-')[1]];after=dict(origin_status=status,note=n);ops.append(dict(table='figures',id=f['id'],before={k:f[k] for k in after},after=after,reason='本次主代理实际查看原页和整图'))
 f.update(after);f.update(lesson_number=64,visual_review_complete=True,reviewer=REVIEWER,visual_review_note=n,source_pdf_sha256=PDF_SHA,render_sha256=sha((OUT/f'{BASE}.visual'/f"{f['id'].split(DOC+'-')[1]}.png").read_bytes()))

c('106-107-arrow-stroke-under-preset-rounding','12-b005 13-b000','106至107箭头所指那一笔以取整为预设前提；作者认为在该前提下成立，但不要求所有人必须取整。','笔|价格精度',1,'具体图例和先定精度同时保；本段未再指定取整算法，61课直接截整的“以后”选择另存，不强行以0.5容差或小数数据重算为唯一答案。',conditions=['本课106至107箭头位置','预设取整且一路一致'],figures=['p0012-fig1'])
c('108-109-not-three-segments-same-direction-gap-contained','13-b002','本例108至109带箭头的一笔不另算线段，108至109不分三段；作者以至少三笔成段及当日低开缺口顺前一笔、未破坏前笔说明。','线段|笔|缺口',1,'至少三笔为必要条件非充分；顺向且未破坏两个条件保，突发逆向缺口早期说法另列待核，不泛化所有缺口。',figures=['p0012-fig1'])
c('first-red-arrow-already-near-prior108-109-area-strong','13-b003','110至111刚起跌、第一次略破109时，已出现MACD面积接近108至109对应面积总和，作者据此说力度强，不能以该处当对108至109的最终背驰点。','MACD柱波|背驰|动力学',1,'原已出现面积与前对应面积之和及略破109时点保；不把柱高代面积或未完成下跌当已背驰。',figures=['p0012-fig1','p0013-fig1'])
c('110-111-compare104-105-around105-110-center','13-b003 14-b000','110至111实际应与104至105下跌力度比较，中间震荡中枢为105至110；这里不能用108至109作最终比较对象。','背驰|中枢震荡|动力学',1,'105至110与下条105至107是不同所指枢，不静合；不把任意最近下段当比较对象，图14是后加5分钟重绘。',figures=['p0012-fig1','p0014-fig1'])
c('110-not-third-sell105-107-near-leave-wait-structure-break','14-b000','站在105至107中枢角度，110虽接近但不构成三卖；对这次强离开，即使搞不清比较段，也至少等其结构被破坏才有介入可能，后面两次上下上反抽未破坏。','第三类卖点|确认|线段破坏',1,'接近不等成立；至少等破坏仅必要等待条件，非一破坏必买，原图示范围内的力度判断非所有离开必强。',figures=['p0012-fig1','p0014-fig1'])
c('green-rebound-analogue-third-sell-micro-center-two-branches','14-b002','绿箭头反抽被作者视为破位前上下上微型类中枢的类三卖；随后可转大级别类中枢，或类中枢移动直至形成新类中枢。','类中枢|第三类卖点|线段',1,'严格线段以下无中枢的旧澄清保；类卖点及两分支不是正式中枢三卖，也不能从不明制作者框注独立推出。',figures=['p0012-fig1'])
c('second-red-arrow-down-up-down-break-not-div-without-sudden-destruction','14-b002','讨论价格图第二红箭头时，作者把黄白线视为下上下中第二下刚破上的低点、力度最大的一下，并说MACD第一个红箭头指这一下；除非线段结构突发破坏，此时不可能背驰。','背驰|线段破坏|动力学',1,'区分价格图第二红箭头与MACD第一个红箭头两套标记；只限本图比较/时序，保突发破坏例外；原下上下字不翻转，不把所有向下突破无条件排除背驰。',exceptions=['本例线段结构出现突发性破坏'],figures=['p0012-fig1'])
c('running-up-down-up-second-micro-center-final-green-area-comparison','14-b002','后一次回拉构成奔走型上下上，第二上与第一上低点稍重合，形成另一微型类中枢；两类中枢形成下跌后，针对第二类中枢前后两段比较MACD绿柱面积判断背驰。','类中枢|MACD柱波|背驰',1,'第二上/第一上低点及稍重合原字保，不擅改为另一高低定义；本例类趋势比拟非严格线段下中枢，价格图两个未定位背驰的红箭头与最终MACD两红箭头的绿柱比较须区分，不混为同一组标记。',figures=['p0012-fig1'])
c('july3-neckline-break-and-retest-triangle-D-less-certain','15-b001','7月3日作者把3919颈线下的头肩底称为雏形；能否成立仍看颈线突破与回抽确认，三角形D段上行是当时最佳剧本但把握低于此前B段。','确认|经验压力线|三角形整理',2,'雏形/剧本/确认和两时点把握均保；未给概率数值，未把未来回抽或后验8月图作当时完成证据。')
c('july4-volume-neckline-break-or-pattern-damage','16-b003','7月4日作者指出，颈线不能放量突破，图形就受破坏，最坏情况为缩量阴跌。','成交量|确认|经验压力线',2,'当日颈线语境及最坏分支非必然结果；不以任意放量单条件充分确认所有突破。')
c('weak-skill-no-capital-half-flat-enlarge-operating-level','16-b003 16-b005','对技术与资金实力不足者，作者允许半仓甚至空仓等待；没有资金实力者按技术行动，尤其技术不好者应放大操作级别。','仓位|操作级别|操作熟练程度|交易容量',1,'对象条件保，半仓空仓是允许选择；放大级别不是被套后任意更换原级别或承诺低风险。')
c('idle-money-only-market-not-disrupt-normal-life','17-b007 18-b000 18-b002 20-b004','作者要求散户只用空闲的钱参与市场，有压力的钱不应投入，也不能因股票影响正常生活；附后的三大纪律再次重复该要求。','资金管理|风险承受能力',1,'仅归作者散户资金纪律，未核其个人经济状态，不把无压力推成能承受任意风险。')
c('retail-wait-large-buy-after-market-forces-have-result','18-b000 18-b003 20-b005','即使资金无压力，散户也不应参与风险过大的活动；作者要求等市场合力走出结果，特别等大级别买点再介入。','买点|操作级别|等待|合力',1,'结果和大买点前提保；不是等作者亲自获胜，文中阵地战/报复修辞不升为技术条件。')
c('retail-follow-result-not-author-intervention-personal-resources','19-b003 19-b004 19-b005','作者明说自己的干预在纯技术角度错误；普通散户无须仿效，只需根据合力结果、自己的操作级别买点买卖点卖。','合力|操作级别|买卖点|操作节奏',1,'作者的特殊资源、动机和一般散户分开；2100极端调整是当时可能而非预定价位，不将个人行动当理论无条件买入信号。')
c('july5-three-target-themes-rely-annual-line-history','18-b008 20-b000','7月5日作者当时关注整体上市、大重组和中小成长三个领域，技术上依靠年线，后文再述介入目标均有年线依托。','均线系统|选股|基本面',3,'仅历史个人目标和筛选条件；不是年线附近任意股票都可买，7月16日新资金迹象答疑另明确，未核资金流。')
c('july6-five-minute-bottom-divergence-teaching-case','20-b009','7月6日作者让读者观察前日两波反抽、当日急拉再下跌如何构筑反攻形态，并以5分钟图的底背驰作教学案例。','背驰|周期K线图|合力',3,'作者称用钱构筑为其自述，不能据此证明实际资金行为；图21含CCTV答复仅读者意见，未把“大级别买点”判断归作者。',figures=['p0021-fig1'])
c('one-bullish-engulfing-not-all-larger-conditions-repaired','20-b011','7月6日作者提醒，大的技术形态仍不利，不能因一根阳包阴就认为局面已经平稳。','周期K线图|确认|走势预测',3,'当时较大形态判断，不把一根K线作为所有级别转向充分条件；不是本项目独立验证技术指标。')
c('july8-triangle-branch-requires-effective3919-rebreak','21-b008','7月8日三分支中，三角形调整要求多方能量最大；当时视为前三段已完、第四段向上，要成立必须重新有效突破3919颈线。','三角形整理|确认|经验压力线',2,'历史假设分支与必要条件，不是已成三角/已突破；后加实际走势线不能证明原时点预知。',figures=['p0022-fig1'])
c('july8-platform-branch3400-strong-above-usual-trap-limit2800','21-b010','7月8日若不能重站3919，平台分支将再次考验3400；作者列最强在3400上完成，一般跌破作空头陷阱，极限约2800。','平台式调整|确认|空头陷阱',2,'最强/一般/极限与历史分支层次保，不当全市场固定跌幅规律或2800保证止跌。',figures=['p0022-fig1'])
c('july8-large-platform-after-rebound-renewed-fall-limit2100','22-b001','大平台分支是在第二种平台后先有大反弹再重新下跌，作为1000点起两年行情的大调整，作者估极限约2100。','平台式调整|走势预测',3,'先后顺序和较大调整对象保，2100仅当时极端估计，不把普通平台2800与大平台2100混成同分支。',figures=['p0022-fig1'])
c('july8-branch-duration-first-two-fast-july-third-atleast-halfyear','22-b002','作者估计前两种调整最快7月可完，第三种至少半年；市场当下形成，尚无预定必须走哪一支。','走势预测|当下|合力',3,'最快和至少各属不同分支，未验证预测成败；不能用后验图实际线回改当时尚未选定状态。')
c('market-resultant-not-any-component-different-interests','21-b006 22-b003 22-b004','市场走势是合力，任何一方即使强大也只是分力；不同利益形成不同分力，不能把作者个人力量当成市场合力本身。','合力|分力',1,'作者市场解释与个体地位边界，不作力学量测或所有信息完全可见的证明；不继承贬词当对象事实。')
c('july8-low-skill-can-flat-another-hold-potential-stock-choice','23-b003 23-b004','作者对无力做震荡者给出空仓等调整完的选择，同时提出另一种持有潜质股全仓不动的选择，后者依赖其当时长期牛市判断。','仓位|操作级别|基本面|风险承受能力',2,'两种不同选择并列，不能将空仓或全仓当统一命令；20年3至5万点/必然行情和股票必赚为作者预测，不是本项目保证。')
c('no-operation-suits-everyone-match-resources-position','23-b007','作者要求先认清自身实力和位置再选择合适操作，并明确没有任何操作适合所有人。','操作策略|交易容量|风险承受能力',1,'个体资源和位置是选择前提，不将作者自述的金融战略职责加给普通读者。')
c('july9-lower-level-strong-return-to-old-center-under3900','23-b009','7月9日作者以比原下跌更低级别且更猛烈的方式，重回此前3900点下中枢，称这是当日第一目标达成，后续走势仍须再看。','中枢震荡|小级别转大级别|确认',3,'历史已发生回枢与后续未定分开；3900是约略定位而非3919精确颈线，不补未给的枢区间。')
c('july10-instant3919-break-not-effective-stand','24-b006 24-b007','7月10日即使瞬间突破3919，作者仍认为压力未改；头肩底等形态最终须归于该颈线的有效突破。','确认|经验压力线',1,'瞬间与有效区分，原段未给统一时间/量化阈值，不把碰价视为已站稳。')
c('july10-lower-price-stock-joint-selection-conditions','24-b009','7月10日第一类技术选股对象须同时有跌幅约50%、年线或至少半年线附近、明显新资金进入、有题材潜质及中低价等条件。','选股|均线系统|成交量|基本面',2,'联合条件不简化成跌50%或单碰年线即买；按当时中长线建仓背景，不是现代收益承诺。')
c('july10-strong-stock-catchdown-risk-high-skill-july12-hs300-example','24-b009 29-b007','另一类是超强势股，但大盘逆转时可能补跌，因此技术要求特别高；7月12日作者把沪深300举作强势类代表。','选股|操作熟练程度|风险承受能力',2,'两日来源分别保，代表非所有沪深300永强；补跌风险不可省，估值被低估是当时作者观点未外核。')
c('dynamic-position-building-if-skilled-cost-and-trap-risk','24-b010 25-b000 24-b004','作者允许散户动态建仓、反复操作同股以降成本，并反对追高；大盘逆转个股可能砸出空头陷阱，能否动态操作仍取决于技术。','仓位|交易成本|操作熟练程度|追高',1,'减成本为方法目的非每次实盘必成0或负成本；底部大震荡容易是作者评价，不省费用与失手风险。',conditions=['有相应操作技术','按个股和既定操作条件执行'])
c('weak-skill-fundamentals-gradual-position-hold-no-forcing','25-b001','对没技术者，作者提出先研究透基本面、逐步建仓再耐心持有，并要求操作方法按个人实际情况选择，不能硬来。','基本面|仓位|操作熟练程度',2,'熬后必赚钱为作者强语未外证；不是没有技术可忽视资金与买点条件，也不把另一全仓选择强加所有人。')
c('study-theory-not-depend-author-or-any-person','25-b002 25-b010','作者要求市场操作最终归自己，不依靠任何人包括作者；可以学理论，但要自己看图并在大级别买点介入，不能依其股票梦话行动。','操作熟练程度|买点|操作级别',1,'理论几何不患是作者自评不当本项目已证定理；梦话/显摆自述和荐股跟单分开。')
c('july11-short3919-midlong4159-halfline-effective-stand','25-b009','7月11日作者分别以3919能否有效站稳衡量中短线，以当时4159的1/2线能否有效站稳衡量中长线。','经验压力线|操作级别|确认',2,'两个空间/时段不合并；原1%的可能与100%努力是修辞，非测得成功率，4159不倒改旧4144。')
c('news-follows-dominant-side-author-view','26-b005','回答利空消息担忧时，作者认为消息跟着走势走，空头主控时利空多，多头主控时也会出现利多。','消息面|合力|走势预测',3,'限作者关于消息环境的观点，不是新闻必无作用或所有利空均假；原问题是读者，不构成独立事实证据。')
c('cross-market-pe-compare-components-author-method','28-b009','7月11日晚作者主张，比较各资本市场市盈率时应看成分股对象，不能以未对齐的股票集合比较。','市盈率|基本面',3,'其所有市场都用成分股的绝对说法不作已外核统计口径事实；仅忠实保存作者比较方法和历史论证范围。')
c('july11-peg-below1-and-dynamic-earnings-growth-assumptions','28-b010 29-b000','作者以市盈率/增长率小于1作为价格合理的典型标准，并认为可接受市盈率随可预期增长率变化；增长率下降时可接受市盈率也下降。','市盈率|增长率|基本面',3,'PEG经验标准为作者观点，不是无风险买入充分条件；50%以上平均增长为当时未外核断言，增长率单位须按其百分数写法，不偷换未来已实现增长。')
c('july11-50pe-50percent-growth-to33-historical-valuation-example','28-b010','在当时约3%利率的论证中，作者把33倍市盈率与利率水平匹配，并以50%增长令50倍市盈率一年后约33倍，论证当时50倍合理。','市盈率|增长率|利率',4,'一年后市盈率数例隐含股价不变及盈利按预期增长；这只是作者估值论证，非本项目对合理价格或当前利率的认定。')
c('july12-three-bull-stages-first-components-not-finished','29-b008','作者称其中国牛市三阶段中的第一阶段是成分股行情，2007年7月当时认为尚未结束，有实在意义的行情须有成分股加入。','牛市三阶段|成分股|走势预测',3,'保作者当时长期牛市判断，非对20年行情已实现的验证，不用后验图证明所有轮动。')
c('july13-no-skill-fund-index-suggestion-not-tracking-guarantee','30-b003','作者主张自己的钱自己操作；缺乏这方面能力者可交给特别好的公募基金，偏好指数型，并以不会跑输指数作其理由。','资金管理|操作熟练程度|指数基金',3,'不会跑输为原强说法，非本项目跟踪误差/费用后收益保证或现代产品推荐；未把其对私募的贬词录为全部事实。')
c('july13-accumulating-lower-price-stocks-may-not-explode-shortterm','30-b005','7月13日作者说，中低价目标股在换庄或收集筹码阶段，短线不一定火暴；沪深300当时则有长线资金关照而轮动。','选股|仓位|操作节奏',3,'限定当时两类股票和作者判断，阶段叙述未核逐笔资金；轮动不等每只必立刻上涨。')
c('july16-weak-shortterm-no-buy-before-fiveweek-restand','31-b000','对中短线且技术不好的投资者，作者说在5周均线重新站稳之前没有必要参与买入；中长线投资者则可对前述两类股震荡建仓。','操作级别|均线系统|操作熟练程度|仓位',1,'两个投资者对象和可/没必要分开；5周不能改5月/5日，不把长线选择当短线被套后的任意改级理由。')
c('annual-line-alone-not-good-need-new-capital-volume-signs','31-b013','作者明确不是年线附近就一定好，而须有新资金进入迹象，可从成交量观察。','选股|均线系统|成交量',1,'年线位置非充分条件，新资金为观察迹象非已验证账户流入；不因读者问安全而回答成一定安全。')
c('know-buy-reason-or-do-not-buy','32-b002','作者要求买时知道自己为何买；对所买股票须有深入了解，不知道购买理由就绝对不能买。','基本面|买点|操作熟练程度',1,'了解与理由不是亏损不可能或任何基本面估值必正确；原没恐慌必要不等风险消失。')

relation_specs={
 '110-111-compare104-105-around105-110-center':[('背驰','动力学','requires')],
 'green-rebound-analogue-third-sell-micro-center-two-branches':[('类中枢','第三类卖点','qualifies')],
 'weak-skill-no-capital-half-flat-enlarge-operating-level':[('操作级别','操作熟练程度','qualifies')],
 'idle-money-only-market-not-disrupt-normal-life':[('资金管理','风险承受能力','requires')],
 'market-resultant-not-any-component-different-interests':[('合力','分力','qualifies')],
 'no-operation-suits-everyone-match-resources-position':[('操作策略','风险承受能力','requires')],
 'dynamic-position-building-if-skilled-cost-and-trap-risk':[('仓位','操作熟练程度','requires')],
 'annual-line-alone-not-good-need-new-capital-volume-signs':[('选股','成交量','requires')],
}
for r in rows:r['relations']=[dict(source=canonical.get(a,a),target=canonical.get(b,b),type=t) for a,b,t in relation_specs.get(r['id'].split('lower-l064-c-stage-')[1],[])]

# Every non-header author paragraph has a deliberate disposition; no default
# "author = processed" shortcut is used for the long attached articles.
note('12-b003 12-b004 14-b001 14-b003 14-b004','teaching_or_personal_context','理论几何自评、机场补课/安检与练习62/63的教学背景。','不将理论自评作外部证明，行程无需转技术命题。')
note('12-b005 13-b000 13-b001 13-b002 14-b002','existing_claim_retained','精度选择一致、顺向缺口、段被段破坏、线段以下类中枢的旧命题保留，具体图例本轮另补。','旧16命题陈述/条件/引文定位不改；0.49/0.51边界不能导出随意变精度，突发逆向缺口仍待后课精确定义联读。')
note('13-b003 14-b000','historical_technical_case','第一箭头已近前段完整面积，实际104至105比较/105至110枢，与105至107及110非三卖结构等待条件分别补录。','不把最近108至109代实际比较段；原正文接页完整，后加5分钟图含次日K不作当时预知。')
note('15-b002 15-b003 15-b004 15-b006 15-b007 15-b008 15-b009 16-b000 16-b001 16-b002 16-b004 16-b006 16-b008 16-b009 16-b010 17-b000 17-b001 17-b002 17-b003 17-b004 17-b005 17-b006 18-b005','historical_political_or_personal_context','7月3/4持仓/干预、资金博弈和监管/金融安全政治评论完整阅读；其中技术颈线与资金/技能纪律另取。','贬称、他方动机、市场操控、法律责任/刑罚与个人战绩未外证，保来源不升普遍技术或现代法律事实。')
note('17-b007 18-b000 18-b002 18-b003 18-b004 20-b004 20-b005 20-b006','capital_discipline','两次三大纪律与生活资金边界完整读，前两条及大级买点已抽；第三条政治对象的高位不抬轿保原文，技术上勿追高另有24页独立证据。','不把针对特定政治对象的表述改成支持民族/敌我识别的事实，也不将闲钱当免风险。')
note('18-b007 18-b008 18-b009 19-b001 19-b002 19-b003 19-b006 19-b007 19-b008 20-b000 20-b001 20-b002','historical_intervention_context','7月5日周线刚破、两次50点反抽失败、三主题年线依托、1%战役与PE资金后路/0成本等自述；普通散户不仿效与三主题另列。','资金来源/控制权/盈利/失败概率未实证；作者干预和纯技术规则冲突明说，不能把其资源能力加给一般读者。')
note('20-b008 20-b010','personal_or_political_context','黄河音乐/纪念日及个人资金出力自述保留，相关5分钟底背驰另列案例。','不将战争比喻作交易因果或账户成交证据。')
note('20-b012 22-b004 23-b002 24-b008','same_method_other_context','散户按自身级别买卖并看合力轨迹的方法在不同日重复，关联本批retail-follow-result命题及旧63操作级别命题。','相同方法不反复造重复命题；不要求陪同作者失败。')
note('21-b006 22-b003','resultant_scope','市场非作者一人、任何分力非合力的边界已补。','不把合力比喻当已测力学值。')
note('22-b005 23-b000 23-b001','historical_motivation_context','利益冲突、1%也做的自述及散户/作者资源差异。','1%非统计胜率，政治动机非普适技术理由，不代读者承担阵地风险。')
note('23-b005 23-b006 24-b001 24-b002 24-b003','historical_stock_and_personal_context','15.19潜质股/30元应值/产品成本低30%及基本面未明、题材与作者个人目标、三角剧本和短期反攻自述均保原文。','未核账户、重组与生产/估值外部事实；23-b006明确不是仅其持股才好，技术心态重要，不能据实例承诺15.19必赚或自己可以改造基本面。')
note('23-b010 24-b000','source_and_teaching_context','战争期暂不发分段、沿用62标准及上一日文章解释。','未给的分段答案不代作者补出，改用已给正文与严格定义。')
note('25-b003 25-b005 25-b006 25-b007 25-b008 25-b011 26-b000 26-b001','historical_rhetoric_self_report','作者承认立场色彩、无量收窄预期后续更广对攻、个股原价涨幅/梦话和回答安排完整读。','预测非已确认方向，个人业绩/贬词不外证，不以理论几何自评保证交易或把价位猜谜作新荐股。')
note('26-b008 26-b011 26-b014 27-b001 27-b004 27-b011 28-b003 31-b007 31-b010 32-b005','existing_claim_retained','旧16条覆盖图周期中枢起点精度、预先/实际段确认、幅度不定级、最低构造/次级线段比喻、至少三笔、反弹中枢位置/级别、标准分解和结合律、顶底间K与背驰段失效。','读者问题只是作者短答指代范围；原被/后者等排印字留证据，不静改为作者未写的严格算法。')
note('27-b007 27-b014 28-b000 28-b005 28-b006 28-b007 28-b008 29-b001 29-b002 29-b003','historical_financial_opinion','政策耐心、投资价值争辩、各市场投机强弱绝对话语和未来中国公司/沪深300低估预测。估值方法另取28b9/b10/29b0。','未经跨市场数据核实，历史50倍/增长率与500强100家预测不当当前统计或已证事实；不复制贬称为事实判断。')
note('29-b005 29-b006 29-b009 30-b000 30-b002 30-b004 30-b007 30-b008 30-b009 31-b004','historical_commentary_context','7月12/13/16颈线形势、私募自检/地量解释、理念/资金人气、宏观利空落地与资本市场影响实体的观点完整阅读。','未外核具体账户/市场因果和危机人为归因，不以反复震荡叙事造统一阈值或必然方向，持仓与弱技能原则另取。')

issue('sudden-reverse-gap-early-analogy-not-universal-exception','13-b002','早期文字称突发逆向530式缺口必当一段，并用0=0+0+0类比三笔；后67明确划分精确定义，72继续澄清。','保存早期原说并联读lower-l067-definition-refines-segment-destruction及67两情况；不把价格跳空偷换特征序列缺口，未足证所有逆向缺口成段例外。',True)
issue('micro-center-running-form-and-execution-boundaries','13-b003 14-b000 14-b002','类中枢/类三卖、第一箭头面积与第二箭头下上下、奔走型第二上与第一上低点稍重合均已忠实记录。','原特殊措辞不改高低字；缺逐K数据和执行回放，不将类比升级正式定义或保证当下成交。',True)
issue('figure-provenance-future-bars-and-reader-overlay','12-b004 20-b009 21-b002 21-b004 22-b002','5图仅原始样式图未核、4后加；14含7/3，22含8月实际走势，21并列作者与夜雨/CCTV文字。','原博客/位图作者未核；后验图不可证前瞻，CCTV回复不是作者对大级别买点的否认，111两版本3724.19/3724.35不静合。')
issue('historical-valuation-growth-fund-and-return-strong-claims','23-b004 23-b005 25-b001 28-b010 29-b000 29-b002 30-b003','长期3至5万、个股必赚/熬可赚、PEG/50倍合理和指数基金不跑输均为作者历史观点或预测。','来源复核不等经济/估值/账户实证，明确条件及强语，不用当前知识回改原文或当现代投资推荐。')
issue('precision-old-stroke-and-cross-lesson-definitions','12-b005 13-b001 31-b010','取整为示范可选但必须一致；7/16答不完全属于顶底的K线边界与62/77新旧笔各有语境。','61明确截整以后选择不覆盖64用户自选；读者2至4K震荡不获认可，不按字面统一成原始额外根数。')

amend=[]
changes={
 'lower-l064-gap-in-same-stroke':('只取文字给定条件；108-109图中具体分段另列图审待核。','原试点只取文字；2026-10-21本轮已实际图审并另补108至109案例，参见lower-l064-c-stage-108-109-not-three-segments-same-direction-gap-contained；位图原发仍未核。'),
 'lower-l064-line-below-center-is-analogy':('具体绿箭头案例未图审，故只抽取作者括号内明确的一般澄清。','原试点只抽作者括号内一般澄清；2026-10-21本轮绿箭头及两类中枢图例已审并另补，参见lower-l064-c-stage-green-rebound-analogue-third-sell-micro-center-two-branches；仍不把后加图认作作者原发。'),
}
for id,(a,b) in changes.items():
 assert old[id]['review_note'].count(a)==1
 amend.append(dict(id=id,before_review_note=old[id]['review_note'],after_review_note=old[id]['review_note'].replace(a,b),reason='只更新原试点具体图例未审的过时描述，所有命题语义/条件/证据保持'))
ledger=[]
for id,p in ps.items():
 linked=[r for r in rows if any(e['passage_id']==id for e in r['evidence'])];n=notes.get(id)
 if not n:
  if linked:n=dict(category='new_claim',reading='；'.join(r['text'] for r in linked),reverse='；'.join(r['review_note'] for r in linked))
  elif p['role']=='reader':n=dict(category='reader_context',reading='保留读者原问题/署名与日期：'+p['text'],reverse='读者前提和CCTV等他人答案不作作者观点，作者仅按实际答复范围取证。')
  elif p['text'].startswith('缠中说禅') and len(p['text'])<70 or len(p['text'])<100 and re.search(r'2007-\d\d-\d\d',p['text']) or p['text'] in ['散户三大纪律','一、三角形调整','二、平台型调整','三、大平台型调整']:n=dict(category='source_header',reading='标题/发言人时间头或条目标题定位。',reverse='只作来源锚点，不单独证明技术结论；日期空格存储格式不改变原时点。')
  else:raise AssertionError(('unaccounted source',id,p['text']))
 ledger.append(dict(passage_id=id,lesson_number=64,document_id=DOC,pdf_page=p['pdf_page'],role=p['role'],speaker=p['speaker'],published_at=p['published_at'],source_text_sha256=sha(p['text'].encode()),result='new_claim' if linked else n['category'],claim_ids=[r['id'] for r in linked],related_existing_claim_ids=retained[id],existing_semantics_and_quote_geometry_not_mutated=True,pending_issue_ids=[i['id'] for i in pending if id in i['passage_ids']],reviewer=REVIEWER,rounds={'1_read_and_scope':n['reading'],'2_atomic_conditions':[dict(claim_id=r['id'],conditions=r['conditions'],exceptions=r['exceptions']) for r in linked],'3_normalization':dict(concept_labels=sorted({v for r in linked for v in r['concepts']}),related_existing_claim_ids=retained[id]),'4_reverse_check':n['reverse']+('；'+'；'.join(r['review_note'] for r in linked) if linked else '')}))
for f in figs:f['linked_claim_ids']=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])]
summary=dict(stage='H early pilot64 completion',graph_version=VERSION,schema_version=meta['schema_version'],document_id=DOC,lessons=[64],reviewer=REVIEWER,claims=len(rows),evidence=sum(len(r['evidence']) for r in rows),relation_supports=sum(len(r['relations']) for r in rows),passages_read=223,existing_claims_retained=16,review_notes_amended=len(amend),source_passages_snapshot_sha256=sha(j(sorted(ps.values(),key=lambda r:r['id'])).encode()),whole_lesson_semantic_read_complete=True,technical_extraction_complete=False,four_round_review=True,independent_review_claimed=False,visual_pdf_pages=list(range(12,33)),figure_objects_viewed=5,figure_origin_counts=dict(Counter(f['origin_status'] for f in figs)),new_concepts=sorted({v for r in rows for v in r['concepts']}-set(canonical.values())),pending=[i['id'] for i in pending],database_mode='ro',formal_import=False,delivery_scope='shared_knowledge_base_only')
for suffix,data in [('reviewed.jsonl',rows),('coverage.jsonl',ledger),('pending.jsonl',pending),('figures.jsonl',figs)]:
 target=OUT/f'{BASE}.{suffix}';assert not target.exists(),target;target.write_text(''.join(j(r)+'\n' for r in data),encoding='utf-8')
target=OUT/f'{BASE}.summary.json';assert not target.exists();target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plan=dict(base_graph_version=VERSION,source_pdf_sha256=PDF_SHA,reviewer=REVIEWER,figure_operations=ops,claim_review_note_amendments=amend,source_passage_changes=[],evidence_changes=[],claim_semantic_changes=[])
target=AUDIT/'stage-h-l064-amendment-plan.json';assert not target.exists();target.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
db.close();print(j(summary))
