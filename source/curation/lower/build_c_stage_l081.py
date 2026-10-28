"""Stage C lesson 81 curation; reads KB mode=ro and writes only own lower files.
All four semantic review rounds use the same GPT-6.1 Sol xhigh agent.
"""
import hashlib,json,sqlite3,sys
from collections import Counter,defaultdict
from pathlib import Path
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
BASE=Path(__file__).resolve().parent
KB=Path(r'C:\Users\13240\Desktop\RAG\shared-knowledge\v0.1.0')
NAME='c_stage_l081_sol61';PREFIX='volume_2-5332cd1b6038-'
REVIEWER='GPT-6.1 Sol xhigh / 阶段C下册第81课四轮复核'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('BEGIN')
meta={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
P={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id='lesson-081' ORDER BY pdf_page,block_index")}
existing={r['id']:dict(r) for r in db.execute('SELECT * FROM claims')}
registry={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
candidate_map=defaultdict(list)
for r in db.execute("SELECT cl.id,e.passage_id FROM claims cl JOIN evidence e ON e.claim_id=cl.id JOIN passages p ON p.id=e.passage_id WHERE p.unit_id='lesson-081' AND cl.review_status!='reviewed'"):candidate_map[r['passage_id']].append(r['id'])
contexts={};section=''
for p in P.values():
    if '(2007-' in p['text'] and len(p['text'])<100:section=p['text']
    contexts[p['id']]=section
claims=[];decisions={};pending=[]

def add(slug,text,concepts,refs,level,reason,conditions=(),exceptions=(),note='',figures=()):
    cid='lower-l081-c-stage-'+slug
    assert cid not in existing and cid not in {c['id'] for c in claims},cid
    citations=[]
    for ref in refs:
        short,quote=ref if isinstance(ref,tuple) else (ref,None)
        p=P[PREFIX+short];quote=p['text'] if quote is None else quote
        assert p['role'] in ('author_body','author_reply','author_commentary') and p['speaker']=='缠中说禅'
        start=p['text'].find(quote);assert start>=0 and p['text'][start:start+len(quote)]==quote,(cid,short)
        citations.append({'passage_id':p['id'],'quote':quote,'quote_start':start,'figure_ids':[PREFIX+f for f in figures]})
    context=' / '.join(dict.fromkeys(contexts[e['passage_id']] for e in citations))
    scope='；'.join(conditions) or '作者讨论的'+'、'.join(concepts)+'对象及原段明确前提'
    c=dict(id=cid,text=text,kind='explicit',conditions=list(conditions),exceptions=list(exceptions),concepts=list(concepts),ambiguity_status='none',review_note=f'语境：{context}。适用条件：{scope}。四轮由同一复核者执行：完整上下文阅读、原子拆分、术语及既有命题归一、逐条逆向证据核验。{note}',reviewer=REVIEWER,importance_level=level,importance_reason=reason+'；等级是整理重要性判断。',evidence=citations,relations=[])
    if figures:c['figure_review_note']='已实际查看volume_2.pdf实际PDF页'+'、'.join(dict.fromkeys(str(int(f[1:5])) for f in figures))+'的对应图及相邻文字，核对点号、相对位置和作者限定。数据库图源仍为unverified；未声称原博客作者原图已溯源，不从图补造文字没有的规则。'
    claims.append(c);return cid

def mark(short,category,reason,old=()):
    assert PREFIX+short in P
    decisions[PREFIX+short]={'category':category,'reason':reason,'existing_claim_ids':list(old)}
def hold(slug,shorts,issue):
    pending.append({'id':'lower-l081-c-stage-pending-'+slug,'lesson_number':81,'document_id':PREFIX[:-1],'passage_ids':[PREFIX+s for s in shorts],'status':'pending','issue':issue})
    for s in shorts:mark(s,'valuable_pending',issue)

# Rounds 1-2: complete reading and atomic extraction.
add('two-diagrams-conditional-answer','对于第81课开头两图，作者明确认可的完整答案是：5＝7或5低于7时，两图均为一段；5高于7时，两图均为三段。',['线段','线段破坏','特征序列'],['p0173-b009','p0173-b010','p0173-b011'],1,'保存例图的完整联合条件与等值边界',conditions=['第81课开头图一、图二的编号及给定走势'],figures=['p0173-fig1','p0173-fig2'],note='p173-b009在正文中是引述读者答案；作者b010明确称正确答案完整写出，b011明确认可其完整性，因此记录作者认可的答案，不仅凭author_body标签归属。')
add('two-diagrams-second-case','上述两图属于线段破坏第二种情况，必须考察高点下来走势的特征序列，并处理包含关系，才给出完整分段答案。',['线段破坏','特征序列','包含关系'],['p0173-b010','p0173-b011'],1,'保存完整答案依赖的判断方法',conditions=['第81课开头两图','第二种线段破坏情况'],figures=['p0173-fig1','p0173-fig2'],note='作者此前下午仅按7不低于5看图作答，不把此前不完整答案与完整条件答案并列为等效。')
add('lesson71-last-diagram-correction','作者明确更正第71课最后一图：原图把类似7的位置画高了，应使类似7的位置低于类似5的位置，才是三段。',['线段','线段破坏','特征序列'],['p0173-b012'],1,'直接保存作者对第71课错误示意图的更正',conditions=['第71课最后一个黑色示意图','与第81课两图类似的位置5、7关系'],figures=['p0173-fig1','p0173-fig2','p0094-fig2'],note='实际对照p94右下标“三段”的旧图和p173文字；p94-b002已指向81课。只保存作者明确7应低于5的更正，不以p94/p95后加标准组合图替代作者证言。')
add('case-1017-low-changes-stroke','作者更正2007年9月17日划分时指出，10:17低点5386.47高于前一分钟5386.39，顶分型的顶实际在10:17，故该处构成一笔，整个划分应改变并形成1分钟中枢。',['分型','笔','线段','最小级别中枢'],['p0174-b000'],3,'保存细微数据核对影响划分的案例',conditions=['2007-09-17作者所举10:16/10:17数据及图示'],note='具体分段第二、三段在此留题，不能由模型替作者补答案。')
add('short-strokes-check-inclusion','对只有5、6根K线的笔候选，应仔细核对其中是否有包含关系，避免粗看图形误判。',['笔','包含关系','K线'],['p0174-b001'],2,'保存容易误判的实际核对步骤',conditions=['本课短K线组笔候选检查'])
add('self-similarity-human-basis','作者把分型和走势类型研究的哲学基础归为人的贪嗔痴疑慢：同类心理随时间环境改变大小，经市场合力反映为走势的自相似性。',['自相似性','市场心理','市场合力'],['p0174-b004'],3,'保存作者明示的哲学论证身份',note='属于作者哲学解释，不宣称本项目已实证验证心理因果。')
add('self-similar-structures','作者把分型、走势类型和走势必完美的本质都归为自相似性，即不同级别虽尺度不同而结构相同；分型从1分钟到年线均可呈相同结构。',['自相似性','分型','走势类型','走势终完美','级别'],['p0174-b005'],1,'保存本课自相似性含义与适用结构')
add('self-similarity-understanding','作者认为走势因有自相似性才可理解、把握，把握走势的实质就是把握自相似性。',['自相似性','技术分析'],['p0174-b006'],3,'保存自相似性的理论用途',note='以“作者认为”保留理论主张，不写成实证收益结论。')
add('levels-self-organize','作者说明级别由自相似性自组、生长出来，而不是先有级别再有自相似性；只要构成走势者仍具其所述相同人性条件，自相似性与级别自组性就存在。',['自相似性','自组性','级别'],['p0174-b007'],1,'保存级别形成的理论方向和条件',conditions=['作者关于人的贪嗔痴疑不改变、参与者仍为人的哲学前提'],note='基因与生命是作者比喻；未添加形式生成算法。')
add('philosophical-life-metaphor','作者把人性引发的自相似性及走势级别自组性称为理论的哲学本质，并以发芽、生长、绽放、凋败描述走势类生命特征。',['自相似性','自组性','走势'],['p0174-b008','p0175-b000'],3,'保留作者哲学层次及类生命措辞',note='不把该类生命叙述改为生物学事实。')
add('developable-research-directions','作者将走势自相似性、自组性列为可持续扩展和精细化的研究方向，举不同交易条件下选择自相似结构为例。',['自相似性','自组性','交易条件'],['p0174-b009','p0175-b005'],3,'保存理论开放性及明确研究对象')
add('nonisomorphic-analysis-paths','作者提出：有多少不同构的自相似性结构，就有多少种分析股市的正确道路；脱离自相似性的分析方法在其理论判断中错误。',['自相似性','技术分析'],['p0175-b002'],3,'保存作者所称定理及判断范围',note='记录作者明说；本课未给形式证明，整理者不声称已证明唯一性或排他性。')
add('two-nonisomorphic-basic-structures','作者把分型与走势类型称为两种不同构、当前讲授的最基础自相似结构；其他结构的寻找及不同结构对应操作差异属于进一步理论研究。',['自相似性','分型','走势类型','操作策略'],['p0175-b001','p0175-b003'],2,'保存基础结构与扩展研究的区分')
add('declared-open-questions','作者明确说其理论暂未解决走势能容纳多少自相似结构，以及起始交易条件如何影响结构生成的问题。',['自相似性','交易条件'],['p0175-b004'],3,'保存作者自己声明的理论未解边界',note='未把作者的开放问题伪装成已经解决的规则。')
add('extremes-need-fractals','本课提出所有顶必须表现为顶分型、所有底必须表现为底分型；因此没有顶分型则没有顶，没有底分型则没有底。',['自相似性','顶分型','底分型','顶','底'],['p0175-b006','p0175-b007'],1,'保存必要条件及其否定推论的原文明说',note='仅必要条件；未逆推每个顶分型都是最终大顶。')
add('hold-until-selected-chart-top','在操作者操作级别的K线图上没有顶分型时，作者建议继续持有，等待该图顶分型出现再处理。',['操作级别','周期K线图','顶分型','持股'],['p0175-b007'],2,'保存持有建议对应的图表和级别',conditions=['在所选操作级别的K线图上','尚无顶分型'],note='未从原句增添一有顶分型就必立即卖出或长期大顶的结论。')
add('levels-compatible-constraints','不同级别走势可同时独立发展，例如30分钟中枢震荡与5分钟上涨可以并存；把多级别条件像联立方程一样综合，可缩小可能走势边界。',['自相似性','级别','边界条件','中枢震荡','上涨'],['p0175-b008'],1,'保存跨级别不矛盾及联合约束的方法',note='“独立”不被改为统计独立或互不影响；原文以联立方程作类比。')
add('multiple-level-observation','作者要求观察走势不能只看一个级别，应立体地结合多级别，利用自相似结构提供的条件。',['自相似性','级别','操作策略'],['p0175-b009'],2,'保存多级别观察方法')
add('case-thirty-minute-classification','在2007年9月18日附文中，作者用30分钟操作举例：按该级别上涨、盘整、下跌分类，不参与该级别下跌；其他操作级别同样按自身节奏处理。',['操作级别','完全分类','上涨','盘整','下跌'],['p0175-b013','p0176-b000'],2,'保存操作级别内完整分类与不参与下跌的策略',conditions=['附文给出的30分钟操作示例'],note='不把世纪大顶的修辞当预测，不将观察图精度与操作级别混为一谈。')
add('case-five-minute-third-buy-boundary','对2007年9月18日原76—85的5分钟中枢，作者以有无第三类买点区分；若未出现则继续震荡，并将该案例的5分钟震荡扩为30分钟中枢。',['第三类买点','中枢震荡','中枢扩展'],['p0176-b001','p0177-b000'],3,'保存当时案例的分支与级别',conditions=['2007-09-18原76—85的5分钟中枢案例'],figures=['p0176-fig1','p0176-fig2'])
add('case-departure-not-finished','2007年9月18日超短线当时为102—105中枢震荡，离开原5分钟中枢的走势尚未完成，所以还不能谈回抽。',['完成','中枢震荡','次级别','第三类买点'],['p0177-b001'],2,'保存离开和回抽判断的时序',conditions=['2007-09-18所述102—105及原5分钟中枢案例'],figures=['p0176-fig1'])
add('old-rule-missing-inner-bar','作者说明部分复杂分段源于第一次笔破坏后不能延伸成线段；本例绿箭头处顶底分型包含处理后中间无K线，按此前标准不能算一笔。',['笔破坏','线段','笔','包含处理'],['p0177-b007'],2,'保存旧标准下不能延伸成段的原因',conditions=['2007-09-18绿箭头处示例','按此前分型间有独立K线的笔标准'],note='与紧接的新可用标准分开记录，未把旧标准结果永久化。')
add('new-stroke-two-joint-conditions','本课附文提出放松后的笔成立条件须联合满足：顶底分型经包含处理后不共用K线；在此前提下，顶分型最高K线与底分型最低K线之间不含这两根、且不考虑包含关系，至少有3根K线。',['笔','分型','包含处理','K线'],['p0177-b008'],1,'保存新标准两项不可拆开的联合条件',conditions=['本课2007-09-18附文提出的新笔标准','第一项必须先满足','计数排除两端最高/最低K线','中间K线计数不考虑包含关系'],note='第一项与旧标准相同且作者强调不能放松；第二项明确至少3根（包括3根）。不是将包含处理后3根作为第二项计数。')
add('new-stroke-simplifies-case','作者说上述新条件可使当日绿箭头处成立一笔，三笔下来成段，可避开106—107复杂线段，并称经计算不影响整个线段的动力学能量；但103—104这样的线段不能因此改变，仍须能处理。',['笔','线段','操作熟练程度','能量结构'],['p0177-b008','p0177-b009'],3,'保存新标准的具体效果与不可改变例子',conditions=['2007-09-18图示绿箭头、106—107及103—104案例'],note='“不影响动力学能量”保留为作者所称计算结果，本课未展示计算过程，整理者不声称独立证明。')
add('higher-types-operation-key','作者强调分型、笔、线段只是最基本准备，关键是据此辨别更高级别走势类型；同花顺收盘后标记只是教学示范，应据各自系统数据按原则划分。',['分型','笔','线段','走势类型','数据源一致性'],['p0177-b010'],2,'保存基础构造与实操对象的区别',note='不把教学标记时间等同理论不能当下划分。')
add('new-standard-optional-old-kept','作者在新旧标准答疑中说可以用新笔标准以减少软件微小数据差异、简化辨认，其他不需改变；作者本人因始终只用一套软件仍用老标准。',['笔','数据源一致性','价格精度'],['p0179-b000','p0179-b001'],1,'保存新标准适应性目的及可选身份',conditions=['2007-09-19对前一晚新笔标准的答疑'],note='不隐式覆盖已复核旧笔定义，也不说新标准已经废止旧标准。')
add('gap-not-replace-duration','对顶底分型间不满足三根K线但有缺口的提问，作者明确答不行，缺口不能替代所需延续时间。',['笔','分型','缺口'],['p0179-b016'],2,'保存新标准中数量时间要求不能被价格跳空替代',conditions=['紧邻p0179-b015提出的顶底之间不满足三根K线且有缺口情境'],note='作者直接答复不能成立；未扩大成缺口永远不参与分型。')
add('case-original-top-selection','在2007年9月19日所示图中，应先确定原线段待破坏顶点为1；3还没1高，不是待破坏顶点。5下来破坏1并扩成线段，是标准第一种情况，与3无关。',['线段破坏','笔破坏','特征序列','顶'],['p0180-b001'],1,'保存作者对具体顶点与第一种情况的判断',conditions=['2007-09-19答疑图的1、3、5位置关系','3不及1高','5下来破坏1并延伸成线段'],figures=['p0180-fig1'],note='只按本例作者明确条件记录，不推广为任意图的额外搜索算法。')
add('case-12-56-78-top','对同一图，作者指出1、5、7对应的特征段分别是12、56、78，12、56、78构成顶分型。',['特征序列','顶分型'],['p0180-b004'],1,'保存作者明确列举的特征序列成员',conditions=['2007-09-19同一答疑图','结合原线段待破坏顶点为1的解释'],figures=['p0180-fig1'],note='读者提出的概括规则只作问题语境；本条只保存作者自己列出的三个元素。')
add('case-34-excluded','作者补充，同图3没有新高，对原线段不算一个顶，因此34不看成特征序列元素。',['特征序列','顶','线段'],['p0180-b005'],1,'保存元素排除的明确对象与前提',conditions=['2007-09-19答疑图','3没有新高及原线段顶点1的语境'],figures=['p0180-fig1'],note='原文以笔中顶的取舍作比喻；未归纳为所有历史元素都应删除。')
add('case-top-two-evolutions','2007年9月20日作者把前一日顶分型的后续分为两种：破5日线并延伸出笔，或不破5日线反而上破顶分型；当日开盘由市场给出选择。',['顶分型','笔','均线','完全分类'],['p0180-b011'],3,'保存顶分型并非唯一后续的具体例子',conditions=['2007-09-19顶分型及次日开盘案例'],note='历史5日线不是顶分型完成所有笔的通用必需参数。')
add('case-no-third-sell-observe','在2007年9月20日短线说明中，原1分钟中枢未出现第三类卖点，作者主张继续等市场发展给出后续操作信号。',['第三类卖点','中枢震荡','当下'],['p0181-b001'],3,'保存未发生条件时的当下操作边界',conditions=['2007-09-20该1分钟中枢案例'])
add('case-risk-half-position','在当时危险行情中，对缺乏相应心理和技术者，作者建议半仓等待，或观察5日/5周线并在有效跌破时退出；并自述战略持有、震荡降成本增筹码。',['仓位','市场风险','均线','成本','操作策略'],['p0181-b003','p0181-b004'],3,'保存面向不同能力者的历史风险策略',conditions=['2007-09-20作者判为危险的政策资金博弈行情','缺乏相应心理与技术者适用半仓/均线建议'],note='半仓为当时建议，不是普遍固定仓位。')
add('case-departure-retest-third-buy','2007年9月20日作者说原1分钟已延伸出5分钟中枢，接着观察1分钟离开后回抽能否形成5分钟第三类买点；不能则再次震荡。',['完成','第三类买点','中枢震荡'],['p0181-b010','p0182-b000'],3,'保存案例中等待离开回抽确认的完整次序',conditions=['2007-09-20所述已形成5分钟中枢案例'])
add('accept-current-outcome','作者要求市场参与者准备接受任何走势，关键是有应对各种情况的技术和策略。',['完全分类','当下','操作策略'],['p0182-b001'],2,'保存完整分类与应对的操作态度',conditions=['本课附文对假设突发利空的答复'],note='不是认为任何仓位都能承受任何损失。')
add('calendar-reference-not-signal','关于时间之窗和中秋前后震荡，作者仅视为参考，要求以图形信号看图操作，不把举例视为次日必然上涨预告。',['走势预测','当下','操作策略'],['p0182-b002','p0182-b003'],3,'保存经验参考与操作信号的区别',conditions=['2007-09-20作者对时间之窗/中秋震荡讨论'])
add('rising-selling-falling-buying','作者把“涨了想卖点，跌了想买点”称为正确操作节奏。',['买卖点','操作策略'],['p0182-b004','p0188-b001'],2,'保存面向买卖点的操作顺序',note='“想”不是机械逢涨卖、逢跌买；个股和区间套例子未变成收益保证。')
add('entry-reason-matches-level','作者要求明确买入理由；若打算中线买入，进入点就应是中线买点，而不是在下跌后才追问是否持有。',['操作级别','买点','操作策略'],['p0179-b007','p0179-b008'],2,'保存买入理由与级别一致的要求')
add('class-divergence-prejudge','对当下如何判断线段结束点的提问，作者答可用类背驰判断，同时建议最好不做线段操作，因为尺度太短。',['类背驰','线段','操作级别'],['p0183-b010'],2,'保存提前辅助判断与操作建议',conditions=['紧邻读者关于线段结束点不等后段走远的第一个问题'],note='没有说类背驰即正式确认结束；第二个关于高周期无买点仍最低的问题未答全。')
add('third-buy-path-not-endpoint-only','若次级别回跌过程中次次级别已跌破本级中枢、仅次级别结束端点未跌破，作者答严格说不算第三类买点，但可作为次次级别某买点后的第二买点之类的可操作类型。',['第三类买点','第二类买点','次级别','走势中枢'],['p0183-b016'],1,'保存路径曾跌破与仅终点未破的严格区别',conditions=['紧邻p0183-b015完整假设','次次级别在回跌过程中跌破本级中枢','次级别结束端点未跌破'],note='“第二买点之类”保留非精确归类语气，不强行确认具体哪一类买点。')
add('rotate-after-sell-wait-buy','作者建议散户对股票不抱感情，卖点卖出后等待买点，等待时寻找其他有买点的股票，以提高资金使用效率。',['散户','买卖点','板块轮动','操作策略'],['p0184-b009','p0184-b010'],2,'保存股票池轮动必须以买卖点为条件',conditions=['本课附文对散户股票池和轮动节奏的建议'],note='未据反问计算收益，也未把任意换股说成必然获利。')
add('case-main-funds-both-sides','作者在该次主力博弈附文中反对仅按多空之争理解主力，称强势主力会“多空齐杀”，使单边参与者左右受挫。',['主力资金','市场心理','市场风险'],['p0184-b002'],3,'保存作者对单边思维的风险提醒',conditions=['2007-09-21主力博弈附文的作者判断'],note='“多空齐杀”为原文市场比喻，不声称本项目已实证验证所有主力行为。')
add('case-top-and-average-wait-bottom','在2007年9月21日个股讨论中，作者对已出现顶分型并跌破5日线者，建议等底分型；对未站半年线的所举股票，散户可关注但先操作其他已走好的对象。',['顶分型','底分型','均线','操作策略'],['p0184-b011'],3,'保存组合条件及资金效率的历史例子',conditions=['2007-09-21所述个股情境','已有顶分型并跌破5日线的联合状态'],note='不是任何顶分型都必立即卖，半年线也不是所有买点统一必要条件。')
add('cross-market-price-force','作者在2007年港股直通车文章中反对同公司股票在不同市场必同价的假设，认为可评估的是由各市场众因素合力形成的交易价值。',['市场合力','跨市场交易价值'],['p0185-b002'],3,'保存跨市场价值分析的假设边界',conditions=['2007-09-24同股A/H市场价格讨论'],note='记录作者观点，不当作已验证的套利定理。')
add('equal-float-cap-model','作者提出一个最简单的跨市场交易价值模型：假设同品种在不同市场的总流通市值相等，以各市场价格乘流通量相等进行分析。',['跨市场交易价值','流通量'],['p0185-b003','p0186-b000','p0186-b001'],3,'保存明确模型等式及其假设身份',conditions=['作者提出的最简单模型','同品种跨市场流通总市值相等是建模假设'],note='等式不是已证市场必然；未补原文没有的汇率处理。')
add('case-fivefold-float','在该模型和当时中国人寿数据下，作者以A股流通量仅H股五分之一为例，认为即使A价为H价五倍也不能据此认定不合理。',['跨市场交易价值','流通量'],['p0186-b001'],4,'保存具体数值算例而不泛化价格倍数',conditions=['2007-09-24作者给出的中国人寿流通量比例','采用前述相等流通市值模型'],note='未核实历史数据或当时汇率，不当作当前公司事实。')
add('case-currency-rates-valuation','作者在当时人民币升值、港币挂钩美元且港币利率较高的背景下，认为港币资产保值性弱于人民币资产、所能接受合理市盈率较低，以此解释同品种A/H交易价值差异。',['跨市场交易价值','宏观市场判断'],['p0186-b002'],4,'保存作者跨市场分析中货币和利率的历史条件',conditions=['2007-09-24作者所述人民币升值背景','作者所述当时港币挂钩及两地利率关系'],note='只记录作者当时论述；未验证历史外汇和利率数值，不作当前制度或价格事实。')
add('cross-market-variables-not-car-alone','作者认为直通车本身不能拉平两地价格，除非各项基础市场变量调节到基本相同；即使同一批交易者跨市场交易，价格也可不同。',['跨市场交易价值','交易条件'],['p0186-b003'],3,'保存市场变量与价格差异的条件论述',conditions=['2007-09-24港股直通车讨论'],note='“不可能相同”为作者在本文语境的主张，未扩为所有市场任意时刻不能偶然同价。')
add('float-supply-policy-case','在当时A股蓝筹供应不足讨论中，作者提出增加流通量以降低交易价格和市盈率，并主张完善公开发行比例要求。',['流通量','跨市场交易价值','政策风险'],['p0186-b004','p0186-b006'],4,'保存作者政策方案而不伪装现行法规',conditions=['2007-09-24调控讨论及作者所设模型'],note='本条只保存政策主张；p186-b005对证券法的引述及违法嫌疑未作为本项目已核法律事实。')
add('case-five-center-current-choice','2007年9月24日作者说106开始的5分钟中枢已有1分钟离开；若回抽形成第三类买点可继续发展，也可能扩为30分钟中枢。',['第三类买点','中枢扩展','次级别'],['p0188-b002'],3,'保存该例已发生离开与未确认回抽之别',conditions=['2007-09-24从106开始的5分钟中枢案例'],figures=['p0188-fig1'])
add('new-stroke-vertical-order-case','本课最后例图中，第一绿箭头不成笔，因为顶分型在底分型下面；第二绿箭头按新笔标准成立。',['笔','顶分型','底分型'],['p0188-b004'],2,'保存新笔标准仍须符合顶底相对位置的反例',conditions=['2007-09-24例图第一、第二绿箭头'],figures=['p0188-fig1','p0188-fig2','p0188-fig3'],note='底部两张简图为汇编辅助图，未核制作来源；作者文字与市场图足以保留两个箭头结论，不由辅助图推广额外几何算法。')

# Explicit exclusions and pending boundaries; do not mutate old lesson files.
hold('original-figures',['p0173-b006','p0188-b004'],'本课11个图对象已实际查看；原博客版本和制作身份仍未溯源，数据库unverified保留。p176第二图有嵌入文字说明，p188末两简图制作身份未核；它们不单独证明作者新增规则。')
hold('reader-generalization-boundary',['p0180-b003'],'读者提出一般化的缺口覆盖补充，作者答“很好体现”后具体列12、56、78，并补充排除34。本批只抽取明确本图判断；未把读者整套概括自动发布为作者一般定义。')
hold('second-question-not-answered',['p0183-b009'],'作者只直接回答紧邻第一个线段结束点问题，未完整回答1/5分钟底背驰而30分钟/日线无买点仍最低的第二个问题。')
hold('open-research',['p0175-b004','p0175-b005'],'作者明示自相似结构数量、起始交易条件影响结构生成及不同条件下结构选择等理论研究尚未解决/继续精细化；不补模型答案。')
hold('sep17-second-third-segments',['p0174-b000','p0177-b001'],'9月17日误标后第二、三段的作者答案称在次日图里。已查看p176图与102—105文字，但本单元未将完整局部分笔标成逐笔答案；不把未核细部自绘成作者原图。')

for shorts,cat,reason in [
 (['p0173-b004','p0175-b010','p0177-b004','p0178-b000','p0180-b009','p0184-b000','p0185-b000','p0187-b000'],'transition','课程/附文标题，不单独形成技术命题。'),
 (['p0173-b005','p0173-b008','p0174-b003','p0177-b003','p0177-b005','p0177-b006','p0184-b001','p0184-b003','p0184-b012','p0188-b003'],'transition_or_background','引入、生活事务、字形显示或标号勘误背景；不另造技术命题。'),
 (['p0173-b007'],'quoted_reader_question','正文内引述读者两图问题，不能因role标签为author_body把提问当作者事实。'),
 (['p0173-b013'],'existing_repeat','按定义而非作者个人权威划分，与既有65课明确要求一致。'),
 (['p0174-b002'],'existing_repeat','同软件同精度原则已由68课明确保存；本段物理类比不作为新划分定理。'),
 (['p0175-b011','p0175-b012','p0177-b002','p0178-b001','p0178-b002','p0178-b004','p0178-b005','p0178-b006','p0178-b007','p0178-b011','p0179-b004','p0179-b009','p0179-b012','p0179-b013','p0180-b008','p0181-b002','p0181-b005','p0181-b006','p0181-b007','p0181-b008','p0181-b009','p0182-b008','p0182-b011','p0182-b015','p0183-b002','p0183-b005','p0183-b013','p0184-b002','p0184-b004','p0184-b005','p0184-b006','p0184-b007','p0184-b008','p0185-b001','p0186-b002','p0186-b005','p0186-b007','p0187-b001','p0187-b002','p0188-b000'],'historical_case_or_background','具体2007行情、个股、资金政策、法律/汇率论断或修辞背景，未推广永久规律、当前法律或收益保证。'),
 (['p0178-b003'],'existing_local_case','冲高震荡卖、以1分钟第三卖点为分支的情境方法由p181-b001/p181-b004相邻说明保存；保留本段来源。'),
 (['p0180-b010','p0180-b012','p0181-b000'],'existing_repeat','预测命中仍属概率游戏的论述，已有68课原文明说；此处保留重复来源不造相同命题。'),
 (['p0182-b001-s01'],'speaker_time_header','附文作者时间头，确认相邻文字身份。'),
]:
    for s in shorts:
        if PREFIX+s not in decisions:mark(s,cat,reason)

# Round 3: concept reuse and precise comparisons with reviewed earlier claims.
cross={
 'p0173-b011':['lower-l067-case-two-up-end','lower-l067-standard-feature-sequence'],
 'p0173-b012':['lower-l071-c-stage-diagram-correction-notice'],
 'p0173-b013':['lower-l065-practice-definitions-authority'],
 'p0174-b002':['lower-l068-c-stage-data-source-consistency','lower-l068-c-stage-measurement-scale'],
 'p0177-b008':['lower-l062-stroke-separation','lower-l064-stroke-extra-bar-clarification'],
 'p0179-b000':['lower-l064-precision-software-limits'],
 'p0180-b001':['lower-l071-c-stage-first-break-third-passes-end'],
 'p0183-b010':['lower-l064-preconfirm-not-actual-confirm'],
 'p0183-b016':['upper-l020-third-buy-definition'],
}
for s,ids in cross.items():
    ids=[cid for cid in ids if cid in existing and existing[cid]['review_status']=='reviewed']
    if PREFIX+s not in decisions:mark(s,'technical_new','保存本课新增限定或具体例图，关联既有命题作一致性对照。',ids)
    else:decisions[PREFIX+s]['existing_claim_ids']=ids

# Round 4: all authored atomic statements returned to exact evidence; machine anchors.
sys.path.insert(0,str(BASE.parents[1]/'tools'))
from curation_contract import validate_records,digest
prepared=validate_records(db,KB,[(c,BASE/(NAME+'.jsonl'),i+1) for i,c in enumerate(claims)])
by_passage=defaultdict(list)
for c in claims:
    for e in c['evidence']:by_passage[e['passage_id']].append(c)
ledger=[];unassigned=[]
for pid,p in P.items():
    linked=by_passage[pid];d=decisions.get(pid)
    if p['role']=='reader':d={'category':'reader_context','reason':'读者问题/观点保留作相邻作者回复上下文，不归为作者事实。','existing_claim_ids':[]}
    elif p['role']=='unknown':d={'category':'unverified_heading','reason':'回复标题或未核身份，不提供直接作者命题证据。','existing_claim_ids':[]}
    elif p['text'].startswith('缠中说禅') and len(p['text'])<50 and not linked:d={'category':'speaker_time_header','reason':'作者姓名时间头，确认回复身份，不单独抽取。','existing_claim_ids':[]}
    elif not d and linked:d={'category':'technical_new','reason':'有价值内容已形成所列原子命题；保留作者限定。','existing_claim_ids':[]}
    if not d:unassigned.append((pid,p['text']));continue
    categories=[d['category']]+(['technical_new'] if linked and d['category']!='technical_new' else [])
    ledger.append(dict(passage_id=pid,unit_id=p['unit_id'],document_id=p['document_id'],pdf_page=p['pdf_page'],role=p['role'],speaker=p['speaker'],text_sha256=hashlib.sha256(p['text'].encode()).hexdigest(),categories=categories,reason=d['reason'],new_claim_ids=[c['id'] for c in linked],existing_claim_ids=d['existing_claim_ids'],existing_candidate_claim_ids=candidate_map[pid],candidate_status_changed=False,rounds={
     '1_full_read':{'complete':True,'semantic_focus':'；'.join(c['text'] for c in linked) if linked else d['reason'],'context_kept':True},
     '2_atomic_split':{'complete':True,'claim_ids':[c['id'] for c in linked],'joint_conditions_kept':True,'exclusion_reason':d['reason']},
     '3_normalization':{'complete':True,'concept_labels':sorted({v for c in linked for v in c['concepts']}),'existing_claim_ids':d['existing_claim_ids'],'same_label_not_same_condition':True},
     '4_reverse_evidence':{'complete':True,'exact_quotes_and_coordinates_checked':bool(linked),'semantic_qualifiers_rechecked':bool(linked),'excluded_nonclaims_rechecked':not bool(linked),'figure_origin_boundary_kept':True}},reviewer=REVIEWER))
assert not unassigned,unassigned
def write(suffix,rows):(BASE/(NAME+suffix)).write_text(''.join(json.dumps(v,ensure_ascii=False)+'\n' for v in rows),encoding='utf-8')
write('.jsonl',claims);write('.coverage.jsonl',ledger);write('.pending.jsonl',pending)
newlabels=sorted({v for c in claims for v in c['concepts']}-registry.keys())
write('.concepts.jsonl',[{'id':'concept-'+digest(label),'label':label,'aliases':[],'new_claim_ids':[c['id'] for c in claims if label in c['concepts']]} for label in newlabels])
write('.anchors.jsonl',[{'claim_id':v['record']['id'],'anchors':[{'evidence_id':a['id'],'passage_id':a['passage_id'],'quote':a['quote'],'quote_start':a['begin'],'quote_end':a['end'],'source_spans':[a['span']],'figure_ids':a['figure_ids'],'source_role':a['source_role'],'figure_origins':a['figure_origins']} for a in v['anchors']]} for v in prepared])
figures=[dict(r) for r in db.execute("SELECT * FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 173 AND 188 ORDER BY pdf_page,id")]
write('.figures.jsonl',[{'figure_id':f['id'],'pdf_page':f['pdf_page'],'visual_review_complete':True,'reviewer':REVIEWER,'origin_status':f['origin_status'],'origin_status_changed':False,'note':'实际查看对应页；与作者明确文字核对点号与图示。原博客及制作身份仍未核。'+('本图含嵌入解说或辅助简图，不把该加注本身当作者证言。' if f['id'] in (PREFIX+'p0176-fig2',PREFIX+'p0188-fig2',PREFIX+'p0188-fig3') else ''),'render':str(BASE/'c_stage_l081_visual'/f"p{f['pdf_page']:04d}.png")} for f in figures])
rejected=[]
for slug,shorts,text,why in [
 ('equal-three',['p0173-b009','p0173-b010'],'两图5＝7时也是三段。','作者认可的完整答案将等值明确归为一段。'),
 ('old71-valid',['p0173-b012'],'第71课最后图原样正确。','作者明确说画错7的高度，应低于类似5位置才三段。'),
 ('new-only-count',['p0177-b008'],'任意顶底最高最低K线之间有3根原始K线就必成笔。','删掉包含处理后不得共用K线的首项及先满足首项的前提。'),
 ('old-abolished',['p0179-b000','p0179-b001'],'新笔标准已经废止旧标准。','作者说可以用新标准且本人一直用老标准。'),
 ('fractal-sufficient',['p0175-b006','p0175-b007'],'一有顶分型即确定最终大顶。','把必要条件倒置为充分条件。'),
 ('endpoint-third-buy',['p0183-b016'],'次级别最终端点没跌破，就算途中次次级别跌破也仍是严格第三买点。','作者明确严格说不算，只称可操作类型。'),
 ('cross-market-law',['p0185-b003','p0186-b001'],'跨市场流通总市值恒等是已证市场定律。','作者只提出一个最简单模型假设。'),
]:rejected.append({'id':'lower-l081-c-stage-rejected-'+slug,'lesson_number':81,'status':'rejected_extraction','passage_ids':[PREFIX+s for s in shorts],'proposed_text':text,'reason':why,'formal_status_changed':False,'reviewer':REVIEWER})
write('.rejected.jsonl',rejected)
correction={'lesson_71_evidence':'volume_2-5332cd1b6038-p0094-b002','lesson_71_figure':'volume_2-5332cd1b6038-p0094-fig2','lesson_81_passage':PREFIX+'p0173-b012','new_claim_id':'lower-l081-c-stage-lesson71-last-diagram-correction','exact_quote':P[PREFIX+'p0173-b012']['text'],'author_correction':'类似7的位置应低于类似5的位置，才是三段。','supporting_conditional_answer':'两图5=7或5<7为一段；5>7为三段。','conditional_answer_source':[PREFIX+'p0173-b009',PREFIX+'p0173-b010',PREFIX+'p0173-b011'],'reader_quote_with_author_endorsement':True,'visual_comparison_pages':[94,173],'scope_note':'更正的是该最后示意图的相对高度及三段标记成立条件；不能直接外推任意线段划分的普遍算法。','old_l071_files_modified':False,'old_pending_database_status_changed':False,'remaining_boundary':'原博客图源仍未核；作者明确文字更正已经核清。'}
(BASE/(NAME+'.correction.json')).write_text(json.dumps(correction,ensure_ascii=False,indent=2),encoding='utf-8')
summary={'stage':'C','run_mode':'authorized_new_curation_files_only','schema_version':meta['schema_version'],'graph_version':meta['graph_version'],'reviewer':REVIEWER,'independent_review_claimed':False,'lesson_number':81,'unit_id':'lesson-081','document_id':PREFIX[:-1],'source_filename':'volume_2.pdf','actual_pdf_page_range':[173,188],'passage_count':len(P),'role_counts':Counter(p['role'] for p in P.values()),'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'claims':len(claims),'kind_counts':Counter(c['kind'] for c in claims),'evidence':sum(len(c['evidence']) for c in claims),'importance_counts':Counter(c['importance_level'] for c in claims),'relations':0,'new_concepts':newlabels,'existing_candidates_mapped':len({cid for ids in candidate_map.values() for cid in ids}),'figure_objects_viewed':len(figures),'visual_pages':[94,173,174,176,177,179,180,183,185,187,188],'pending':[p['id'] for p in pending],'rejected_extractions':len(rejected),'lesson71_textual_correction_verified':True,'database_mode':'ro','formal_writes':False,'old_l068_l071_files_modified':False,'imports_run':False,'commit_run':False,'checks_run':['逐段语义四轮审读','图示视觉核对','只读curation_contract字符映射/几何/角色/ID检查'],'machine_checks_pass':True,'semantic_entailment_automatically_proven':False,'visual_interpretation_automatically_proven':False,'acceptance':'部分通过：全188段审读与所列新增命题完成；作者明确第71课更正已核清，原图来源、未答第二问题及理论开放边界仍保留pending。','next_resume_anchor':NAME+'.pending.jsonl','next_action':'主任务复核新批并按当前版本统一只读预检和发布；旧71课pending历史由主任务追加解析记录。'}
(BASE/(NAME+'.summary.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'claims':len(claims),'evidence':summary['evidence'],'coverage':len(ledger),'new_concepts':newlabels,'figure_objects':len(figures),'graph_version':meta['graph_version']},ensure_ascii=False))
