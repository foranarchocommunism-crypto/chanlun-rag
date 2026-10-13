import json,sqlite3
from pathlib import Path
BASE=Path(__file__).parent
DB=Path(r'C:\Users\13240\Desktop\RAG\shared-knowledge\v0.1.0\graph.sqlite')
con=sqlite3.connect(f'file:{DB.as_posix()}?mode=ro',uri=True)
con.row_factory=sqlite3.Row
P={r['id']:dict(r) for r in con.execute("select * from passages where document_id='volume_2-5332cd1b6038'")}
claims=[]
def add(slug,text,concepts,refs,level,reason,conditions=(),exceptions=(),relations=(),note='',figures=(),figure_review_note=''):
    evidence=[]
    for item in refs:
        pid=item[0] if isinstance(item,tuple) else item
        pid='volume_2-5332cd1b6038-'+pid
        quote=item[1] if isinstance(item,tuple) else P[pid]['text']
        assert quote in P[pid]['text'],(slug,pid,quote)
        assert P[pid]['role'].startswith('author_'),(slug,pid,P[pid]['role'],P[pid]['speaker'])
        e={'passage_id':pid,'quote':quote}
        if figures:e['figure_ids']=['volume_2-5332cd1b6038-'+f for f in figures]
        evidence.append(e)
    claim=dict(id='lower-'+slug,text=text,kind='explicit',conditions=list(conditions),exceptions=list(exceptions),concepts=concepts,ambiguity_status='none',review_note=note,evidence=evidence,relations=[dict(source=s,target=t,type=k) for s,t,k in relations],importance_level=level,importance_reason=reason+'该分级为整理判断。')
    if figure_review_note:claim['figure_review_note']=figure_review_note
    claims.append(claim)
def save(name):
    target=BASE/name
    with target.open('w',encoding='utf-8',newline='\n') as f:
        for c in claims:f.write(json.dumps(c,ensure_ascii=False)+'\n')
    print(json.dumps({'path':str(target),'claims':len(claims),'evidence':sum(len(c['evidence']) for c in claims)},ensure_ascii=False))
def log(obj):
    with (BASE/'coverage.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(obj,ensure_ascii=False)+'\n')
def pending(obj):
    with (BASE/'pending.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(obj,ensure_ascii=False)+'\n')
