"""Materialize the main agent's four-pass reading of lesson34.

This writes curation artifacts only; the source DB remains read-only.
"""
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
OUT = Path(__file__).resolve().parent
DOC = 'volume_1-a53e99c37ca5'
BASE = 'c_stage_l034'
REVIEWER = 'Codex 主代理 / 阶段C上册34课同模型四轮复核'
SOURCE_SHA = '3a58979f142d5528cd4a9282991ef4f3c371a130e81d5b66604aa53e00ad7b8e'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-034' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 37
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 256 AND 258 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 5
rows, pending, notes = [], [], {}
quote_overrides = {}
retained = defaultdict(list)


def pid(short):
    page, block = short.split('-', 1)
    return f'{DOC}-p{int(page):04d}-{block}'


def c(lesson, slug, shorts, text, labels, level, check, conditions=(), exceptions=(), figs=(), ambiguity='none'):
    citations = []
    for i, short in enumerate(shorts.split()):
        p = passages[pid(short)]
        # A date heading extracted at the previous paragraph's tail belongs to
        # the following paragraph; preserve source text, but don't cite that tail.
        quote = quote_overrides.get(short, re.sub(r'(?:\*+)?200[678]-\d{2}-\d{2}\d{2}:\d{2}:\d{2}$', '', p['text']).rstrip('*'))
        citations.append({'passage_id': p['id'], 'quote': quote, 'quote_start': p['text'].index(quote),
                          'figure_ids': [f'{DOC}-p{n:04d}-fig{k}' for n, k in figs] if i == 0 else []})
    cid = f'upper-l{lesson:03d}-c-stage-{slug}'
    assert cid not in old and cid not in {r['id'] for r in rows}, cid
    ps = [passages[e['passage_id']] for e in citations]
    assert all(p['speaker'] == '缠中说禅' and p['role'] in ('author_body', 'author_reply', 'author_commentary') for p in ps)
    labels = list(dict.fromkeys(canonical.get(x, x) for x in labels.split('|')))
    reasons = {1: '基础核心：定义及不能省略的条件。', 2: '主要方法：影响识别与操作选择。',
               3: '补充深化：方法适用边界。', 4: '背景细节：作者历史判断或经验自述。'}
    context = '；'.join(f"PDF{p['pdf_page']} {p['role']} {p['published_at'] or '未记单独时间'}" for p in ps)
    applicable = '；'.join(conditions) if conditions else '本条陈述的对象、级别、完成状态与所引原段语境；' + check
    row = {'id': cid, 'text': text, 'kind': 'explicit', 'conditions': list(conditions), 'exceptions': list(exceptions),
           'concepts': labels, 'ambiguity_status': ambiguity,
           'review_note': f'语境：第{lesson}课；{context}。适用条件：{applicable}。四轮：通读全部段落并核对实际页面；拆分原子命题与联合条件；比对既有概念及跨课范围；回查证据、量词、时序和配图。{check}。同一主代理四轮，不称独立复核；固定汇编边界，未核原博客。',
           'importance_level': level, 'importance_reason': reasons[level] + check,
           'reviewer': REVIEWER, 'evidence': citations, 'relations': []}
    if figs:
        assert citations[0]['figure_ids'] == [f'{DOC}-p{n:04d}-fig{k}' for n, k in figs]
        row['figure_review_note'] = '主代理实际查看原页、整图和插图右端：' + '；'.join(f['note'] for f in figures if f['id'] in citations[0]['figure_ids']) + '。配图有后加整理版及来源未核图，制作者未核，不作为作者观点唯一证明，文字独立支持命题。'
    rows.append(row)
    return cid


def note(shorts, category, reading, reverse):
    for s in shorts.split():
        assert pid(s) in passages, s
        notes[pid(s)] = {'category': category, 'reading': reading, 'inverse': reverse}


def keep(shorts, ids, reason):
    for short in shorts.split():
        for id in ids.split():
            assert id in old, id
            retained[pid(short)].append(id)
    note(shorts, 'existing_claim_retained', reason, '保留跨课线索；旧命题及旧证据不改。' + reason)


