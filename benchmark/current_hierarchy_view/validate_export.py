"""Independent, integer-only checks for the fixed two-graph root export."""
import json
import math

FAMILIES=('leaf_hierarchy4','leaf_shuffled4')

def require(value,message):
    if not value:raise ValueError(message)

def read(path):
    def unique(items):
        value={}
        for key,item in items:
            require(key not in value,'duplicate JSON key');value[key]=item
        return value
    def reject(value):raise ValueError('nonfinite JSON: '+value)
    value=json.loads(path.read_text(),object_pairs_hook=unique,parse_constant=reject)
    def integers(item):
        if isinstance(item,dict):
            for nested in item.values():integers(nested)
        elif isinstance(item,list):
            for nested in item:integers(nested)
        else:require(type(item) in (str,int,bool,type(None)) or (type(item) is float and math.isfinite(item)),
                     'nonfinite export or receipt value')
    # Per-field export checks below reject non-integer counters/endpoints.
    # Inherited monitor receipts also contain finite duration measurements.
    integers(value);return value

class Ledger:
    def __init__(self,n):self.parent=list(range(n))
    def root(self,v):
        while self.parent[v]!=v:self.parent[v]=self.parent[self.parent[v]];v=self.parent[v]
        return v
    def join(self,u,v):
        u,v=self.root(u),self.root(v)
        if u==v:return False
        self.parent[u]=v;return True

def words(seed,count):
    """Canonical scalar MT19937 recurrence; independent of native predicates."""
    state=[seed&0xffffffff]
    for i in range(1,624):state.append((1812433253*(state[-1]^(state[-1]>>30))+i)&0xffffffff)
    index=624
    for _ in range(count):
        if index==624:
            for i in range(624):
                joined=(state[i]&0x80000000)|(state[(i+1)%624]&0x7fffffff)
                state[i]=state[(i+397)%624]^(joined>>1)^(0x9908b0df if joined&1 else 0)
            index=0
        word=state[index];index+=1
        word^=word>>11;word^=(word<<7)&0x9d2c5680;word^=(word<<15)&0xefc60000;word^=word>>18
        yield word&0xffffffff

def fingerprint(edges,n,weighted):
    result=14695981039346656037
    def append(number):
        nonlocal result
        for shift in (0,8,16,24):result=((result^((number>>shift)&255))*1099511628211)&((1<<64)-1)
    append(n)
    for u,v,w,identifier in edges:
        for number in ([u,v,w,identifier] if weighted else [u,v,identifier]):append(number)
    return str(result)

def graph(stage):
    require(set(stage)=={'n','m','edges'} and type(stage['n']) is int and 1<stage['n']<=1024 and
            type(stage['m']) is int and stage['m']==len(stage['edges']),'graph count/schema')
    ids=set();weights=set()
    for edge in stage['edges']:
        require(type(edge) is list and len(edge)==4 and all(type(x) is int for x in edge),'edge schema')
        u,v,w,i=edge
        require(0<=u<stage['n'] and 0<=v<stage['n'] and u!=v and 0<w<0x3f3f3f3f and 0<=i<32768,'edge domain')
        require(i not in ids and w not in weights,'duplicate edge ID/weight');ids.add(i);weights.add(w)

def forest_paths(edges,selected,n):
    require(type(selected) is list and all(type(x) is int for x in selected) and len(selected)==len(set(selected)),'forest ID schema')
    by_id={edge[3]:edge for edge in edges};ledger=Ledger(n);adjacent=[[] for _ in range(n)]
    for identifier in selected:
        require(identifier in by_id,'forest edge missing');u,v,w,_=by_id[identifier]
        require(ledger.join(u,v),'forest cycle');adjacent[u].append((v,w));adjacent[v].append((u,w))
    maxima=[]
    for source in range(n):
        row=[None]*n;stack=[(source,-1,-1)]
        while stack:
            vertex,parent,maximum=stack.pop();row[vertex]=maximum
            for other,weight in adjacent[vertex]:
                if other!=parent:stack.append((other,vertex,max(maximum,weight)))
        maxima.append(row)
    for u,v,w,_ in edges:require(maxima[u][v] is not None and maxima[u][v]<=w,'forest spanning/cycle certificate')
    return maxima

def contraction(before,after,chosen,mapping):
    cheapest=[None]*before['n'];by_id={edge[3]:edge for edge in before['edges']}
    for edge in before['edges']:
        for vertex in edge[:2]:
            if cheapest[vertex] is None or edge[2]<cheapest[vertex][2]:cheapest[vertex]=edge
    require(type(chosen) is list and all(type(x) is int for x in chosen) and len(chosen)==len(set(chosen)) and
            set(chosen)=={edge[3] for edge in cheapest if edge is not None},'wrong contraction minima')
    ledger=Ledger(before['n'])
    for identifier in chosen:require(ledger.join(*by_id[identifier][:2]),'contraction cycle')
    names={};expected=[]
    for vertex in range(before['n']):
        root=ledger.root(vertex)
        if root not in names:names[root]=len(names)
        expected.append(names[root])
    require(mapping==expected and all(type(x) is int for x in mapping) and after['n']==len(names),'wrong quotient map')
    crossing=[]
    for u,v,w,i in before['edges']:
        u,v=mapping[u],mapping[v]
        if u!=v:crossing.append([min(u,v),max(u,v),w,i])
    require(after['edges']==crossing,'quotient lost/reordered parallel records')

