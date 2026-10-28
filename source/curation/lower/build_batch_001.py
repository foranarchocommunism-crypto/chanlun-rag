import json, sqlite3
from pathlib import Path

BASE=Path(__file__).parent
DB=Path(r'C:\Users\13240\Desktop\RAG\shared-knowledge\v0.1.0\graph.sqlite')
con=sqlite3.connect(f'file:{DB.as_posix()}?mode=ro',uri=True)
con.row_factory=sqlite3.Row
P={r['id']:dict(r) for r in con.execute("select * from passages where document_id='volume_2-5332cd1b6038'")}
claims=[]
def add(slug,text,concepts,refs,conditions=(),exceptions=(),relations=(),note=''):
    evidence=[]
    for pid,quote in refs:
        pid='volume_2-5332cd1b6038-'+pid
        assert pid in P,pid
        assert quote in P[pid]['text'],(slug,pid,quote)
        assert P[pid]['speaker']=='缠中说禅',(slug,pid,P[pid]['speaker'])
        evidence.append({'passage_id':pid,'quote':quote})
    claims.append(dict(id='lower-'+slug,text=text,kind='explicit',conditions=list(conditions),exceptions=list(exceptions),concepts=concepts,ambiguity_status='none',review_note=note,evidence=evidence,relations=[dict(source=s,target=t,type=k) for s,t,k in relations]))

