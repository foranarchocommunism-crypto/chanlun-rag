import collections, hashlib, json, pathlib, sqlite3, unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent
DB = ROOT / 'shared-knowledge/v0.1.0/graph.sqlite'
db = sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
rows = lambda q: [dict(r) for r in db.execute(q)]
concepts = {r['id']: r for r in rows('select * from concepts')}
claims = {r['id']: r for r in rows('select * from claims')}
relations = rows('select * from relations')
evidence = rows('select e.*,p.text passage_text,p.role,p.speaker,p.published_at from evidence e join passages p on p.id=e.passage_id')
for c in concepts.values(): c['aliases'] = json.loads(c['aliases'])
for c in claims.values():
    for k in ['conditions','exceptions','concept_ids','derivation']: c[k] = json.loads(c[k])
for r in relations: r['claim_ids'] = json.loads(r['claim_ids'])
norm = lambda s: unicodedata.normalize('NFKC', s).strip().lower()
names = collections.defaultdict(set)
for c in concepts.values():
    for s in [c['label']] + c['aliases']: names[norm(s)].add(c['id'])
aliases_conflicts = {s: sorted(ids) for s,ids in names.items() if len(ids)>1}
degree, adjacency, claim_degree = collections.Counter(), collections.defaultdict(set), collections.Counter()
for c in claims.values():
    if c['review_status']=='reviewed': claim_degree.update(c['concept_ids'])
for r in relations:
    degree.update([r['source'],r['target']]); adjacency[r['source']].add(r['target'])
e_by_claim = collections.defaultdict(list)
for e in evidence: e_by_claim[e['claim_id']].append(e)
support_issues = []
for r in relations:
    for cid in r['claim_ids']:
        if cid not in claims or claims[cid]['review_status']!='reviewed' or not e_by_claim[cid]: support_issues.append({'relation':r['id'],'claim':cid})
indexes, lows, stack, active, sccs = {}, {}, [], set(), []
def visit(v):
    indexes[v]=lows[v]=len(indexes); stack.append(v); active.add(v)
    for w in sorted(adjacency[v]):
        if w not in indexes: visit(w); lows[v]=min(lows[v],lows[w])
        elif w in active: lows[v]=min(lows[v],indexes[w])
    if lows[v]==indexes[v]:
        component=[]
        while True:
            w=stack.pop(); active.remove(w); component.append(w)
            if w==v: break
        sccs.append(component)
for v in concepts:
    if v not in indexes: visit(v)
triples=collections.Counter((r['source'],r['type'],r['target']) for r in relations)
reverse = {(r['source'],r['target'],r['type']) for r in relations}
schema={t:rows(f'pragma table_info({t})') for t in ['concepts','claims','relations','evidence','reviews']}
def typed_cycles(typ):
    adj=collections.defaultdict(set)
    for r in relations:
        if r['type']==typ: adj[r['source']].add(r['target'])
    ind,low,st,on,components={},{},[],set(),[]
    def walk(v):
        ind[v]=low[v]=len(ind);st.append(v);on.add(v)
        for w in sorted(adj[v]):
            if w not in ind: walk(w);low[v]=min(low[v],low[w])
            elif w in on: low[v]=min(low[v],ind[w])
        if low[v]==ind[v]:
            group=[]
            while True:
                w=st.pop();on.remove(w);group.append(w)
                if w==v: break
            if len(group)>1: components.append([concepts[x]['label'] for x in group])
    for v in concepts:
        if v not in ind:walk(v)
    return components
