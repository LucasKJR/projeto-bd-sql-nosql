"""Experimento exploratório Q4: lotes de 100 pedidos completos para exportação administrativa."""
import csv,json,random
from pathlib import Path
from lab.db import connect_pg,connect_mongo,run
from lab.core import validate_filters,summarize
out=Path('results/q4-lotes-100-pedidos');out.mkdir(exist_ok=False)
a,b,_=validate_filters('2025-01-01','2026-01-01',1)
ids=random.Random(20261117).sample(range(1,999902),30)
cs={'postgres':connect_pg(),'mongo':connect_mongo()};samples=[]
try:
 for oid in ids:
  baseline=run('postgres','batch',a,b,oid,cs['postgres'])['rows']
  other=run('mongo','batch',a,b,oid,cs['mongo'])['rows']
  assert baseline==other and len(baseline)==100
  for rep in range(10):
   for source in (('postgres','mongo') if rep%2==0 else ('mongo','postgres')):
    r=run(source,'batch',a,b,oid,cs[source]);assert r['rows']==baseline
    samples.append(dict(order_id=oid,items=sum(len(x['items']) for x in baseline),repetition=rep+1,source=source,elapsed_ms=r['elapsed_ms']))
 summary={s:summarize([x['elapsed_ms'] for x in samples if x['source']==s]) for s in cs}
 result=dict(summary=summary,speedup_sql_over_mongo=summary['postgres']['median_ms']/summary['mongo']['median_ms'],seed=20261117,ids=ids,method='30 inícios de lote aleatórios sem reposição; 100 pedidos por lote; 1 aquecimento por ID/banco; 10 repetições medidas por ID/banco; ordem alternada; mesmas linhas; conexões persistentes; Mongo find por faixa de _id; SQL por faixa de PK com join e jsonb_agg; ordem por ID nos dois lados',equivalent=True)
 (out/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
finally:
 with (out/'samples.csv').open('w',newline='') as f:
  if samples:
   w=csv.DictWriter(f,fieldnames=list(samples[0]));w.writeheader();w.writerows(samples)
 for c in cs.values():c.close()
