"""Base of the Python port of tradingview/MZ_SDP.pine (Pine v6) for backtesting.

Conventions every section module follows (see PORTING.md):
  * one class Sim(Sec*, Base); every Pine global is self.<same name>
  * Pine na -> NA (float nan); na(x) tests it; use ne(a, b) for Pine '!=' when an operand may be na
  * arrays -> PArr (list with Pine method names); for i = a to b -> for i in prange(a, b)
  * built-in series: self.open/high/low/close/time/time_close/bar_index; history self.O/H/L/C/T[abs index]
"""
import math, csv, functools
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

NA = float('nan')
NYZ = ZoneInfo('America/New_York')
TZ = "America/New_York"


def na(x):
    return x is None or (isinstance(x, float) and x != x)


def nz(x, y=0):
    return y if na(x) else x


def ne(a, b):
    """Pine '!=': false when either side is na"""
    if na(a) or na(b):
        return False
    return a != b


def pmax(*a):
    if any(na(v) for v in a):
        return NA
    return max(a)


def pmin(*a):
    if any(na(v) for v in a):
        return NA
    return min(a)


def pabs(x):
    return NA if na(x) else abs(x)


def pint(x):
    return NA if na(x) else int(x)


def pround(x):
    if na(x):
        return NA
    return int(math.floor(x + 0.5)) if x >= 0 else -int(math.floor(-x + 0.5))


def pfloor(x):
    return NA if na(x) else math.floor(x)


def pceil(x):
    return NA if na(x) else math.ceil(x)


def prange(a, b):
    """Pine 'for i = a to b': inclusive, counts DOWN when b < a"""
    if na(a) or na(b):
        return []
    a = int(a); b = int(b)
    return range(a, b + 1) if b >= a else range(a, b - 1, -1)


def tstr(x, fmt=None):
    if isinstance(x, bool):
        return "true" if x else "false"
    if na(x):
        return "NaN"
    if isinstance(x, int):
        return str(x)
    if fmt == "0.0":
        return "%.1f" % x
    if fmt == "0.00":
        return "%.2f" % x
    if fmt == "0":
        return "%.0f" % x
    if float(x).is_integer():
        return str(int(x))
    return ("%.5f" % x).rstrip('0').rstrip('.')


class PArr(list):
    """Pine array"""
    def size(self): return len(self)
    def get(self, i): return self[i]
    def set(self, i, v): self[i] = v
    def push(self, v): self.append(v)
    def shift(self): return list.pop(self, 0) if len(self) else NA
    def unshift(self, v): self.insert(0, v)
    def first(self): return self[0]
    def last(self): return self[-1]
    def remove(self, i): return list.pop(self, i)
    def includes(self, v): return v in self
    def indexof(self, v):
        try:
            return self.index(v)
        except ValueError:
            return -1
    def pop(self): return list.pop(self)
    def copy(self): return PArr(self)


def afrom(*a):
    return PArr(a)


class _T:
    _fields = ()
    def __init__(self, *args, **kw):
        for (name, default), v in zip(self._fields, args):
            setattr(self, name, v)
        for name, default in self._fields[len(args):]:
            setattr(self, name, kw.pop(name, default))
        for k, v in kw.items():
            if k not in dict(self._fields):
                raise TypeError("%s has no field %s" % (type(self).__name__, k))
            setattr(self, k, v)
    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, ", ".join("%s=%r" % (n, getattr(self, n)) for n, _ in self._fields if not n.startswith(('lns', 'lbs', 'bxs', 'lls', 'lab'))))


def ptype(name, spec):
    """spec: list of (field, default); default NA = Pine na"""
    return type(name, (_T,), {'_fields': tuple(spec)})


