import random
from datetime import datetime, timedelta, timezone
from statistics import median, quantiles

def orders(count, seed=42):
    if count < 1: raise ValueError("count deve ser positivo")
    rng=random.Random(seed)
    base=datetime(2025,1,1,tzinfo=timezone.utc)
    for oid in range(1,count+1):
        customer=rng.randint(1,10000)
        date=base+timedelta(seconds=rng.randrange(365*86400))
        status=rng.choices(["criado","concluido","cancelado"],[10,80,10])[0]
        items=[]
        for pos in range(rng.randint(1,10)):
            pid=rng.randint(1,1000)
            items.append(dict(position=pos,product_id=pid,product_name=f"Produto {pid}",quantity=rng.randint(1,5),unit_cents=100+pid*13))
        yield dict(id=oid,customer_id=customer,created_at=date.isoformat(),status=status,items=items,total_cents=sum(i["quantity"]*i["unit_cents"] for i in items))

def validate_filters(start,end,order_id):
    a=datetime.strptime(start,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    b=datetime.strptime(end,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    oid=int(order_id)
    if a>=b or oid<1: raise ValueError("Período ou ID inválido")
    return a,b,oid

def summarize(values):
    if not values: raise ValueError("Nenhuma amostra")
    q=quantiles(values,n=4,method="inclusive") if len(values)>1 else [values[0]]*3
    return dict(median_ms=median(values),min_ms=min(values),max_ms=max(values),iqr_ms=q[2]-q[0],samples=len(values))