def samples(root,samples_,mst):
    require(type(samples_) is list and len(samples_)==2,'missing sample policy')
    generated=list(words(2801,root['m']))
    keys={'policy','mask','engine_words','sample_edges','forest_edges','forest_components','heavy_edges','light_edges',
          'selected_parent_positions','sampled_ids','forest_ids','heavy_ids'}
    for sample,policy,mask in zip(samples_,('half','eighth'),(1,7)):
        require(set(sample)==keys and sample['policy']==policy,'sample schema/policy')
        require(all(type(sample[key]) is int for key in ('mask','engine_words','sample_edges','forest_edges','forest_components','heavy_edges','light_edges')),'sample count types')
        positions=[i for i,word in enumerate(generated) if word%(mask+1)==mask]
        require(sample['mask']==mask and sample['engine_words']==root['m'] and sample['selected_parent_positions']==positions and
                all(type(x) is int for x in sample['selected_parent_positions']),'sample draws/position order differ')
        selected=[root['edges'][position] for position in positions]
        require(sample['sampled_ids']==[edge[3] for edge in selected] and all(type(x) is int for x in sample['sampled_ids']),'sample restored IDs differ')
        maxima=forest_paths(selected,sample['forest_ids'],root['n'])
        heavy=[i for u,v,w,i in root['edges'] if maxima[u][v] is not None and w>maxima[u][v]]
        require(sample['heavy_ids']==heavy and all(type(x) is int for x in sample['heavy_ids']),'heavy marks differ from independent paths')
        require(not(set(heavy)&set(mst)),'reference MST removed')
        expected=dict(sample_edges=len(selected),forest_edges=len(sample['forest_ids']),forest_components=root['n']-len(sample['forest_ids']),
                      heavy_edges=len(heavy),light_edges=root['m']-len(heavy))
        require(all(sample[key]==value for key,value in expected.items()),'sample/filter complete counts differ')

def validate(value):
    require(set(value)=={'schema','trace_scope','graphs'} and value['schema']=='current_hierarchy_root_view_v1' and
            value['trace_scope']=='reconstructed_root_only' and type(value['graphs']) is list and len(value['graphs'])==2,'wrong export scope')
    keys={'family','n','m','density','graph_seed','sampling_seed','input_fingerprint','topology_fingerprint','original_to_label',
          'mst_ids','stages','maps','selected_ids','samples','validation'}
    for data,family in zip(value['graphs'],FAMILIES):
        require(set(data)==keys and data['family']==family and data['validation']=='pass','graph record schema')
        for key,number in dict(n=1024,m=32768,density=32,graph_seed=17000011,sampling_seed=2801).items():
            require(type(data[key]) is int and data[key]==number,'wrong declared fixture')
        labels=data['original_to_label'];require(all(type(v) is int for v in labels) and sorted(labels)==list(range(1024)),'wrong labels')
        stages=data['stages'];require(len(stages)==3 and len(data['maps'])==len(data['selected_ids'])==2,'missing stages')
        for stage in stages:graph(stage)
        require((stages[0]['n'],stages[0]['m'])==(1024,32768) and {edge[3] for edge in stages[0]['edges']}==set(range(32768)) and
                {edge[2] for edge in stages[0]['edges']}==set(range(1,32769)),'wrong original edge/rank domain')
        require(len({tuple(sorted(edge[:2])) for edge in stages[0]['edges']})==32768,'original input not simple')
        for weighted,key in ((True,'input_fingerprint'),(False,'topology_fingerprint')):
            require(type(data[key]) is str and data[key]==fingerprint(stages[0]['edges'],1024,weighted),'wrong full-input fingerprint')
        require(len(data['mst_ids'])==1023,'wrong full MST size')
        for stage in stages:
            stage_ids={edge[3] for edge in stage['edges']};surviving=[i for i in data['mst_ids'] if i in stage_ids]
            forest_paths(stage['edges'],surviving,stage['n'])
        for index in range(2):contraction(stages[index],stages[index+1],data['selected_ids'][index],data['maps'][index])
        if family=='leaf_hierarchy4':require([(stage['n'],stage['m']) for stage in stages]==[(1024,32768),(256,32000),(128,31872)],'ordered count formula')
        samples(stages[2],data['samples'],data['mst_ids'])
    a,b=value['graphs'];require(a['original_to_label']==b['original_to_label'] and
        [(e[0],e[1],e[3]) for e in a['stages'][0]['edges']]==[(e[0],e[1],e[3]) for e in b['stages'][0]['edges']],'topology twins differ')
    return dict(graphs=2,root_samples=4,original_edges=65536,root_query_edges=sum(2*data['stages'][2]['m'] for data in value['graphs']))