out={
 'scope':'Read-only actual canonical graph; structural checks are not semantic entailment accuracy.',
 'database_sha256':hashlib.sha256(DB.read_bytes()).hexdigest(),
 'counts':{t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','passages','concepts','claims','evidence','relations','reviews']},
 'claim_status':dict(collections.Counter(c['review_status'] for c in claims.values())),
 'reviewed_kinds':dict(collections.Counter(c['kind'] for c in claims.values() if c['review_status']=='reviewed')),
 'reviewed_ambiguity':sum(c['ambiguity_status']!='none' for c in claims.values() if c['review_status']=='reviewed'),
 'reviewed_evidence':sum(claims[e['claim_id']]['review_status']=='reviewed' for e in evidence),
 'reviewers':rows('select reviewer,count(*) n from reviews group by reviewer order by n desc'),
 'relation_types':dict(collections.Counter(r['type'] for r in relations)),
 'schema':schema,
 'concepts_with_aliases':sum(bool(c['aliases']) for c in concepts.values()),
 'alias_count':sum(len(c['aliases']) for c in concepts.values()),
 'normalized_alias_conflicts':aliases_conflicts,
 'empty_concept_descriptions':sum(not c['description'].strip() for c in concepts.values()),
 'concept_id_label_hash_match':sum(c['id']=='concept-'+hashlib.sha256(c['label'].encode()).hexdigest()[:16] for c in concepts.values()),
 'self_loops':[r for r in relations if r['source']==r['target']],
 'duplicate_triples':[list(k)+[n] for k,n in triples.items() if n>1],
 'reverse_same_type_pair_count':sum((b,a,t) in reverse for a,b,t in reverse)//2,
 'nontrivial_scc_sizes':sorted([len(s) for s in sccs if len(s)>1],reverse=True),
 'same_type_cycle_components':{typ:typed_cycles(typ) for typ in sorted(set(r['type'] for r in relations))},
 'largest_scc_labels':[concepts[i]['label'] for i in sorted(max(sccs,key=len))],
 'zero_relation_degree_nodes':[c['label'] for id,c in concepts.items() if not degree[id]],
 'degree_distribution':dict(sorted(collections.Counter(degree[id] for id in concepts).items())),
 'highest_degree':[{'id':id,'label':concepts[id]['label'],'incident_edges':n,'reviewed_claim_links':claim_degree[id]} for id,n in degree.most_common(15)],
 'relation_support_reference_errors':support_issues,
 'quote_mismatches':[e['id'] for e in evidence if e['passage_text'][e['quote_start']:e['quote_end']]!=e['quote']],
 'reviewed_evidence_wrong_speaker':[e['id'] for e in evidence if claims[e['claim_id']]['review_status']=='reviewed' and (e['role'] not in ['author_body','author_reply','author_commentary'] or e['speaker']!='缠中说禅')],
 'missing_claim_concept_refs':[c['id'] for c in claims.values() if any(i not in concepts for i in c['concept_ids'])],
 'fk_check':rows('pragma foreign_key_check'),
 'integrity_check':db.execute('pragma integrity_check').fetchone()[0],
}
samples=[]
for typ in sorted(set(r['type'] for r in relations)):
    group=sorted([r for r in relations if r['type']==typ],key=lambda r:r['id'])
    for r in [group[i] for i in sorted(set([0,len(group)//2,len(group)-1]))]:
        samples.append({**r,'source_label':concepts[r['source']]['label'],'target_label':concepts[r['target']]['label'],
            'supports':[{'claim':claims[id], 'evidence':e_by_claim[id]} for id in r['claim_ids']]})
(OUT/'graph-structure.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'relation-samples.json').write_text(json.dumps(samples,ensure_ascii=False,indent=2),encoding='utf-8')
historical={}
for name in ['m4-graph-development','m3-hybrid-development','m4-rerank-development','m4-production-development','m6-prospective-acceptance']:
    p=ROOT/'validation-runs/agent-implementation-20261022'/f'{name}.json'
    data=json.loads(p.read_text(encoding='utf-8'))
    historical[name]={k:v for k,v in data.items() if k not in ['observations','cases','errors','results']}
(OUT/'prior-evaluation-summary.json').write_text(json.dumps(historical,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ['schema','reviewers','largest_scc_labels','zero_relation_degree_nodes','degree_distribution']},ensure_ascii=False,indent=2))
