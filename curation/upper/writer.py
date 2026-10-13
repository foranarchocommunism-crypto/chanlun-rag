import sqlite3, json, pathlib, datetime
ROOT=pathlib.Path(__file__).parent
DB=pathlib.Path(r'C:\Users\13240\Desktop\RAG\shared-knowledge\v0.1.0\graph.sqlite')
conn=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
conn.row_factory=sqlite3.Row
def pid(s):
    return s if s.startswith('volume_') else 'volume_1-a53e99c37ca5-p'+s.replace(':','-b')
def passage(s):
    r=conn.execute('select * from passages where id=?',(pid(s),)).fetchone()
    if not r: raise ValueError(s)
    return dict(r)
def claim(slug,text,refs,concepts,conditions=(),exceptions=(),relations=(),note='',quotes=None,kind='explicit',derivation=None,importance=2,importance_reason=''):
    if isinstance(refs,str):refs=[refs]
    ev=[]
    for i,s in enumerate(refs):
        r=passage(s);q=r['text'] if quotes is None else quotes[i]
        assert q and q in r['text'],(slug,s,q)
        ev.append({'passage_id':r['id'],'quote':q})
    d={'id':'upper-'+slug,'text':text,'kind':kind,'conditions':list(conditions),'exceptions':list(exceptions),'concepts':list(concepts),'ambiguity_status':'none','review_note':note or '二次逐段复读：核对作者正文身份、命题主语、级别与完成状态及原文数量限定；本条不依赖配图判断。','evidence':ev,'relations':[{'source':a,'target':b,'type':t} for a,b,t in relations]}
    d['importance_level']=importance
    d['importance_reason']=importance_reason or {1:'基本定义、核心定理或直接影响成立性的关键边界。',2:'用于识别走势、级别或买卖点的主要分析方法与限制。',3:'对主干规则的补充辨析、特殊情形或说明案例。',4:'作者的方法论背景，帮助理解主干规则的研究定位。'}[importance]
    if derivation:d['derivation']=derivation
    return d
def write_batch(name,claims):
    ids=[c['id'] for c in claims];assert len(ids)==len(set(ids))
    dest=ROOT/(name+'.reviewed.jsonl')
    dest.write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in claims),encoding='utf-8')
    print(str(dest),len(claims))
def log_lesson(n,scope,themes,excluded,pending,complete=False,batch=None):
    row={'lesson_number':n,'document_id':'volume_1-a53e99c37ca5','actual_read_scope':scope,'extracted_themes':themes,'excluded':excluded,'pending':pending,'whole_lesson_semantic_read_complete':complete,'batch':batch,'reviewer':'GPT-6.1 Sol xhigh upper','logged_at':datetime.datetime.now().isoformat(timespec='seconds')}
    with (ROOT/'coverage.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
def issue(s,description):
    with (ROOT/'pending.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'passage_id':pid(s),'description':description,'status':'pending'},ensure_ascii=False)+'\n')
