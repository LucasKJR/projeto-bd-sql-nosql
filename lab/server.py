import json
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
from pathlib import Path
from .core import validate_filters
from .db import run,SQL
STATIC=Path(__file__).resolve().parent.parent/'static'
def parse_request(url):
    p=parse_qs(urlparse(url).query)
    source=p.get('source',['postgres'])[0]; kind=p.get('query',['daily'])[0]
    if source not in ('postgres','mongo') or kind not in SQL: raise ValueError("Fonte/consulta inválida")
    a,b,oid=validate_filters(p.get('start',['2025-01-01'])[0],p.get('end',['2026-01-01'])[0],p.get('order_id',['1'])[0])
    return source,kind,a,b,oid
class Handler(BaseHTTPRequestHandler):
    def send(self,status,body,content_type='application/json'):
        self.send_response(status); self.send_header('Content-Type',content_type+'; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/query':
            try: data=run(*parse_request(self.path)); self.send(200,json.dumps(data).encode())
            except ValueError as e: self.send(400,json.dumps({'error':str(e)}).encode())
            except Exception:
                self.send(503,json.dumps({'error':'Banco indisponível ou consulta falhou. Confira carga, drivers e logs do servidor.'}).encode())
                import traceback; traceback.print_exc()
            return
        names={'/':'index.html','/static/index.html':'index.html','/static/style.css':'style.css','/static/app.js':'app.js','/static/logic.js':'logic.js'}
        if path not in names: self.send(404,b'{}'); return
        file=STATIC/names[path]
        mime={'.html':'text/html','.css':'text/css','.js':'text/javascript'}[file.suffix]
        self.send(200,file.read_bytes(),mime)
def serve(port=8000):
    print(f"Dashboard local: http://127.0.0.1:{port}",flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