Level = ptype('Level', [('name', NA), ('price', NA), ('bar', NA), ('bsl', False), ('kind', NA), ('swept', False)])
Sweep = ptype('Sweep', [('bar', NA), ('bsl', False), ('name', NA), ('kind', NA), ('price', NA)])
Sess = ptype('Sess', [('active', False), ('key', NA), ('hi', NA), ('lo', NA), ('hiBar', NA), ('loBar', NA)])
Gap = ptype('Gap', [('bar', NA), ('top', NA), ('bottom', NA), ('bull', False), ('filled', False), ('ltf', False), ('t1', 0), ('t2', 0), ('b0', -1), ('nofvg', False), ('atMss', False)])
Hunt = ptype('Hunt', [('bear', False), ('one', NA), ('zero', NA), ('bar', NA), ('level', NA), ('names', NA), ('external', False), ('parent', -1), ('zeroBar', -1)])
Ltf = ptype('Ltf', [('xi', -1), ('xp', NA), ('xt', 0), ('last', -1), ('hunt', False), ('mss', False), ('zero', NA), ('zeroBar', -1)])
Leg = ptype('Leg', [('bear', False), ('one', NA), ('zero', NA), ('oneBar', NA), ('createdBar', NA), ('names', NA), ('z2Alive', True), ('z3Alive', True), ('z2Pend', -1), ('zone', ""), ('touchBar', -1), ('extreme', NA), ('extremeBar', -1), ('mssLevel', NA), ('mssBar', -1), ('ithBar', -1), ('tsoup', False), ('cMss', False), ('cMssBar', -1), ('cFar', NA), ('cDone', False), ('cLevel', NA), ('cLvlBar', -1), ('cMssDrawn', False), ('note', ""), ('fs', False), ('parentBar', -1), ('drOne', NA), ('hasFs', False), ('redraw', False), ('zeroBar', -1), ('endWhy', ""), ('done', False), ('signaled', False), ('inZone', False), ('mssOk', False), ('sbTouch', -1), ('sbExt', NA), ('sbExtBar', -1), ('sbMss', False), ('sbDone', False), ('sbLvl', NA), ('z5', None), ('c5', None), ('oppDone', False), ('oppPx', NA), ('oppBar', -1), ('cleaned', False), ('lns', None), ('lbs', None), ('bxs', None)])
Trade = ptype('Trade', [('id', NA), ('sell', False), ('entry', NA), ('stop', NA), ('tp1', NA), ('tpMain', NA), ('validUntil', NA), ('market', False), ('state', 0), ('risk', NA), ('remaining', 1.0), ('realized', 0.0), ('partialDone', False), ('legBar', -1), ('lab', None), ('mini', False), ('tip', ""), ('kind', ""), ('warn', ""), ('lns', None), ('lls', None), ('bxs', None)])
DRng = ptype('DRng', [('hi', NA), ('hiB', -1), ('hiWhy', ""), ('lo', NA), ('loB', -1), ('loWhy', ""), ('isNew', False), ('pHiBar', -1), ('pHiWhy', ""), ('pLoBar', -1), ('pLoWhy', "")])
Stats = ptype('Stats', [('signals', 0), ('closed', 0), ('wins', 0), ('losses', 0), ('totalR', 0.0), ('dayCount', 0), ('rejected', 0), ('liveLeg', -1), ('lastSig', -1), ('noteBarUp', -100), ('noteSlotUp', 0), ('noteBarDn', -100), ('noteSlotDn', 0), ('noteTxtUp', ""), ('noteTxtUpBar', -100), ('noteTxtDn', ""), ('noteTxtDnBar', -100)])


@functools.lru_cache(maxsize=400000)
def ny_parts(t_ms):
    d = datetime.fromtimestamp(t_ms / 1000, tz=timezone.utc).astimezone(NYZ)
    # Pine dayofweek: 1 = Sunday ... 7 = Saturday
    return (d.year, d.month, d.day, d.hour, d.minute, (d.isoweekday() % 7) + 1)


def year(t, tz=TZ): return ny_parts(int(t))[0]
def month(t, tz=TZ): return ny_parts(int(t))[1]
def dayofmonth(t, tz=TZ): return ny_parts(int(t))[2]
def hour(t, tz=TZ): return ny_parts(int(t))[3]
def minute(t, tz=TZ): return ny_parts(int(t))[4]
def dayofweek(t, tz=TZ): return ny_parts(int(t))[5]


def timestamp(tz, y, m, d, hh=0, mm=0):
    return int(datetime(y, m, d, hh, mm, tzinfo=NYZ).timestamp() * 1000)


def format_time(t, fmt="", tz=TZ):
    if na(t):
        return ""
    return datetime.fromtimestamp(t / 1000, tz=timezone.utc).astimezone(NYZ).strftime("%Y-%m-%d %H:%M")


def trading_day(t_ms):
    """FX daily candle (17:00 New York) the bar belongs to, as a date ordinal"""
    d = datetime.fromtimestamp(t_ms / 1000, tz=timezone.utc).astimezone(NYZ) + timedelta(hours=7)
    return d.date().toordinal()


def h4_key(t_ms):
    d = datetime.fromtimestamp(t_ms / 1000, tz=timezone.utc).astimezone(NYZ)
    m = d.date().toordinal() * 1440 + d.hour * 60 + d.minute - 17 * 60
    return m // 240


