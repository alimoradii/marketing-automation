"""python3 batch.py NAME base k=v ...  -> results/NAME.json (stats overall and per half, all signals and one at a time, gross and net)"""
import sys, json, os
import sim
from sim import *
name, mode = sys.argv[1], sys.argv[2]
cfg = parse_cfg(sys.argv[3:])
s = run(cfg)
rows = trades_of(s)
SPLIT = timestamp(TZ, 2026, 1, 1)
def block(rs):
    one = one_at_a_time(rs)
    return dict(all=stats(rs), all_net=stats(rs, 'Rnet'), one=stats(one), one_net=stats(one, 'Rnet'))
out = dict(name=name, mode=mode, cfg=cfg, full=block(rows),
           h1=block([r for r in rows if r['time'] < SPLIT]), h2=block([r for r in rows if r['time'] >= SPLIT]))
rs = sorted([r['R'] for r in rows if r['R'] is not None], reverse=True)
out['big'] = dict(n=sum(1 for x in rs if x > 4), sum=round(sum(x for x in rs if x > 4), 1))
os.makedirs('results', exist_ok=True)
json.dump(out, open('results/%s.json' % name, 'w'), default=str)
json.dump(rows, open('results/%s_rows.json' % name, 'w'), default=str)
