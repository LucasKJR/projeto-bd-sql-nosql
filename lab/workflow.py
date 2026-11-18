import json,hashlib,time,platform,csv,sys
from pathlib import Path
from datetime import datetime
from .core import orders,summarize,validate_filters
from .db import connect_pg,connect_mongo,SCHEMA,run

def generate(folder,count=1000000,seed=42):
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    target=folder/'orders.jsonl'
    t=time.perf_counter(); digest=hashlib.sha256(); items=0; total=0
    with target.open('xb') as f:
        for o in orders(count,seed):
            line=(json.dumps(o,separators=(',',':'))+'\n').encode()
            digest.update(line); f.write(line); items+=len(o['items']); total+=o['total_cents']
    m=dict(seed=seed,orders=count,items=items,total_cents=total,sha256=digest.hexdigest(),bytes=target.stat().st_size,generation_seconds=time.perf_counter()-t,logical_record="um pedido completo",synthetic=True)
    (folder/'manifest.json').write_text(json.dumps(m,indent=2))
    return m

def records(folder):
    with (Path(folder)/'orders.jsonl').open() as f:
        for line in f: yield json.loads(line)

def load(folder,out):
    folder=Path(folder); out=Path(out); out.mkdir(parents=True,exist_ok=True)
    expected=json.loads((folder/'manifest.json').read_text())
    digest=hashlib.sha256()
    with (folder/'orders.jsonl').open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): digest.update(block)
    if digest.hexdigest()!=expected['sha256']: raise ValueError("SHA256 da massa diverge")
    report={'manifest':expected,'python':sys.version,'platform':platform.platform(),'loads':{}}
    # Refuse to destroy or overwrite existing data. Each database is an independent stage.
    pg=connect_pg(); mongo=connect_mongo()
    try:
        with pg.cursor() as c:
            c.execute("SELECT to_regclass('public.orders') AS existing")
            if c.fetchone()['existing']: raise ValueError("PostgreSQL já possui orders; use banco vazio")
        if set(mongo.bd_lab.list_collection_names()) & {'orders','customers','products'}: raise ValueError("MongoDB já possui coleções do laboratório; use banco vazio")
        t=time.perf_counter()
        with pg.cursor() as c:
            c.execute(SCHEMA)
            c.executemany("INSERT INTO customers VALUES (%s,%s)",((i,f"Cliente {i}") for i in range(1,10001)))
            c.executemany("INSERT INTO products VALUES (%s,%s,%s)",((i,f"SKU-{i}",f"Produto {i}") for i in range(1,1001)))
            with c.copy("COPY orders(id,customer_id,created_at,status,total_cents) FROM STDIN") as copy:
                for o in records(folder): copy.write_row((o['id'],o['customer_id'],o['created_at'],o['status'],o['total_cents']))
            with c.copy("COPY items(order_id,position,product_id,product_name,quantity,unit_cents) FROM STDIN") as copy:
                for o in records(folder):
                    for i in o['items']: copy.write_row((o['id'],i['position'],i['product_id'],i['product_name'],i['quantity'],i['unit_cents']))
        pg.commit()
        with pg.cursor() as c: c.execute("ANALYZE")
        pg.commit()
        report['loads']['postgres_seconds']=time.perf_counter()-t
        t=time.perf_counter()
        db=mongo.bd_lab
        db.customers.insert_many([{'_id':i,'name':f"Cliente {i}"} for i in range(1,10001)])
        db.products.insert_many([{'_id':i,'sku':f"SKU-{i}",'name':f"Produto {i}"} for i in range(1,1001)])
        batch=[]
        for o in records(folder):
            o['_id']=o.pop('id'); o['created_at']=datetime.fromisoformat(o['created_at'])
            batch.append(o)
            if len(batch)==1000: db.orders.insert_many(batch); batch=[]
        if batch: db.orders.insert_many(batch)
        db.orders.create_index([('status',1),('created_at',1)])
        db.orders.create_index([('items.product_id',1)])
        db.products.create_index('sku',unique=True)
        report['loads']['mongo_seconds']=time.perf_counter()-t
        with pg.cursor() as c:
            c.execute("SELECT count(*) AS orders,sum(total_cents)::bigint AS total_cents FROM orders")
            report['postgres_counts']=c.fetchone()
            c.execute("SELECT count(*) AS items FROM items"); report['postgres_counts'].update(c.fetchone())
            c.execute("SELECT pg_database_size(current_database()) AS bytes"); report['postgres_bytes']=c.fetchone()['bytes']
            c.execute("SELECT version() AS version"); report['postgres_version']=c.fetchone()['version']
        m=list(db.orders.aggregate([{'$group':{'_id':None,'orders':{'$sum':1},'items':{'$sum':{'$size':'$items'}},'total_cents':{'$sum':'$total_cents'}}}]))[0]
        m.pop('_id'); report['mongo_counts']=m
        report['mongo_stats']=db.command('dbStats'); report['mongo_version']=mongo.server_info()['version']
        for key in ('orders','items','total_cents'):
            if report['postgres_counts'][key]!=expected[key] or m[key]!=expected[key]: raise ValueError(f"Integridade divergiu: {key}")
        report['validated']=True
    except Exception as e:
        pg.rollback(); report['validated']=False; report['error']=str(e)
        raise
    finally:
        (out/'load.json').write_text(json.dumps(report,indent=2,default=str)); pg.close(); mongo.close()
    return report

