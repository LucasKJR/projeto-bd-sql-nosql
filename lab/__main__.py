import argparse,json
from .workflow import generate,load,benchmark
from .server import serve
p=argparse.ArgumentParser(description="Laboratório PostgreSQL × MongoDB")
sub=p.add_subparsers(dest='command',required=True)
g=sub.add_parser('generate'); g.add_argument('--count',type=int,default=1000000); g.add_argument('--seed',type=int,default=42); g.add_argument('--data',default='data')
l=sub.add_parser('load'); l.add_argument('--data',default='data'); l.add_argument('--out',default='results')
b=sub.add_parser('benchmark'); b.add_argument('--repetitions',type=int,default=10); b.add_argument('--start',default='2025-01-01'); b.add_argument('--end',default='2026-01-01'); b.add_argument('--order-id',type=int,default=1); b.add_argument('--out',default='results')
s=sub.add_parser('serve'); s.add_argument('--port',type=int,default=8000)
args=vars(p.parse_args()); cmd=args.pop('command')
if cmd=='generate': result=generate(args.pop('data'),**args)
elif cmd=='load': result=load(args.pop('data'),args.pop('out'))
elif cmd=='benchmark': result=benchmark(**args)
else: serve(**args); result=None
if result is not None: print(json.dumps(result,indent=2,default=str))
