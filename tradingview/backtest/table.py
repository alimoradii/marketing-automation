import json, glob, sys
names = sys.argv[1:] or sorted(p[8:-5] for p in glob.glob('results/*.json') if not p.endswith('_rows.json'))
print('%-26s %-5s | %-30s | %-30s | %-30s | %s' % ('variant', 'set', 'FULL trades win R(net) PF DD', 'H1 2025 trades R(net) PF', 'H2 2026 trades R(net) PF', 'big>4R'))
for n in names:
    try: d = json.load(open('results/%s.json' % n))
    except Exception: continue
    for k in ('all', 'one'):
        f = d['full'][k + '_net']; g = d['full'][k]; a = d['h1'][k + '_net']; b = d['h2'][k + '_net']
        print('%-26s %-5s | %4d %4.1f%% %+6.1f(%+6.1f) %4.2f %5.1f | %4d %+6.1f %4.2f | %4d %+6.1f %4.2f | %s' % (
            n, k, g['closed'], g['winrate'], g['totalR'], f['totalR'], f['pf'], f['maxDD'], a['closed'], a['totalR'], a['pf'], b['closed'], b['totalR'], b['pf'],
            '%d/%+.0f' % (d['big']['n'], d['big']['sum']) if k == 'all' else ''))
