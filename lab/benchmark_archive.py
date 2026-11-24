"""Read the exact stored samples summaries used in the project report."""
import json
import math
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / 'results'
EXPERIMENTS = (
    ('Q1', 'Buscar um pedido por ID', '100 IDs × 10 repetições, consulta direta', 'q1-direto-100-ids/summary.json', None),
    ('Q2', 'Vendas por dia no ano', 'Vendas de 2025, agregadas por dia', 'rodada-1/benchmark.json', 'daily'),
    ('Q3', 'Top 10 produtos vendidos', 'Ranking de 2025 por unidades vendidas', 'rodada-1/benchmark.json', 'top'),
    ('Q4', 'Lote de 100 pedidos completos', '30 lotes × 10 repetições, com os itens', 'q4-lotes-100-pedidos/summary.json', None),
)

def history():
    cached = {}
    rows = []
    for code, label, scope, filename, kind in EXPERIMENTS:
        if filename not in cached:
            cached[filename] = json.loads((RESULTS / filename).read_text(encoding='utf-8'))
        archive = cached[filename]['summary']
        result = archive[kind] if kind else archive
        pg, mongo = (result[key] for key in ('postgres', 'mongo'))
        a, b = pg['median_ms'], mongo['median_ms']
        if not all(math.isfinite(v) and v>0 for v in (a,b)) or pg['samples']!=mongo['samples'] or pg['samples']<10:
            raise ValueError('Registro de benchmark inválido.')
        winner = 'Empate' if a==b else 'PostgreSQL' if a<b else 'MongoDB'
        rows.append(dict(code=code,label=label,scope=scope,postgres_ms=a,mongo_ms=b,
                         samples=pg['samples'],winner=winner,lower_pct=100*abs(a-b)/max(a,b),
                         ratio=max(a,b)/min(a,b),archive='results/'+filename))
    return dict(run_date='2026-11-17',rows=rows)