N63='复核第63课p8-10正文及其后解盘边界；该段是课程作者正文而非读者问句。二次重读递归定义与显微镜比喻的相邻段，区分理论对象、周期图和实际应用；本命题不依赖配图。'
add('l063-center-recursive-existence','中枢的递归定义解决中枢按级别存在的存在性问题，并提供可操作地寻找中枢的方法。',['中枢','递归定义','级别'],[('p0008-b003','所以，前面关于中枢的递归定义，就是解决这个问题的，是解决存在性问题。也就是说，中枢是可以递归式地定义出来的，而该定义是可操作性的，该定义实际上是如何找出中枢的一种方法，按照这种方法，就肯定能找出定义中的中枢。')],relations=[('中枢','递归定义','defines')],note=N63)
add('l063-chart-period-not-center-level','周期K线图的级别与中枢、走势类型的级别没有必然对应关系；不同周期图相当于不同倍数的显微镜，改变的是观察精细程度。',['周期K线图','中枢','走势类型','级别'],[('p0008-b005','再次强调，什么级别的图和什么级别的中枢没有任何必然关系，走势类型以及中枢就如同显微镜下的观察物，是客观存在的，其存在性由上面所说最原始的递归定义保证，而级别的图，就如同显微镜，不同倍数的看这客观的图就看到不同的精细程度，如此而已。')],relations=[('周期K线图','中枢','distinguishes'),('周期K线图','走势类型','distinguishes')],note=N63)
add('l063-base-chart-recursion','选择1分钟图为最基本图后，可依次定义分型、笔、线段、1分钟中枢和1分钟走势类型，再递归定义更高级别的中枢和走势类型。',['周期K线图','分型','笔','线段','中枢','走势类型','递归定义'],[('p0008-b006','如果我们首先确立了显微镜的倍数，也就是说，例如我们把1分钟图作为最基本的图，那么就可以开始定义上一课程说的分型、笔、线段等等。有了线段，就可以定义1分钟的中枢，然后就是1分钟的走势类型，然后按照递归的方法，可以逐步定义5分钟、30分钟、日、周、月、季度、年的中枢和走势类型。')],conditions=['以1分钟图作为最基本图'],relations=[('中枢','线段','requires'),('走势类型','中枢','requires'),('递归定义','级别','related')],note=N63+'这里保留“例如”的选图前提，不把所有1分钟图上的线段直接等同于固定客观级别。')
add('l063-base-chart-choice','也可以选择5分钟或30分钟图作为最基本图，其分析方法与选1分钟图相同，只是观察较粗糙；已选择1分钟为最基本图时，可在1分钟图上进行分析。',['周期K线图','级别'],[('p0008-b006','如果你选择5分钟或30分钟为最基本的图，那么和1分钟的看法一样，只不过你的显微镜倍数比较小，看起来比较粗糙而已。而如果你已经选择1分钟作为最基本的图，也就是选定了1分钟这个倍数的显微镜，那么看1分钟图就可以')],conditions=['明确选择最基本图的周期'],relations=[('周期K线图','级别','qualifies')],note=N63)
add('l063-completed-types-higher-chart-memory','将已完成的次级别走势类型记在较大周期图上，可以帮助记忆，并直观显示较高级别中枢和走势类型的形成。',['走势类型','周期K线图','中枢'],[('p0008-b007','例如走出一个1分钟的走势类型，已经完成了，就可以在5分钟图上相应记号'),('p0009-b000','上，这样的一个好处就是帮助记忆'),('p0009-b001','在大级别图上记号次级别的走势类型有一个好处，就是能让你清晰地看到该级别的中枢和走势类型是如何形成的，这样会更直观。')],conditions=['记号对象是已经完成的走势类型'],relations=[('周期K线图','走势类型','illustrates'),('周期K线图','中枢','illustrates')],note=N63+'已补齐p8-b007到p9-b000的跨页续句；不将记号习惯误写为图周期与走势级别的定义。')
add('l063-macd-higher-chart-convenience','用较大周期图的MACD辅助判断，是为避免对小周期图上过多柱子面积逐一相加；理论上的小周期等效处理在软件参数上限下可能不可行。',['MACD','背驰','周期K线图'],[('p0009-b000','另外一个好处就是看MACD辅助判断时，不用对太多的柱子面积进行相加，可以看大级别的MACD图，这样一目了然。'),('p0009-b000','如果用1分钟的MACD把参数调到足够大，效果其实是一样的，而实际上不可能，一般软件上，MACD的参数有上限限制，所以实际上也限制了日线的背驰不能用1分钟的图解决。')],conditions=['MACD仅作为辅助判断工具','受实际软件参数上限约束'],relations=[('MACD','背驰','related'),('周期K线图','MACD','qualifies')],note=N63+'二次检查本段“理论”与“实际上”的区别，保留辅助地位和软件限制。')
add('l063-operation-selected-level','在较大周期图粗略选定对象后，应选好基本观察图进行精细跟踪，定位符合自己操作级别的买点，并按相应级别操作。',['操作级别','买点','周期K线图'],[('p0010-b001','在大级别图粗略选定攻击目标后，就要选好显微镜，进行精细的跟踪分析，然后定位好符合自己操作级别的买点建仓，按照相应的操作级别进行操作')],conditions=['操作级别事先确定'],relations=[('买点','操作级别','qualifies')],note=N63+'排除同页后段具体指数解盘；本句仍位于课程正文。')