def load_5m(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append((int(r['time']) * 1000, float(r['open']), float(r['high']), float(r['low']), float(r['close']), int(r['spread'])))
    rows.sort()
    return rows


def aggregate(rows, keyf):
    """rows (t, o, h, l, c, ...) -> list of [key, t_first, o, h, l, c, [row indices]]"""
    out = []
    for idx, r in enumerate(rows):
        k = keyf(r[0])
        if out and out[-1][0] == k:
            b = out[-1]
            b[3] = max(b[3], r[2]); b[4] = min(b[4], r[3]); b[5] = r[4]; b[6].append(idx)
        else:
            out.append([k, r[0], r[1], r[2], r[3], r[4], [idx]])
    return out


def pivot_hi(h, k, left=1, right=1):
    """ta.pivothigh(high, left, right) evaluated at bar k (pivot at k-right): left strict, right >= (as the script's own LTF swings)"""
    c = k - right
    if c - left < 0 or k >= len(h):
        return NA
    v = h[c]
    for j in range(c - left, c):
        if not v > h[j]:
            return NA
    for j in range(c + 1, k + 1):
        if not v >= h[j]:
            return NA
    return v


def pivot_lo(l, k, left=1, right=1):
    c = k - right
    if c - left < 0 or k >= len(l):
        return NA
    v = l[c]
    for j in range(c - left, c):
        if not v < l[j]:
            return NA
    for j in range(c + 1, k + 1):
        if not v <= l[j]:
            return NA
    return v


def htf_trend(o, h, l, c):
    """f_htfTrend() on an HTF series; returns per HTF bar nz(state[1])"""
    state = 0; lastPH = NA; lastPL = NA; out = []; prev = 0
    for k in range(len(h)):
        hp = pivot_hi(h, k); lp = pivot_lo(l, k)
        if not na(hp): lastPH = hp
        if not na(lp): lastPL = lp
        if not na(lastPH) and c[k] > lastPH:
            state = 1; lastPH = NA
        elif not na(lastPL) and c[k] < lastPL:
            state = -1; lastPL = NA
        out.append(prev)
        prev = state
    return out


def htf_dr(h, l):
    """f_htfDr()"""
    hi = NA; lo = NA; out = []
    def g(a, k): return a[k] if k >= 0 else NA
    for k in range(len(h)):
        if g(h, k - 2) > g(h, k - 3) and g(h, k - 2) > g(h, k - 1):
            hi = pmax(g(h, k - 2), g(h, k - 1))
        elif not na(hi):
            hi = pmax(hi, g(h, k - 1))
        if g(l, k - 2) < g(l, k - 3) and g(l, k - 2) < g(l, k - 1):
            lo = pmin(g(l, k - 2), g(l, k - 1))
        elif not na(lo):
            lo = pmin(lo, g(l, k - 1))
        out.append((hi, lo))
    return out


def daily_ctx(o, h, l, c):
    """f_dailyCtx() -> per D bar (b, bT[1], bB[1], sT[1], sB[1], drHi, drLo, react)"""
    def g(a, k): return a[k] if k >= 0 else NA
    bT = bB = sT = sB = NA
    hbT, hbB, hsT, hsB = [], [], [], []
    drHi = drLo = NA
    out = []
    for k in range(len(h)):
        b = 1 if g(c, k - 1) > g(h, k - 2) else -1 if g(c, k - 1) < g(l, k - 2) else -1 if (g(h, k - 1) > g(h, k - 2) and g(c, k - 1) < g(h, k - 2)) else 1 if (g(l, k - 1) < g(l, k - 2) and g(c, k - 1) > g(l, k - 2)) else 0
        if l[k] > g(h, k - 2):
            bT = l[k]; bB = g(h, k - 2)
        if h[k] < g(l, k - 2):
            sT = g(l, k - 2); sB = h[k]
        if not na(bB) and c[k] < bB:
            bT = NA; bB = NA
        if not na(sT) and c[k] > sT:
            sT = NA; sB = NA
        if g(h, k - 2) > g(h, k - 3) and g(h, k - 2) > g(h, k - 1):
            drHi = pmax(g(h, k - 2), g(h, k - 1))
        elif not na(drHi):
            drHi = pmax(drHi, g(h, k - 1))
        if g(l, k - 2) < g(l, k - 3) and g(l, k - 2) < g(l, k - 1):
            drLo = pmin(g(l, k - 2), g(l, k - 1))
        elif not na(drLo):
            drLo = pmin(drLo, g(l, k - 1))
        sB2 = hsB[k - 2] if k >= 2 else NA; sT2 = hsT[k - 2] if k >= 2 else NA
        bB2 = hbB[k - 2] if k >= 2 else NA; bT2 = hbT[k - 2] if k >= 2 else NA
        react = -1 if (not na(sB2) and g(h, k - 1) >= sB2 and g(c, k - 1) < (sB2 + sT2) / 2) else 1 if (not na(bB2) and g(l, k - 1) <= bT2 and g(c, k - 1) > (bB2 + bT2) / 2) else 0
        out.append((b, hbT[k - 1] if k >= 1 else NA, hbB[k - 1] if k >= 1 else NA, hsT[k - 1] if k >= 1 else NA, hsB[k - 1] if k >= 1 else NA, drHi, drLo, react))
        hbT.append(bT); hbB.append(bB); hsT.append(sT); hsB.append(sB)
    return out


class Base:
    def __init__(self, path5m, cfg=None, start=None, end=None):
        cfg = cfg or {}
        self.cfg = cfg
        self.init_inputs(cfg)
        rows = load_5m(path5m)
        if start:
            rows = [r for r in rows if r[0] >= start]
        if end:
            rows = [r for r in rows if r[0] < end]
        self.rows5 = rows
        bars = aggregate(rows, lambda t: t // 900000)
        self.N = len(bars)
        self.O = [b[2] for b in bars]; self.H = [b[3] for b in bars]; self.L = [b[4] for b in bars]; self.C = [b[5] for b in bars]
        self.T = [b[0] * 900000 for b in bars]
        self.SPREAD = [rows[b[6][0]][5] for b in bars]
        self.LTF = [b[6] for b in bars]
        # ta.atr(14): RMA of true range (seeded with the SMA of the first 14)
        tr = []
        for i in range(self.N):
            if i == 0:
                tr.append(self.H[i] - self.L[i])
            else:
                pc = self.C[i - 1]
                tr.append(max(self.H[i] - self.L[i], abs(self.H[i] - pc), abs(self.L[i] - pc)))
        atr = [NA] * self.N
        for i in range(self.N):
            if i == 13:
                atr[i] = sum(tr[:14]) / 14
            elif i > 13:
                atr[i] = (atr[i - 1] * 13 + tr[i]) / 14
        self.ATR = atr
        # HTF: 4h (iHtf) and D candles from the 5m data, aligned to 17:00 New York
        def htf(keyf):
            hb = aggregate(rows, keyf)
            o = [b[2] for b in hb]; h = [b[3] for b in hb]; l = [b[4] for b in hb]; c = [b[5] for b in hb]
            keys = [b[0] for b in hb]
            return keys, o, h, l, c
        k4, o4, h4, l4, c4 = htf(h4_key)
        kd, od, hd, ld, cd = htf(trading_day)
        tr4 = htf_trend(o4, h4, l4, c4)
        trd = htf_trend(od, hd, ld, cd)
        dr4 = htf_dr(h4, l4)
        dctx = daily_ctx(od, hd, ld, cd)
        i4 = {k: j for j, k in enumerate(k4)}
        idd = {k: j for j, k in enumerate(kd)}
        self.HTF4 = []; self.HTFD = []
        for i in range(self.N):
            j4 = i4[h4_key(self.T[i])]; jd = idd[trading_day(self.T[i])]
            self.HTF4.append((tr4[j4], dr4[j4]))
            self.HTFD.append((trd[jd], dctx[jd]))
        self.DAYKEY = [trading_day(t) for t in self.T]
        self.WEEKKEY = [datetime.fromordinal(d).isocalendar()[:2] for d in self.DAYKEY]
        self.trlog = []      # one entry per closed / dropped trade (filled by the trade section)
        self.siglog = []     # one entry per signal

    def init_inputs(self, cfg):
        self.iMode = cfg.get('iMode', "Balanced")  # L11 string
        self.iMssSw = cfg.get('iMssSw', "Short-term swing (≈ LTF ITH/ITL)")  # L12 string
        self.iProfile = cfg.get('iProfile', "Custom (settings below)")  # L14 string
        self.iUseWin = cfg.get('iUseWin', True)  # L18 bool
        self.iMO = cfg.get('iMO', True)  # L19 bool
        self.iNoFvg = cfg.get('iNoFvg', "Market")  # L20 string
        self.iHtfFilter = cfg.get('iHtfFilter', "4h or daily")  # L21 string
        self.iBiasMode = cfg.get('iBiasMode', "Teacher")  # L22 string
        self.iMssMkt = cfg.get('iMssMkt', "Off")  # L23 string
        self.iNoFvgPd = cfg.get('iNoFvgPd', "Skip")  # L24 string
        self.iFvgDisp = cfg.get('iFvgDisp', True)  # L25 bool
        self.iRevDR = cfg.get('iRevDR', True)  # L26 bool
        self.iMOHard = cfg.get('iMOHard', True)  # L27 bool
        self.iUseSessLiq = cfg.get('iUseSessLiq', True)  # L28 bool
        self.iDR = cfg.get('iDR', True)  # L29 bool
        self.iDisp = cfg.get('iDisp', True)  # L30 bool
        self.iDispAtr = cfg.get('iDispAtr', 1.0)  # L31 float
        self.iPD = cfg.get('iPD', True)  # L32 bool
        self.iUB = cfg.get('iUB', True)  # L33 bool
        self.iUBPips = cfg.get('iUBPips', 10.0)  # L34 float
        self.iUBEq = cfg.get('iUBEq', True)  # L35 bool
        self.iHtfReq = cfg.get('iHtfReq', False)  # L36 bool
        self.iWarnTrend = cfg.get('iWarnTrend', True)  # L37 bool
        self.iUseMinStop = cfg.get('iUseMinStop', True)  # L38 bool
        self.iUseNews = cfg.get('iUseNews', True)  # L39 bool
        self.iZeroMode = cfg.get('iZeroMode', "Last swing")  # L40 string
        self.iSbEntry = cfg.get('iSbEntry', False)  # L41 bool
        self.iChain = cfg.get('iChain', True)  # L42 bool
        self.iSupersede = cfg.get('iSupersede', True)  # L43 bool
        self.iChainIth = cfg.get('iChainIth', True)  # L44 bool
        self.iHuntZone = cfg.get('iHuntZone', False)  # L45 bool
        self.iDispHunt = cfg.get('iDispHunt', True)  # L46 bool
        self.iAgainstLive = cfg.get('iAgainstLive', 0.0)  # L47 float
        self.iFS = cfg.get('iFS', True)  # L48 bool
        self.iFsOnly = cfg.get('iFsOnly', "Off")  # L49 string
        self.iFsBig = cfg.get('iFsBig', 0.0)  # L50 float
        self.iHunt = cfg.get('iHunt', True)  # L51 bool
        self.iUseSB = cfg.get('iUseSB', True)  # L56 bool
        self.iW1 = cfg.get('iW1', True)  # L59 bool
        self.sW1 = cfg.get('sW1', "0200-0500")  # L60 session
        self.iW2 = cfg.get('iW2', True)  # L61 bool
        self.sW2 = cfg.get('sW2', "0700-1000")  # L62 session
        self.iW3 = cfg.get('iW3', True)  # L63 bool
        self.sW3 = cfg.get('sW3', "1000-1100")  # L64 session
        self.iW4 = cfg.get('iW4', True)  # L65 bool
        self.sW4 = cfg.get('sW4', "1400-1500")  # L66 session
        self.sSB1 = cfg.get('sSB1', "0300-0400")  # L67 session
        self.sSB2 = cfg.get('sSB2', "1000-1100")  # L68 session
        self.sSB3 = cfg.get('sSB3', "1400-1500")  # L69 session
        self.sAsia = cfg.get('sAsia', "1900-0100")  # L72 session
        self.sLon = cfg.get('sLon', "0200-0700")  # L73 session
        self.sNYs = cfg.get('sNYs', "0700-1700")  # L74 session
        self.iSwingLB = cfg.get('iSwingLB', 200)  # L75 int
        self.iEqPips = cfg.get('iEqPips', 2.0)  # L76 float
        self.iPivot = cfg.get('iPivot', 1)  # L79 int
        self.iZ1a = cfg.get('iZ1a', 1.0)  # L80 float
        self.iZ1b = cfg.get('iZ1b', 1.5)  # L81 float
        self.iZ2a = cfg.get('iZ2a', 2.0)  # L82 float
        self.iZ2b = cfg.get('iZ2b', 2.5)  # L83 float
        self.iZ3a = cfg.get('iZ3a', 3.5)  # L84 float
        self.iZ3b = cfg.get('iZ3b', 4.0)  # L85 float
        self.iZ2Grace = cfg.get('iZ2Grace', True)  # L86 bool
        self.iLegAge = cfg.get('iLegAge', 192)  # L87 int
        self.iMinLeg = cfg.get('iMinLeg', 5.0)  # L88 float
        self.iMaxLegs = cfg.get('iMaxLegs', 3)  # L89 int
        self.iIthLB = cfg.get('iIthLB', 60)  # L92 int
        self.iEdge = cfg.get('iEdge', "CE (50%)")  # L93 string
        self.iLtf = cfg.get('iLtf', True)  # L94 bool
        self.iLtfTf = cfg.get('iLtfTf', "5")  # L95 timeframe
        self.iLtfMss = cfg.get('iLtfMss', False)  # L96 bool
        self.iShowFvg = cfg.get('iShowFvg', True)  # L97 bool
        self.iSlPips = cfg.get('iSlPips', 0.0)  # L98 float
        self.iTpBuf = cfg.get('iTpBuf', 0.2)  # L99 float
        self.iMinStop = cfg.get('iMinStop', 3.0)  # L100 float
        self.iValidMin = cfg.get('iValidMin', 120)  # L101 int
        self.iShowDR = cfg.get('iShowDR', False)  # L104 bool
        self.iDrLiq = cfg.get('iDrLiq', "External liquidity: previous day / week highs & lows")  # L107 string
        self.iDrUse = cfg.get('iDrUse', "Dealing range on the chart (BSL ↔ SSL)")  # L108 string
        self.iShowLDR = cfg.get('iShowLDR', True)  # L109 bool
        self.iLdrN = cfg.get('iLdrN', 1)  # L110 int
        self.iLdrFill = cfg.get('iLdrFill', "Right of price")  # L111 string
        self.iTgtMode = cfg.get('iTgtMode', "Dealing range + SDP zones")  # L117 string
        self.iTgtLiq = cfg.get('iTgtLiq', True)  # L118 bool
        self.iTgt = cfg.get('iTgt', 2.0)  # L119 float
        self.iPart = cfg.get('iPart', 1.0)  # L120 float
        self.iPartFrac = cfg.get('iPartFrac', 0.6)  # L121 float
        self.iMaxRR = cfg.get('iMaxRR', 4.0)  # L122 float
        self.iMinRR = cfg.get('iMinRR', 1.0)  # L123 float
        self.iUse3PD = cfg.get('iUse3PD', True)  # L126 bool
        self.iUseHTF = cfg.get('iUseHTF', True)  # L127 bool
        self.iHtf = cfg.get('iHtf', "240")  # L128 timeframe
        self.iUseSMT = cfg.get('iUseSMT', True)  # L129 bool
        self.iSmtSym = cfg.get('iSmtSym', "FOREXCOM:GBPUSD")  # L130 symbol
        self.iSmtInv = cfg.get('iSmtInv', False)  # L131 bool
        self.iPipOvr = cfg.get('iPipOvr', 0.0)  # L132 float
        self.iNewsOn = cfg.get('iNewsOn', True)  # L135 bool
        self.iFomc = cfg.get('iFomc', True)  # L136 bool
        self.iNewsList = cfg.get('iNewsList', "")  # L137 text_area
        self.iNewsBefore = cfg.get('iNewsBefore', 60)  # L138 int
        self.iNewsAfter = cfg.get('iNewsAfter', 60)  # L139 int
        self.iNewsDay = cfg.get('iNewsDay', True)  # L140 bool
        self.iMajorAfter = cfg.get('iMajorAfter', 720)  # L141 int
        self.iNewsClose = cfg.get('iNewsClose', True)  # L142 bool
        self.iPass = cfg.get('iPass', "change-me")  # L145 string
        self.iMinGrade = cfg.get('iMinGrade', "B")  # L146 string
        self.iAlUpdates = cfg.get('iAlUpdates', True)  # L147 bool
        self.iAlFmt = cfg.get('iAlFmt', "Text (phone / popup)")  # L148 string
        self.iShowLegs = cfg.get('iShowLegs', True)  # L151 bool
        self.iShowBoxes = cfg.get('iShowBoxes', True)  # L152 bool
        self.iShowMss = cfg.get('iShowMss', True)  # L153 bool
        self.iMssDraw = cfg.get('iMssDraw', True)  # L154 bool
        self.iFibTv = cfg.get('iFibTv', False)  # L155 bool
        self.iFibLen = cfg.get('iFibLen', 0)  # L156 int
        self.iView = cfg.get('iView', "Clean")  # L157 string
        self.iTxtSize = cfg.get('iTxtSize', "Normal")  # L158 string
        self.iSigSize = cfg.get('iSigSize', "Normal")  # L159 string
        self.iNoteSize = cfg.get('iNoteSize', "Tiny")  # L160 string
        self.iDashSize = cfg.get('iDashSize', "Small")  # L161 string
        self.iDashPos = cfg.get('iDashPos', "Top right")  # L162 string
        self.iFibLeft = cfg.get('iFibLeft', False)  # L163 bool
        self.iHist = cfg.get('iHist', "All legs")  # L164 string
        self.iHistN = cfg.get('iHistN', 20)  # L165 int
        self.iShowTrade = cfg.get('iShowTrade', True)  # L166 bool
        self.iShowMO = cfg.get('iShowMO', True)  # L167 bool
        self.iShowWin = cfg.get('iShowWin', True)  # L168 bool
        self.iShowRej = cfg.get('iShowRej', False)  # L169 bool
        self.iNotesN = cfg.get('iNotesN', 3)  # L170 int
        self.iDrawDays = cfg.get('iDrawDays', 2)  # L171 int
        self.iCompact = cfg.get('iCompact', True)  # L172 bool
        self.iOldSig = cfg.get('iOldSig', True)  # L173 bool
        self.iOldLbl = cfg.get('iOldLbl', False)  # L174 bool
        self.iOldCanc = cfg.get('iOldCanc', False)  # L175 bool
        self.iShowDash = cfg.get('iShowDash', True)  # L176 bool
        self.iLineBars = cfg.get('iLineBars', 20)  # L177 int
        self.iDayLine = cfg.get('iDayLine', "NY midnight")  # L178 string
        self.iOneSwing = cfg.get('iOneSwing', False)  # L182 bool
        self.iTfLock = cfg.get('iTfLock', True)  # L184 bool
        self.iSimple = cfg.get('iSimple', True)  # L186 bool
        self.iOnRetrace = cfg.get('iOnRetrace', False)  # L187 bool
        self.iMktEntry = cfg.get('iMktEntry', False)  # L188 bool
        # derived (lines 13-191, 369-386 of the Pine)
        self.MSS_SHORT = self.iMssSw == "Short-term swing (≈ LTF ITH/ITL)"
        self.BEST = self.iProfile == "More signals"
        self.STRICT = self.iMode == "Strict (notes)"
        self.DRL_ANY = "Any swing high / low (same timeframe)"
        self.DRL_EXT = "External liquidity: previous day / week highs & lows"
        self.iDrExt = cfg.get("iDrExt", False)   # first external-range version (removed from the Pine); kept here only for comparison runs
        self.DRU_CHART = "Dealing range on the chart (BSL ↔ SSL)"
        self.TGT_DR = "Dealing range + SDP zones"
        self.TZ = TZ
        self.DRAW = True          # drawing is not simulated
        self.TFOK = True          # 15m chart
        self.MOF = self.iMO and not self.iSimple
        self.AGL = -1.0 if self.iSimple else self.iAgainstLive
        self.HTFF = "Off" if self.iSimple else self.iHtfFilter
        self.iClean = self.iView == "Clean"
        self.TK = "EURUSD"
        self.isFX = True
        self.PIP = self.iPipOvr if self.iPipOvr > 0 else 0.0001
        self.TF_MIN = 15
        self.validBars = max(1, int(math.ceil(float(480 if self.BEST else self.iValidMin) / self.TF_MIN)))
        self.useDR = self.iDR
        self.useHZ = self.iHuntZone and not self.BEST
        self.barsPerDay = min(480, int(1440 / self.TF_MIN))
        self.timeframe_period = "15"
        self.timeframe_in_seconds = 900
        self.usedStops = PArr()
        self.hsHB = PArr(); self.hsHP = PArr(); self.hsLB = PArr(); self.hsLP = PArr()
        self.iUseSMT_data = False   # no GBPUSD data: SMT (grade only) never confirms

    # ---- per bar, Pine lines 1-555 ----
    def prelude(self, i):
        self.bar_index = i
        self.open = self.O[i]; self.high = self.H[i]; self.low = self.L[i]; self.close = self.C[i]
        self.time = self.T[i]; self.time_close = self.T[i] + 900000
        self.barstate_isfirst = i == 0
        self.barstate_islast = i == self.N - 1
        self.change_D = i > 0 and self.DAYKEY[i] != self.DAYKEY[i - 1]
        self.change_W = i > 0 and self.WEEKKEY[i] != self.WEEKKEY[i - 1]
        self.mod = hour(self.time) * 60 + minute(self.time)
        self.calKey = self.f_dateKey(self.time)
        self.atr14 = self.ATR[i]
        self.rngHi = max(self.H[i - 29:i + 1]) if i >= 29 else NA
        self.rngLo = min(self.L[i - 29:i + 1]) if i >= 29 else NA
        self.ph = pivot_hi(self.H, i, self.iPivot, self.iPivot)
        self.pl = pivot_lo(self.L, i, self.iPivot, self.iPivot)
        (self.htfTrend, (self.h4DrHi, self.h4DrLo)) = self.HTF4[i]
        (self.dTrend, (self.dBiasS, self.dBT, self.dBB, self.dST, self.dSB, self.dDrHi, self.dDrLo, self.dReact)) = self.HTFD[i]
        self.dDrOk = not na(self.dDrHi) and not na(self.dDrLo) and self.dDrHi > self.dDrLo
        self.dDrEq = (self.dDrHi + self.dDrLo) / 2 if self.dDrOk else NA
        self.dBias = self.dBiasS if self.iBiasMode == "Simple" else (self.dReact if self.dReact != 0 else ((-1 if self.close > self.dDrEq else 1) if self.dDrOk else 0))
        self.smtH = self.high; self.smtL = self.low   # SMT symbol not available
        idx = self.LTF[i]
        r5 = self.rows5
        self.lH = PArr(r5[k][2] for k in idx); self.lL = PArr(r5[k][3] for k in idx); self.lC = PArr(r5[k][4] for k in idx)
        self.lT = PArr(r5[k][0] for k in idx); self.lO = PArr(r5[k][1] for k in idx)

    # history of built-ins: x[k]
    def o_(self, k): j = self.bar_index - int(k); return self.O[j] if 0 <= j <= self.bar_index else NA
    def h_(self, k): j = self.bar_index - int(k); return self.H[j] if 0 <= j <= self.bar_index else NA
    def l_(self, k): j = self.bar_index - int(k); return self.L[j] if 0 <= j <= self.bar_index else NA
    def c_(self, k): j = self.bar_index - int(k); return self.C[j] if 0 <= j <= self.bar_index else NA
    def t_(self, k): j = self.bar_index - int(k); return self.T[j] if 0 <= j <= self.bar_index else NA
    def atr_(self, k): j = self.bar_index - int(k); return self.ATR[j] if 0 <= j <= self.bar_index else NA
    def smtH_(self, k): return self.h_(k)
    def smtL_(self, k): return self.l_(k)

    # ---- Pine helper functions, lines 362-480 ----
    def f_hm(self, s, pos): return int(s[pos:pos + 2])
    def f_sStart(self, s): return self.f_hm(s, 0) * 60 + self.f_hm(s, 2)
    def f_sEnd(self, s): return self.f_hm(s, 5) * 60 + self.f_hm(s, 7)
    def f_in(self, m, s, e): return (m >= s and m < e) if e > s else (m >= s or m < e)
    def f_dateKey(self, t): return year(t) * 10000 + month(t) * 100 + dayofmonth(t)
    def f_key(self, s, e): return self.f_dateKey(self.time - e * 60000 if e <= s else self.time)
    def f_num(self, v): return "null" if na(v) else ("%.5f" % v)
    def f_q(self, s): return '"' + s + '"'
    def f_b(self, b): return "true" if b else "false"
    def f_gradeRank(self, g): return 2 if g == "A+" else 1 if g == "A" else 0
    def f_fib(self, lg, k): return lg.zero + k * (lg.one - lg.zero)
    def f_lvl(self, lg, k): return self.f_fib(lg, -k)
    def f_beyond(self, bear, px, lvl): return px < lvl if bear else px > lvl
    def f_reach(self, bear, ext, lvl): return ext <= lvl if bear else ext >= lvl

    def f_lastBefore(self, bars, prices, x):
        r = NA
        n = bars.size()
        if n > 0:
            for i in prange(n - 1, 0):
                if bars.get(i) < x:
                    r = prices.get(i)
                    break
        return r

    def f_lastBarBefore(self, bars, x):
        r = -1
        n = bars.size()
        if n > 0:
            for i in prange(n - 1, 0):
                if bars.get(i) < x:
                    r = bars.get(i)
                    break
        return r

    def f_huntOrigin(self, bars, prices, x, lowSwings):
        zp = NA
        zb = -1
        n = bars.size()
        last = -1
        if n > 0:
            for k in prange(n - 1, 0):
                if bars.get(k) < x:
                    last = k
                    break
        if last >= 0:
            zp = prices.get(last)
            zb = bars.get(last)
            done = False
            if self.iZeroMode == "Previous stop hunt":
                hb = self.hsLB if lowSwings else self.hsHB
                hp = self.hsLP if lowSwings else self.hsHP
                m = hb.size()
                if m > 0:
                    for k in prange(m - 1, 0):
                        b = hb.get(k)
                        if b < x:
                            if x - b <= self.iSwingLB:
                                zp = hp.get(k)
                                zb = b
                                for j in prange(0, last):
                                    if bars.get(j) > b and (prices.get(j) < zp if lowSwings else prices.get(j) > zp):
                                        zp = prices.get(j)
                                        zb = bars.get(j)
                                done = True
                            break
            if not done and self.iZeroMode != "Last swing" and last >= 1:
                for k in prange(last, max(1, last - 20)):
                    pk = prices.get(k)
                    pp = prices.get(k - 1)
                    if (pk < pp) if lowSwings else (pk > pp):
                        zp = pk
                        zb = bars.get(k)
                        break
        return [zp, zb]

    def f_cisdAt(self, ox, bearishDelivery):
        lvl = self.o_(ox)
        j = -1
        for k in prange(ox, ox + 2):
            d = (self.c_(k) > self.o_(k)) if bearishDelivery else (self.c_(k) < self.o_(k))
            if d:
                j = k
                break
        if j >= 0:
            first = j
            for k in prange(j + 1, ox + 10):
                d = (self.c_(k) > self.o_(k)) if bearishDelivery else (self.c_(k) < self.o_(k))
                if d:
                    first = k
                else:
                    break
            lvl = self.o_(first)
        return lvl
