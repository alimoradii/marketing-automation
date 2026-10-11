"""Run the Python port of MZ_SDP.pine on 5m EURUSD data and report the backtest.

python3 sim.py [name=value ...]     e.g.  python3 sim.py iTgtLiq=False
"""
import os
import re
import sys
import json
import time as _time
from base import *
from sec1 import Sec1
from sec2 import Sec2
from sec3 import Sec3
from sec4 import Sec4
from sec5 import Sec5

DATA = os.environ.get('MZ_DATA', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'EURUSD_MT5_OANDA_MASTER_M5_2025-05-17_to_2026-09-18.csv'))


class Sim(Sec1, Sec2, Sec3, Sec4, Sec5, Base):
    pass


def run(cfg=None, path=DATA, start=None, end=None, progress=False):
    s = Sim(path, cfg or {}, start, end)
    names = dir(s)
    inits = sorted([m for m in names if re.fullmatch(r'init_\d+', m)], key=lambda m: int(m[5:]))
    tops = sorted([m for m in names if re.fullmatch(r'top_\d+', m)], key=lambda m: int(m[4:]))
    s._inits, s._tops = inits, tops
    for m in inits:
        getattr(s, m)()
    calls = [getattr(s, m) for m in tops]
    t0 = _time.time()
    for i in range(s.N):
        s.prelude(i)
        for f in calls:
            f()
        if progress and i % 5000 == 0:
            print('bar', i, '/', s.N, '%.0fs' % (_time.time() - t0), file=sys.stderr)
    return s


TERMINAL = ('tp', 'sl', 'close', 'cancel', 'expired', 'void')


def trades_of(s, cost_pips=1.0):
    """one row per signal: fill, exit, R (indicator accounting) and R after costs"""
    ev = {}
    for e in s.trlog:
        ev.setdefault(e['id'], []).append(e)
    out = []
    for sg in s.siglog:
        es = ev.get(sg['id'], [])
        row = dict(sg)
        row['events'] = [e['ev'] for e in es]
        fill = next((e for e in es if e['ev'] == 'filled'), None)
        term = next((e for e in es if e['ev'] in TERMINAL), None)
        row['filled'] = fill is not None
        row['fillBar'] = fill['bar'] if fill else None
        row['fillPx'] = fill['px'] if fill else None
        row['end'] = term['ev'] if term else 'open'
        row['endBar'] = term['bar'] if term else s.N
        row['endTime'] = term['time'] if term else s.T[-1]
        row['R'] = term['r'] if term and term['ev'] in ('tp', 'sl', 'close') else None
        if row['R'] is not None and fill:
            risk = abs(fill['px'] - sg['stop'])
            row['riskPips'] = risk / s.PIP
            row['Rnet'] = row['R'] - (cost_pips * s.PIP / risk if risk > 0 else 0)
        else:
            row['riskPips'] = None
            row['Rnet'] = None
        out.append(row)
    return out


def one_at_a_time(rows):
    """the strategy version: a signal is taken only when no earlier taken signal is still pending or open"""
    taken = []
    busy_until = -1
    for r in sorted(rows, key=lambda r: (r['bar'], r['id'])):
        if r['bar'] >= busy_until:
            taken.append(r)
            busy_until = r['endBar']
    return taken


def stats(rows, key='R'):
    closed = [r for r in rows if r.get(key) is not None]
    rs = [r[key] for r in closed]
    wins = [x for x in rs if x > 0.05]
    losses = [x for x in rs if x < -0.05]
    eq = 0.0; peak = 0.0; dd = 0.0
    for r in sorted(closed, key=lambda r: r['endBar']):
        eq += r[key]; peak = max(peak, eq); dd = max(dd, peak - eq)
    gp = sum(x for x in rs if x > 0); gl = -sum(x for x in rs if x < 0)
    return dict(signals=len(rows), filled=sum(1 for r in rows if r['filled']), closed=len(closed),
                wins=len(wins), losses=len(losses), winrate=(100.0 * len(wins) / len(closed)) if closed else 0.0,
                totalR=sum(rs), avgR=(sum(rs) / len(rs)) if rs else 0.0, pf=(gp / gl) if gl > 0 else float('inf'),
                maxDD=dd,
                cancelled=sum(1 for r in rows if r['end'] == 'cancel'), expired=sum(1 for r in rows if r['end'] == 'expired'),
                void=sum(1 for r in rows if r['end'] == 'void'))


def monthly(rows, key='R'):
    m = {}
    for r in rows:
        if r.get(key) is None:
            continue
        k = format_time(r['endTime'])[:7]
        a = m.setdefault(k, [0, 0, 0.0])
        a[0] += 1; a[1] += 1 if r[key] > 0.05 else 0; a[2] += r[key]
    return m


def parse_cfg(argv):
    cfg = {}
    for a in argv:
        k, v = a.split('=', 1)
        if v in ('True', 'False'):
            v = v == 'True'
        else:
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
        cfg[k] = v
    return cfg


if __name__ == '__main__':
    cfg = parse_cfg(sys.argv[1:])
    s = run(cfg, progress=True)
    rows = trades_of(s)
    res = dict(cfg=cfg, all=stats(rows), all_net=stats(rows, 'Rnet'),
               one=stats(one_at_a_time(rows)), one_net=stats(one_at_a_time(rows), 'Rnet'),
               st=dict(signals=s.st.signals, closed=s.st.closed, wins=s.st.wins, totalR=s.st.totalR),
               first=format_time(s.T[0]), last=format_time(s.T[-1]))
    print(json.dumps(res, indent=1, default=str))
