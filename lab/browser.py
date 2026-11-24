"""Read-only, bounded MongoDB collection browser."""
from urllib.parse import urlparse, parse_qs
from .db import connect_mongo, normalize
COLLECTIONS = ('orders', 'customers', 'products')
PAGE_SIZE = 20

def parse_browser(url):
    args = parse_qs(urlparse(url).query)
    if set(args) - {'collection', 'after', 'id'}:
        raise ValueError('Parâmetro desconhecido')
    name = args.get('collection', ['orders'])[0]
    if name not in COLLECTIONS:
        raise ValueError('Coleção inválida')
    if 'id' in args and 'after' in args:
        raise ValueError('Use ID ou cursor, não ambos')
    raw = args.get('id', args.get('after', ['0']))[0]
    if not raw.isascii() or not raw.isdecimal():
        raise ValueError('ID/cursor deve ser inteiro positivo')
    value = int(raw)
    if not (0 <= value <= 2147483647) or ('id' in args and value == 0):
        raise ValueError('ID/cursor fora do intervalo')
    return name, value, 'id' in args

def browse(name, value, detail=False):
    if name not in COLLECTIONS or not 0 <= value <= 2147483647:
        raise ValueError('Coleção/ID inválido')
    with connect_mongo() as client:
        collection = client.bd_lab[name]
        if detail:
            doc = collection.find_one({'_id': value}, max_time_ms=5000)
            return {'collection': name, 'document': normalize(doc)}
        # Keyset pagination on the existing _id index; no skip/count/full scan.
        rows = list(collection.find({'_id': {'$gt': value}}, {'items': 0})
                    .sort('_id', 1).hint('_id_').limit(PAGE_SIZE + 1).max_time_ms(5000))
        more = len(rows) > PAGE_SIZE
        rows = rows[:PAGE_SIZE]
        return {'collection': name, 'documents': normalize(rows),
                'next_after': rows[-1]['_id'] if more else None}