def benchmark(out,repetitions=10,start='2025-01-01',end='2026-01-01',order_id=1):
    if repetitions<10: raise ValueError("Mínimo 10 repetições")
    a,b,oid=validate_filters(start,end,order_id); out=Path(out); out.mkdir(parents=True,exist_ok=True)
    if any((out/name).exists() for name in ('samples.csv','benchmark.json','benchmark-failure.json')):
        raise FileExistsError('Resultados já existem; use --out results/nova-rodada')
    connections={}
    try:
        connections['postgres']=connect_pg(); connections['mongo']=connect_mongo()
    except Exception as e:
        for c in connections.values(): c.close()
        (out/'benchmark-failure.json').write_text(json.dumps({'error':str(e),'complete':False}))
        raise
    samples=[]; summary={}
    try:
        for kind in ('order','daily','top'):
            baseline=run('postgres',kind,a,b,oid,connections['postgres'])['rows']
            if not baseline: raise ValueError(f"Consulta {kind} vazia: ajuste filtros/ID")
            other=run('mongo',kind,a,b,oid,connections['mongo'])['rows']
            if baseline!=other: raise ValueError(f"Resultados diferentes em {kind}")
            # Two unmeasured warmups; sequential runs alternate first database.
            for _ in range(2):
                for source in connections: run(source,kind,a,b,oid,connections[source])
            for rep in range(repetitions):
                for source in (('postgres','mongo') if rep%2==0 else ('mongo','postgres')):
                    result=run(source,kind,a,b,oid,connections[source])
                    if result['rows']!=baseline: raise ValueError(f"Resultado mudou: {source}/{kind}")
                    samples.append(dict(query=kind,source=source,repetition=rep+1,elapsed_ms=result['elapsed_ms'],rows=len(baseline)))
            summary[kind]={s:summarize([x['elapsed_ms'] for x in samples if x['query']==kind and x['source']==s]) for s in connections}
            summary[kind]['speedup_sql_over_mongo']=summary[kind]['postgres']['median_ms']/summary[kind]['mongo']['median_ms']
        result=dict(summary=summary,filters=dict(start=start,end=end,order_id=oid),warmups=2,cache="aquecido; sem limpeza de caches do SO/bancos",method="perf_counter_ns; execução, materialização, normalização e JSON; conexões persistentes, ordem alternada",platform=platform.platform())
        (out/'benchmark.json').write_text(json.dumps(result,indent=2))
        return result
    except Exception as e:
        (out/'benchmark-failure.json').write_text(json.dumps({'error':str(e),'complete':False}))
        raise
    finally:
        if samples:
            with (out/'samples.csv').open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(samples[0])); w.writeheader(); w.writerows(samples)
        for c in connections.values(): c.close()