N72='复核第72课p102-b008至p105-b005课程正文，排除p105-b006起另日加息和大盘文章。二次重读形态学/动力学分类与前提段，保留作者自述的理论范围；本命题不依赖配图。'
add('l072-morphology-dynamics','作者将其理论分为形态学、动力学及二者结合；背驰、类背驰判别和第一类买卖点的讲授涉及动力学。',['形态学','动力学','背驰','第一类买卖点'],[('p0103-b004','本ID的理论，本质上分两部分，一是形态学，二是动力学，当然三就是两者的结合。'),('p0103-b004','但如果不说动力学，那至少背驰是没法讲了，然后中枢震荡也不可能用类背驰的方法去判别，第一类买卖点也无法说了。')],relations=[('背驰','动力学','related'),('第一类买卖点','动力学','requires')],note=N72)
add('l072-morphology-geometric-scope','形态学本质上是几何；作者此前提出的理论前提主要针对动力学部分，不针对形态学部分。',['形态学','动力学'],[('p0103-b006','形态学，从本质上就是几何，这部分内容，是无须任何前提的。以前说的本ID理论成立的前提，其实并不是针对这部分的，主要是针对动力学部分。')],relations=[('形态学','动力学','distinguishes')],note=N72+'“无须任何前提”仅按作者给出的形态学相对于市场动力学前提的范围表述。')
add('l072-dynamics-premises','动力学部分要求价格充分有效市场和非完全绝对趋同交易这两个前提。',['动力学','价格充分有效市场','非完全绝对趋同交易'],[('p0103-b006','而动力学方面的东西就不同了，必须有本ID要求的那两个前提：价格充分有效市场里的非完全绝对趋同交易。')],conditions=['讨论动力学部分'],relations=[('动力学','价格充分有效市场','requires'),('动力学','非完全绝对趋同交易','requires')],note=N72)
add('l072-dynamics-energy-and-divergence','涉及背驰、中枢与走势能量结构的内容属于动力学；中枢、走势类型、笔、线段等几何结构属于形态学。',['动力学','形态学','背驰','中枢','走势类型','笔','线段','能量结构'],[('p0104-b003','任何涉及背驰的，都是动力学的范围，背驰是动力学的基本点之一。另外，中枢、走势的能量结构之类的东西，也属于动力学。而形态学，就是中枢、走势类型、笔、线段之类的东西。')],relations=[('动力学','背驰','composed_of'),('动力学','能量结构','composed_of'),('形态学','中枢','composed_of'),('形态学','走势类型','composed_of'),('形态学','笔','composed_of'),('形态学','线段','composed_of')],note=N72+'二次检查顿号和句义：前句中枢/走势的“能量结构”归动力学，中枢几何本身归形态学，不混为同一层。')
add('l072-morphology-second-not-first','单用形态学可形成操作体系；由于不含背驰概念，不能据此抓第一类买卖点，但可以处理第二类买卖点。',['形态学','背驰','第一类买卖点','第二类买卖点'],[('p0104-b004','其实，光用形态学，就足以形成一套有效的操作体系。只是在形态学中，由于没有背驰的概念，所以第一买卖点是抓不住了，但第二买卖点是肯定没问题的。')],conditions=['只用形态学、没有引入背驰概念'],relations=[('第一类买卖点','背驰','requires'),('形态学','第二类买卖点','related')],note=N72)
add('l072-morphology-operation-segment','只用形态学操作时，对最后一个中枢回拉后，第一个与回拉反向、不创新高或新低的中枢同级别离开，被作者称为买卖段。',['形态学','中枢','买卖段','级别'],[('p0104-b004','单纯用形态学去操作，就是任何对最后一个中枢的回拉后第一个与回拉反向的不创新高或新低的中枢同级别离开，就是买卖段。')],conditions=['只用形态学','相对于最后一个中枢的回拉','回拉后的第一次反向离开','离开与中枢同级别','不创新高或新低'],relations=[('买卖段','中枢','requires'),('买卖段','级别','qualifies')],note=N72+'逐项复核原句限定词“最后”“第一个”“反向”“不创新高或新低”“同级别”，未替换为未经原文给出的买卖点编号。')
add('l072-morphology-learning-chain','作者给出的形态学基本学习路线为分型、笔、线段、最小级别中枢，再到各级别中枢和走势类型。',['形态学','分型','笔','线段','最小级别中枢','中枢','走势类型'],[('p0104-b010','分型-笔-线段-最小级别中枢-各级别中枢、走势类型'),('p0104-b011','上面几个东西，是形态学中最基本的，完全没有办法再简略了')],relations=[('笔','分型','requires'),('线段','笔','requires'),('最小级别中枢','线段','requires'),('中枢','最小级别中枢','related')],note=N72+'重读p104-b008区分最小级别构造与理论递归定义，不把教学路线当成消除该区别。')
add('l072-center-makes-types-strict','早期以高低点描述上涨、盘整是引入中枢前的不严格说法；引入中枢后才可给出严格定义。',['中枢','上涨','盘整','走势类型'],[('p0105-b001','最开始时，说上涨、盘整，都是用高、低点之类的东西，因为当时没说中枢，所以不可能严格定义，后来说了中枢，就可以给出严格定义。')],relations=[('上涨','中枢','requires'),('盘整','中枢','requires')],note=N72+'保留课程概念逐步严格化的历史关系，不以日期自动覆盖全部早期表述。')
add('l072-l067-explicit-refinement','作者明确说明第64课部分线段论述尚不严格，第67课引入特征序列后进行了精确化；此后的线段划分以该精确定义为基础。',['线段','特征序列','线段破坏'],[('p0105-b002','64课里，由于没说特征序列的元素之类的概念，所以里面关于线段一些论述都如同用高、低点定义上涨、盘整一样，不太严格，到67课说了特征序列之类的东西后，定义就是严格的'),('p0105-b002','以后关于线段的划分，都以此精确的定义为基础。')],conditions=['针对第64课与第67课线段定义的明确自述'],relations=[('线段','特征序列','requires'),('特征序列','线段破坏','qualifies')],note=N72+'跨课关联为作者本段明确点名，不是按发文时间自动推断修订；第67课细则仍另行审读。')
add('l072-feature-sequence-removes-small-to-large','作者说明，引入特征序列后，线段层次不再需要沿用类似小级别转大级别的不确定情况，从而可精确划分线段。',['线段','特征序列','小级别转大级别'],[('p0105-b003','按照原来没有特征序列的定义，那么线段里都要继续存在类似小级别转大级别的情况，而有了特征序列后，就不再需要这种情况了，这样才能把线段给精确划分。')],conditions=['讨论线段层次的精确划分'],relations=[('特征序列','线段','qualifies'),('线段','小级别转大级别','distinguishes')],note=N72)

