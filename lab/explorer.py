"""Bounded read-only explorer. No user-provided SQL or Mongo commands are executed."""
import json
import re
from datetime import datetime, timezone
from time import perf_counter
from urllib.parse import parse_qs, urlparse

from .db import connect_mongo, connect_pg, normalize

ORDER = {'customer_id':'int','created_at':'date','status':'status','total_cents':'int'}
CATALOG = {
    'postgres':{
        'orders':({'id':'int',**ORDER},('id',)),
        'items':({'order_id':'int','position':'int','product_id':'int','product_name':'text','quantity':'int','unit_cents':'int'},('order_id','position')),
        'customers':({'id':'int','name':'text'},('id',)),
        'products':({'id':'int','sku':'text','name':'text'},('id',)),
    },
    'mongo':{
        'orders':({'_id':'int',**ORDER,'items':'object','items.product_id':'int','items.product_name':'text','items.quantity':'int','items.unit_cents':'int','items.position':'int'},('_id',)),
        'customers':({'_id':'int','name':'text'},('_id',)),
        'products':({'_id':'int','sku':'text','name':'text'},('_id',)),
    },
}
OPS = {'int':('eq','gte','lte','lt','gt'),'date':('gte','lt'),'status':('eq',),'text':('eq','prefix')}
SQL_OP = {'eq':'=','gte':'>=','lte':'<=','lt':'<','gt':'>'}
MONGO_OP = {'gte':'$gte','lte':'$lte','lt':'$lt','gt':'$gt'}

def integer(value):
    if type(value) not in (str,int) or not re.fullmatch(r'[0-9]{1,13}', str(value)):
        raise ValueError('Use um inteiro não negativo.')
    return int(value)

def parse(url):
    query=urlparse(url).query
    if len(query)>7000:
        raise ValueError('Consulta longa demais.')
    p=parse_qs(query, keep_blank_values=True, max_num_fields=6)
    if set(p)-{'source','entity','filters','after','limit','select'} or any(len(v)!=1 for v in p.values()):
        raise ValueError('Parâmetros inválidos.')
    get=lambda key,default: p.get(key,[default])[0]
    source,entity=get('source','postgres'),get('entity','orders')
    if source not in CATALOG or entity not in CATALOG[source]:
        raise ValueError('Tabela/coleção não disponível.')
    fields,keys=CATALOG[source][entity]
    returnable=tuple(field for field in fields if '.' not in field)
    selected=json.loads(get('select',json.dumps(returnable)))
    if (not isinstance(selected,list) or not selected or
        any(not isinstance(field,str) or field not in returnable for field in selected) or
        len(set(selected))!=len(selected)):
        raise ValueError('Selecione pelo menos um campo válido para o resultado.')
    limit=integer(get('limit','20'))
    if limit not in (10,20,50):
        raise ValueError('Escolha 10, 20 ou 50 registros por página.')
    f=json.loads(get('filters','[]')); after=json.loads(get('after','null'))
    if after is not None:
        if not isinstance(after,list) or len(after)!=len(keys): raise ValueError('Cursor inválido.')
        after=tuple(integer(x) for x in after)
    if not isinstance(f,list) or len(f)>3: raise ValueError('Use no máximo três filtros.')
    filters=[]
    for condition in f:
        if not isinstance(condition,list) or len(condition)!=3: raise ValueError('Filtro inválido.')
        field,op,value=condition
        if not isinstance(field,str) or field not in fields or not isinstance(op,str) or op not in OPS.get(fields[field],()):
            raise ValueError('Campo ou operador inválido para esta consulta.')
        kind=fields[field]
        if kind=='int': value=integer(value)
        elif kind=='date':
            if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value): raise ValueError('Informe uma data válida.')
            value=datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
        else:
            if not isinstance(value,str) or not 0<len(value.strip())<=80 or any(ord(c)<32 for c in value): raise ValueError('Informe texto de até 80 caracteres.')
            value=value.strip()
            if kind=='status' and value not in ('criado','concluido','cancelado'): raise ValueError('Status inválido.')
        filters.append((field,op,value))
    return source,entity,fields,keys,limit,filters,after,tuple(selected)