def issue(slug, shorts, description, action, blocker=False):
    pending.append({'id': 'upper-l034-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})








c(34, 'emotion-program-puppet-and-gambling-view', '255-b001',
  '作者用傀儡与自动程序比喻受预设情绪操控，认为先把市场当赌场会使观察、认识、学习和操作都受这种想象限制。',
  '市场心理|操作熟练程度|操作策略', 3, '这是作者对投资认知的批评和比喻，未做心理实验；面首/怨男为原文人物隐喻，不作为真实身份分类或群体事实。')
c(34, 'four-zheng-means-current-not-claimed-correct', '255-b002',
  '作者把正闻、正见、正学、正行合称四正，并特意说“正”不是名言上自称正确，而是当下；股市里的闻见学行应依当下走势。',
  '正闻正见正学正行|当下|市场心理|操作熟练程度', 1, '限定本课作者对正字的释义，不扩为所有思想史语境或道德判决；四正不构成可测收益合格证。')
c(34, 'all-secrets-in-current-path-author-view', '255-b002',
  '作者强调在当下走势中磨练、化解情绪，称走势公开呈现一切股市秘密，不必向外求。',
  '当下|市场心理|技术分析', 3, '一切秘密皆在其中是作者强理念，不证明价格全反映信息或基本面永远无用，前30/32结合其他因素的范围另保留。', ambiguity='author_all_information_in_path_rhetoric_not_empirical_proof')
c(34, 'percentage-loss-not-proven-equal-ruin-probability', '255-b003',
  '作者强调损失按百分比，并进一步声称无论资金从何处涨来、在任何位置归零几率都一样，以此要求警觉。',
  '资金管理|市场风险|成本', 3, '相同比例损失与任意位置同归零概率是不同断言，后者没有模型或样本，本项目只记录作者主张，不当已证概率定理。', ambiguity='percentage_loss_and_equal_ruin_probability_not_equivalent_or_verified')
c(34, 'current-level-by-capital-and-tolerance-not-second', '255-b003',
  '作者说当下并非每秒变化，而应按资金及承受能力选择操作级别；例如选30分，就观察相应30分实际走势。',
  '当下|操作级别|资金管理|操作熟练程度', 1, '承受能力和级别选择未给统一金额阈值，不把一秒行情反向等同选定级别逆势。')
c(34, 'exit-when-chosen-level-actual-path-opposes-operation', '255-b003',
  '作者要求一旦已有操作与所选级别实际当下走势相反，就尽快退出，例为30分操作逆于30分当下走势。',
  '操作级别|当下|确认|操作策略|市场风险', 1, '所选级别相反是条件，原文未在此给定量判定或通道成交保证；与某次更低级柱缩不同，尽快不等必能无损或卖在极值。',
  ['已有操作与事先选择级别的实际当下走势相反'])
c(34, 'beast-reflex-after-danger-no-emotional-shadow', '255-b004 256-b000',
  '作者把上述退出称为并非其所说的“止蚀”，而是野兽般识险反应；危险过去后可重新寻找机会，不把先前事件变成情绪阴影。',
  '市场心理|操作熟练程度|操作策略|当下', 2, '野兽直觉在危险前是作者理想化比喻，不保证交易者可预知所有突发风险，也不能推出禁止一切实际风险止损。')
c(34, 'mar7-index-levels-observe-not-commentator-following', '256-b001 257-b000',
  '3月7日作者要求把指数在2888与2915下震荡用作培养当下判断的案例，综合1、5、15、30、60分观察，而非跟随作者股评。',
  '当下|操作级别|走势中枢|技术分析', 2, '这些是观察图周期及相应结构，非所有周期恰有同名严格中枢；后图未来走势不证明作者当日已知。',
  ['2007年3月7日15:12:14指数解盘'], figs=[(256, 1), (256, 2), (257, 1)])
c(34, 'mar7-2915-stable-third-buy-or-two-range-shapes', '257-b001',
  '作者说未有效站稳2915并最终形成三买，就不能摆脱下方中枢；列2915附近回跌乃至破底之字型，或先上3000再回拉平台型两支。',
  '第三类买点|确认|走势中枢|平台式调整|走势预测', 1, '站稳和三买是联合要求，未来两支不等都已发生，不把2915普遍当中枢ZG或一过该价就确认脱离。',
  ['2007年3月7日指数当时结构'], figs=[(257, 1)], ambiguity='dated_conditional_zigzag_or_platform_paths')
c(34, 'mar8-five-retest-not-back-2858-thirty-third-buy', '257-b003',
  '3月8日作者将前尾盘至当晨的5分回试不回2858原30分中枢判为三买；2915尾盘突破仍须确认。',
  '第三类买点|次级别|走势中枢|确认|操作级别', 1, '原30分中枢与5分回试层级分开，2858为该例文字口径不代替全书定义；三买已判与压力突破尚待确认是不同对象。',
  ['2007年3月8日15:30:24作者具体例'], figs=[(257, 2), (258, 1)])
c(34, 'mar8-can-return-five-and-expand-new-thirty', '258-b000',
  '作者同时保留重新跌回5分中枢并扩为新30分中枢的可能，称2915不能被有效跌破，否则走势会变复杂。',
  '中枢扩展|走势中枢|确认|走势预测', 1, '已存在原30分与未来可能新30分不是同一对象；三买之后仍有演化，不把作者可能/有效破坏条件改为此时已扩展。',
  ['2007年3月8日当时指数结构'], figs=[(257, 2), (258, 1)], ambiguity='dated_future_reentry_and_new_thirty_center_not_confirmed')
c(34, 'rotation-no-chase-but-five-main-rise-not-all-small-exits', '258-b001 259-b002',
  '作者要求板块轮动中买点买、不追高，也不要过短：若5分仍主升，见每个1分以下背驰就跑可能错过较大上涨，应综合判断；动过板块可等调整再观察。',
  '板块轮动|追高|操作级别|背驰|操作策略', 1, '5分主升是小信号用途限制，非所有小背驰都没用；板块还会动/利润吃不到是作者当时经验，不保证持仓必涨。')
c(34, 'front-is-back-not-short-reply-referent-unclear', '258-b006',
  '对读者同时问AB是否中枢及a+A+b、b+B+c是否中枢，作者仅答“前面是，后面不是”。',
  '走势中枢|走势分解|确认', 3, '多项问句与前后短答不能唯一配对，不能据此建立a+A+b为中枢或b+B+c必非中枢的无条件规则；必须保留原问题上下文。',
  ['相邻悠悠悠哉复合问句的原指代范围'], ambiguity='short_reply_multiple_question_referents_unresolved')
c(34, 'third-buy-confirm-look-inside-sublevel', '258-b009',
  '对三买回抽如何确认不破中枢，作者要求看次级内部走势，并说与此前判断离开力度不足的方法相同。',
  '第三类买点|次级别|中枢回拉作用|确认', 1, '没有认可读者2871/2888全部标注、半仓操作或给出固定等几根K的确认算法；具体力度口径仍需上课范围。')
c(34, 'a-plus-b-plus-b-area-sum-not-maximum-bar', '259-b007',
  '作者从原文a+B+b角度解释该例力度比较，应算柱子面积而非单根最长柱，建议在5分图观察。',
  'MACD|MACD柱波|中枢回拉作用|指标对比', 1, '原a+B+b大小写和次序保留，不静改a+A+b；本例面积优于峰高并不废33一般黄白线/多级配套，也未给统一积分算法。')
c(34, 'five-center-formed-prior-close-later-pull-and-gap-oscillate', '259-b007',
  '同一答复从纯中枢角度说5分中枢在前一天尾盘已形成，之后拉起和次晨跳动均属围绕中枢震荡。',
  '走势中枢|中枢震荡|完成|操作级别', 1, '不将读者“两1分中枢重叠就是5分盘整”的完整推断当作者认可，也不以早上波动重新确认前晚尚未形成。')

keep('255-b003', 'upper-l031-c-stage-proportional-loss-and-no-desperate-position upper-l030-c-stage-entered-divergence-leg-can-break-and-reassess',
     '34百分比风险警示与当下重估相应，任意位置同归零概率仍无证明，选定级别而非每秒噪音。')
keep('257-b001 257-b003 258-b000', 'upper-l032-c-stage-2915-is-gg-not-center-top-2894-correction upper-l033-c-stage-third-buy-center-edge-versus-swing-high-strongest',
     '2915继续为该例参照，原30分2858与新5分/可能30分要分层，不能回改GG/ZG区分或将过压线等同三买。')
keep('258-b001', 'upper-l031-c-stage-099-five-main-fall-even-one-divergence-wait-parent upper-l033-c-stage-subminute-pull-important-under-five-thirty-center',
     '5分主升下小信号不必全退出，与中枢回拉下次1可重要是不同阶段，不能作所有小背驰通用判断。')
keep('258-b009', 'upper-l032-c-stage-third-buy-retest-at-least-sublevel-three-down-up-down',
     '34继续要求看次级内部而非一根回抽不破的猜测；读者价点不是额外作者确认。')
keep('259-b007', 'upper-l033-c-stage-macd-lines-generally-area-complex-multilevel-first',
     '34具体a+B+b用面积非最长柱，33一般黄白/复杂面积/多级优先范围分别保留，不自动以较晚一答改全局优先级。')

issue('emotional-metaphors-four-zheng-and-equal-ruin-claim', '254-b003 254-b004 255-b000 255-b001 255-b002 255-b003 255-b004 256-b000',
      '人物/高校/性别泛化只作作者历史修辞，四正的正为本课当下释义；按比例损失不证明任何位置同归零概率，野兽预知危险不构成零风险方法。',
      '不将作者情绪评价升级为群体事实/心理诊断，概率断言无样本就保留未核，四正不等保证正确交易。')
issue('chosen-level-exit-not-second-noise-or-perfect-execution', '255-b003 255-b004 258-b001',
      '当下按资金承受所选级别，反向尽快退出未给具体量化判定或可成交保证；不是止蚀的比喻不能解成禁止所有止损。',
      '30分操作与次1信号分开，接后文具体级别完成标准；不补预知突发风险、无损退出或固定秒级触发器。', True)
issue('dated-2915-third-buy-confirmation-and-new-center', '256-b001 257-b001 257-b003 258-b000',
      '3/7双盘整分支与3/8已判三买、2915突破待确认和可能回5分扩新30分要分对象；旧30分2858并非新5分框。',
      '保留有效/最终/可能及各层级，图未来到3/9—20不能抹当时不确定，也不把2915当严格ZG。', True)
issue('short-front-back-answer-ambiguous', '258-b005 258-b006',
      '问题含AB是中枢及a+A+b/b+B+c是否中枢，前面是后面不是的指代不唯一；只有短答不能支持任一组合的裸定义。',
      '原问题/短答并存，默认只返回确证的作者答句及歧义；后35定义可作范围补充，不能事后捏造这句唯一语法指代。', True)
issue('area-versus-peak-and-center-formed-state', '258-b009 259-b004 259-b005 259-b006 259-b007',
      'a+B+b为原记号，本例用柱面积不是最长柱；前晚5分中枢已形成与读者两1分中心拼法不是同一断言，面积/黄白全局优先级未被重写。',
      '与33的多级配套一起读，保留具体对象与原大小写，不能由面积小一项补完整三买/背驰算法。', True)
issue('cross-day-date-later-figures-and-historical-context', '257-b002 257-b003 258-b000 258-b001 258-b002 259-b002',
      '5解盘段原继承3/7现改3/8，本课5图全晚于原文，PDF254前课图只核边界；板块/传媒平台自述未核。',
      '源原文/映射/坐标不动，不以后图和作者自评认证实际收益、行为或预测。')

note('254-b003 254-b004 255-b000', 'historical-literary-and-personal-metaphor-context',
     '开篇以文学人物、人物类型及高校男性对比展开投资受情绪支配的隐喻，原文完整已读并保留。',
     '不把贬损性比喻、身份泛化和历史人物影射作为可核心理分类或群体事实；不额外猜未具名王某身份。')
note('258-b002', 'historical-media-platform-self-report', '作者构建传媒平台、引导舆论的自述已读。', '未核平台身份、实际动作或政治标签，不由来源指令触发对外发言或操作。')

relations = {
    'upper-l034-c-stage-four-zheng-means-current-not-claimed-correct': [('正闻正见正学正行', '当下', 'defines')],
    'upper-l034-c-stage-current-level-by-capital-and-tolerance-not-second': [('当下', '操作级别', 'qualifies')],
    'upper-l034-c-stage-exit-when-chosen-level-actual-path-opposes-operation': [('操作策略', '操作级别', 'qualifies')],
    'upper-l034-c-stage-third-buy-confirm-look-inside-sublevel': [('第三类买点', '中枢回拉作用', 'qualifies')],
    'upper-l034-c-stage-a-plus-b-plus-b-area-sum-not-maximum-bar': [('MACD柱波', '指标对比', 'qualifies')],
}

for r in rows:
    r['relations'] = [{'source': a, 'target': b, 'type': t} for a, b, t in relations.get(r['id'], [])]
by_passage = defaultdict(list)
for r in rows:
    for e in r['evidence']:
        by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers'] = sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('embedded-dates-and-figure-provenance'):
        item['figure_ids'] = [f['id'] for f in figures]
ledger = []
for id, p in passages.items():
    linked, decision = by_passage[id], notes.get(id)
    if linked:
        result, reading = 'new_claim', '；'.join(r['text'] for r in linked)
        atomic = [{'claim_id': r['id'], 'conditions': r['conditions'], 'exceptions': r['exceptions']} for r in linked]
        inverse = '；'.join(r['review_note'] for r in linked)
    elif decision:
        result, reading, atomic, inverse = decision['category'], decision['reading'], [], decision['inverse']
    elif p['role'] == 'reader':
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者AB及两组合是否中枢的复合问句、2871/2888半仓与两1分中枢重叠的分析仍是读者，作者短答/具体解释不扩大成全部认可。'
    elif p['text'].startswith('教你炒股票') or p['text'] in ('缠中说禅解盘:', '缠中说禅解盘：', '缠中说禅回复:', '缠中说禅回复：') or re.fullmatch(r'.*200[5678]-\d{1,2}-\d{1,2}.*', p['text']) and (len(p['text']) < 75 or p['text'].startswith('缠中说禅')):
        result, reading, atomic, inverse = 'source_header', '课程、解盘/回复的作者署名与时间头已核。', [], '只作来源身份锚点，不独立支持技术结论。'
    else:
        raise AssertionError(('unaccounted paragraph', id, p['text']))
    if linked and decision:
        reading += '；其余语境：' + decision['reading']; inverse += '；' + decision['inverse']
    ledger.append({'passage_id': id, 'lesson_number': int(p['unit_id'].split('-')[1]), 'document_id': DOC,
      'pdf_page': p['pdf_page'], 'role': p['role'], 'speaker': p['speaker'], 'published_at': p['published_at'],
      'source_text_sha256': hashlib.sha256(p['text'].encode()).hexdigest(), 'result': result, 'claim_ids': [r['id'] for r in linked],
      'related_existing_claim_ids': retained[id], 'existing_evidence_not_mutated': True,
      'pending_issue_ids': [x['id'] for x in pending if id in x['passage_ids']], 'reviewer': REVIEWER,
      'rounds': {'1_read_and_scope': reading, '2_atomic_conditions': atomic,
        '3_normalization': {'concept_labels': sorted({x for r in linked for x in r['concepts']}), 'related_existing_claim_ids': retained[id],
        'note': '情绪/四正和等归零概率是作者理念或未核主张；当下按选定级别非秒噪音，三买已出现不等2915突破已确认；前后简答指代未解，面积和非单根最长柱。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='本课5图全部查看且均为文后行情；254前课图仅边界核对不重复改，3/9—3/20未来K不抹3/7与3/8的尚需确认和扩展可能。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 37 and Counter(x['lesson_number'] for x in ledger) == {34: 37}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [34], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(254, 260)), 'figure_objects_viewed': 5, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '34课37段6页5本课图及前课边界同模型四轮；5跨日日期修正，四正/选定级别退出、三买与突破确认/扩展可能、简答指代和面积范围分开，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