importance={
 'l063-center-recursive-existence':(1,'中枢递归定义的存在性和可操作性是级别体系基础。'),
 'l063-chart-period-not-center-level':(1,'区分图周期与走势级别是防止整个中枢体系误用的关键边界。'),
 'l063-base-chart-recursion':(1,'说明从基础图到中枢、走势类型及高一级递归的基础构造链。'),
 'l063-base-chart-choice':(2,'规定实际选图方法及观察精度限制。'),
 'l063-completed-types-higher-chart-memory':(3,'补充较大周期图的记忆和显示用途。'),
 'l063-macd-higher-chart-convenience':(3,'澄清MACD跨周期使用的便利性和软件限制。'),
 'l063-operation-selected-level':(2,'将买点和操作明确约束到既定操作级别。'),
 'l072-morphology-dynamics':(1,'划分理论的两大范围并定位背驰与第一类买卖点。'),
 'l072-morphology-geometric-scope':(1,'明确理论前提的适用范围，避免将动力学前提套到形态学。'),
 'l072-dynamics-premises':(1,'动力学适用的必要前提与其核心结论同级。'),
 'l072-dynamics-energy-and-divergence':(1,'给出形态学结构和动力学能量内容的基础分类边界。'),
 'l072-morphology-second-not-first':(2,'界定单用形态学操作所能处理的买卖点范围。'),
 'l072-morphology-operation-segment':(2,'给出仅用形态学寻找买卖段的完整条件。'),
 'l072-morphology-learning-chain':(2,'提供最基本形态分析和学习的构造顺序。'),
 'l072-center-makes-types-strict':(3,'说明早期高低点描述和严格中枢定义的教学关联。'),
 'l072-l067-explicit-refinement':(1,'作者明确指定线段划分的精确定义依据，是跨课规范冲突的关键边界。'),
 'l072-feature-sequence-removes-small-to-large':(1,'界定精确线段体系与小级别转大级别情形的关键关系。'),
}
for claim in claims:
    level,reason=importance[claim['id'].removeprefix('lower-')]
    claim['importance_level']=level
    claim['importance_reason']=reason+'该分级为整理判断。'
target=BASE/'batch_001_pilot_levels.jsonl'
with target.open('w',encoding='utf-8',newline='\n') as f:
    for claim in claims:f.write(json.dumps(claim,ensure_ascii=False)+'\n')
print(json.dumps({'path':str(target),'claims':len(claims),'evidence':sum(len(c['evidence']) for c in claims)},ensure_ascii=False))