def sql_literal(value):
    if isinstance(value,int): return str(value)
    if isinstance(value,datetime): return "'"+value.isoformat()+"'::timestamptz"
    return "E'"+value.replace('\\','\\\\').replace("'","''")+"'"

def sql_query(q):
    _,entity,fields,keys,limit,filters,after,selected=q
    pg_id=lambda k: '"'+k+'"'
    selected=', '.join(map(pg_id,dict.fromkeys((*selected,*keys))))
    ordered=', '.join(map(pg_id,keys))
    clauses=[]; values=[]
    for field,op,value in filters:
        if op=='prefix':
            clauses.append(pg_id(field)+ " LIKE %s ESCAPE '!'")
            value=value.replace('!','!!').replace('%','!%').replace('_','!_')+'%'
        else: clauses.append(pg_id(field)+' '+SQL_OP[op]+' %s')
        values.append(value)
    if after is not None:
        predicate=pg_id(keys[0])+' > %s' if len(keys)==1 else '('+ordered+') > (%s, %s)'
        clauses.append(predicate); values.extend(after)
    select='SELECT '+selected+'\nFROM "public".'+pg_id(entity)
    where='\nWHERE '+'\n  AND '.join(clauses) if clauses else ''
    statement=select+where+'\nORDER BY '+ordered+'\nLIMIT %s;'
    values.append(limit+1)
    literals=iter(map(sql_literal,values))
    preview=re.sub(r'%s',lambda _:next(literals),statement)
    return statement,values,preview

def shell_json(value):
    if isinstance(value,datetime): return 'ISODate('+json.dumps(value.isoformat().replace('+00:00','Z'))+')'
    if isinstance(value,dict): return '{'+', '.join(json.dumps(k)+': '+shell_json(v) for k,v in value.items())+'}'
    if isinstance(value,list): return '['+', '.join(map(shell_json,value))+']'
    return json.dumps(value,ensure_ascii=False)

def mongo_query(q):
    _,entity,_,keys,limit,filters,after,_=q
    clauses=[]
    for field,op,value in filters:
        if op=='eq': clauses.append({field:value})
        elif op=='prefix': clauses.append({field:{'$regex':'^'+re.escape(value)}})
        else: clauses.append({field:{MONGO_OP[op]:value}})
    if after is not None: clauses.append({keys[0]:{'$gt':after[0]}})
    match={} if not clauses else clauses[0] if len(clauses)==1 else {'$and':clauses}
    preview='db.getSiblingDB("bd_lab").'+entity+'.find('+shell_json(match)+')\n  .sort({_id: 1}).limit('+str(limit+1)+').maxTimeMS(4000)'
    return match,preview

def mongo_projection(q):
    return {field:1 for field in dict.fromkeys((*q[-1],*q[3]))}

def explore(q):
    source,entity,_,keys,limit,_,_,selected=q
    start=perf_counter()
    if source=='postgres':
        statement,values,_=sql_query(q)
        with connect_pg() as connection, connection.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            cur.execute('SET LOCAL statement_timeout = 4000')
            cur.execute(statement,values); rows=cur.fetchall()
    else:
        match,_=mongo_query(q)
        with connect_mongo() as client:
            rows=list(client.bd_lab[entity].find(match,mongo_projection(q)).sort('_id',1).limit(limit+1).max_time_ms(4000))
    elapsed=(perf_counter()-start)*1000
    more=len(rows)>limit
    rows=rows[:limit]
    next_page=[rows[-1][key] for key in keys] if more else None
    visible=[{field:row[field] for field in selected if field in row} for row in rows]
    return dict(source=source,entity=entity,columns=list(selected),rows=normalize(visible),
                next=next_page,elapsed_ms=round(elapsed,2))
