"""Port of MZ_SDP.pine lines 556-899 (globals, news, levels, sessions, FVGs, LTF candles / swings / gaps, sweeps, DR helpers).

See PORTING.md. Drawing (NY Open lines / labels, FVG boxes) is dropped; every state change the logic reads is kept.
"""
import re
from base import *


def _pts(y, mo, d, hh, mi):
    """Pine timestamp(TZ, y, mo, d, hh, mi) for the manual news list. Valid dates -> base.timestamp; an out-of-range
    month / day / hour / minute is rolled over (wall clock in New York) instead of raising."""
    try:
        return timestamp(TZ, y, mo, d, hh, mi)
    except ValueError:
        y2 = y + (mo - 1) // 12
        m2 = (mo - 1) % 12 + 1
        dt = datetime(y2, m2, 1, tzinfo=NYZ) + timedelta(days=d - 1, hours=hh, minutes=mi)
        return int(dt.timestamp() * 1000)


class Sec1:
    # ---- L556-579: var state ----
    def init_556(self):
        self.levels = PArr()        # array<Level>
        self.sweeps = PArr()        # array<Sweep>
        self.gaps = PArr()          # array<Gap>
        self.hunts = PArr()         # array<Hunt>
        self.fsq = PArr()           # array<Hunt>
        self.trades = PArr()        # array<Trade>
        self.shB = PArr()
        self.shP = PArr()
        self.slB = PArr()
        self.slP = PArr()
        self.ithB = PArr()
        self.ithP = PArr()
        self.itlB = PArr()
        self.itlP = PArr()
        self.newsTimes = PArr()
        self.newsFrom = PArr()
        self.newsTo = PArr()
        self.st = Stats()
        self.bearLegs = PArr()      # array<Leg>
        self.bullLegs = PArr()      # array<Leg>
        self.usedFvg = PArr()
        self.ssAsia = Sess()
        self.ssLon = Sess()
        self.ssNY = Sess()

    # ---- L581-589: built-in FOMC days (no trade that NY day) ----
    def top_581(self):
        if self.barstate_isfirst and self.iFomc:
            for d in afrom("2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10", "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09"):
                fy = int(d[0:4])
                fm = int(d[5:7])
                fd = int(d[8:10])
                ft = timestamp(TZ, fy, fm, fd, 14, 0)
                self.newsTimes.push(ft)
                self.newsFrom.push(timestamp(TZ, fy, fm, fd, 0, 0) if self.iNewsDay else ft - self.iNewsBefore * 60000)
                self.newsTo.push(ft + pmax(self.iNewsAfter, self.iMajorAfter) * 60000)

    # ---- L591-611: manual red-news list ----
    def top_591(self):
        if self.barstate_isfirst and self.iNewsOn and len(self.iNewsList) > 0:
            rows = PArr(self.iNewsList.replace(",", "\n").split("\n"))
            for r in rows:
                m = re.search(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}", r)
                s = m.group(0) if m else ""
                if len(s) == 16:
                    y = int(s[0:4])
                    mo = int(s[5:7])
                    d = int(s[8:10])
                    hh = int(s[11:13])
                    mi = int(s[14:16])
                    if not na(y) and not na(mo) and not na(d) and not na(hh) and not na(mi):
                        nt = _pts(y, mo, d, hh, mi)
                        up = r.upper()
                        major = ("CPI" in up) or ("NFP" in up) or ("NON-FARM" in up) or ("FOMC" in up) or ("RATE" in up)
                        fromT = nt - self.iNewsBefore * 60000
                        toT = nt + (pmax(self.iNewsAfter, self.iMajorAfter) if major else self.iNewsAfter) * 60000
                        if major and self.iNewsDay:
                            fromT = pmin(fromT, _pts(y, mo, d, 0, 0))
                        self.newsTimes.push(nt)
                        self.newsFrom.push(fromT)
                        self.newsTo.push(toT)

    # L613
    def f_newsAt(self, t):
        r = ""
        if self.newsTimes.size() > 0:
            for i in prange(0, self.newsTimes.size() - 1):
                if t >= self.newsFrom.get(i) and t <= self.newsTo.get(i):
                    r = "red news " + format_time(self.newsTimes.get(i), "yyyy-MM-dd HH:mm", TZ) + " NY"
                    break
        return r

    # L622
    def f_removeLevels(self, kind, prefix):
        n = self.levels.size()
        if n > 0:
            for i in prange(n - 1, 0):
                l = self.levels.get(i)
                if l.kind == kind and (prefix == "" or l.name.startswith(prefix)):
                    self.levels.remove(i)
        return n

    # ---- L631-646: NY midnight open (lines / labels dropped) ----
    def init_631(self):
        self.midOpen = NA
        self.curCal = NA

    def top_635(self):
        if na(self.curCal) or self.calKey != self.curCal:
            self.curCal = self.calKey
            if self.mod < 60:
                self.midOpen = self.open
        # L645-646: NY Open line extension - drawing only

    # ---- L648-680: day / week highs and lows -> PDH / PDL / PWH / PWL ----
    def init_648(self):
        self.dH = NA
        self.dL = NA
        self.dHB = 0
        self.dLB = 0
        self.wH = NA
        self.wL = NA
        self.wHB = 0
        self.wLB = 0

    def top_656(self):
        if self.bar_index > 0 and self.change_D and not na(self.dH):
            self.f_removeLevels("day", "")
            self.levels.push(Level("PDH", self.dH, self.dHB, True, "day"))
            self.levels.push(Level("PDL", self.dL, self.dLB, False, "day"))
            self.dH = NA
            self.dL = NA
            self.st.dayCount = 0
        if self.bar_index > 0 and self.change_W and not na(self.wH):
            self.f_removeLevels("week", "")
            self.levels.push(Level("PWH", self.wH, self.wHB, True, "week"))
            self.levels.push(Level("PWL", self.wL, self.wLB, False, "week"))
            self.wH = NA
            self.wL = NA
        if na(self.dH) or self.high > self.dH:
            self.dH = self.high
            self.dHB = self.bar_index
        if na(self.dL) or self.low < self.dL:
            self.dL = self.low
            self.dLB = self.bar_index
        if na(self.wH) or self.high > self.wH:
            self.wH = self.high
            self.wHB = self.bar_index
        if na(self.wL) or self.low < self.wL:
            self.wL = self.low
            self.wLB = self.bar_index

    # L682: session high / low; when the session ends its high / low become levels
    def f_sess(self, s, sess, name):
        a = self.f_sStart(sess)
        e = self.f_sEnd(sess)
        inside = self.f_in(self.mod, a, e)
        key = self.f_key(a, e)
        if s.active and (not inside or ne(key, s.key)):
            self.f_removeLevels("session", name + " ")
            if self.iUseSessLiq:
                self.levels.push(Level(name + " High", s.hi, s.hiBar, True, "session"))
                self.levels.push(Level(name + " Low", s.lo, s.loBar, False, "session"))
            s.active = False
        if inside:
            if not s.active:
                s.active = True
                s.key = key
                s.hi = self.high
                s.lo = self.low
                s.hiBar = self.bar_index
                s.loBar = self.bar_index
            else:
                if self.high > s.hi:
                    s.hi = self.high
                    s.hiBar = self.bar_index
                if self.low < s.lo:
                    s.lo = self.low
                    s.loBar = self.bar_index
        return inside

    # ---- L710-712 ----
    def top_710(self):
        self.f_sess(self.ssAsia, self.sAsia, "Asia")
        self.f_sess(self.ssLon, self.sLon, "London")
        self.f_sess(self.ssNY, self.sNYs, "NY")

    # ---- L714-731: chart FVGs + lower-timeframe settings ----
    def top_714(self):
        if self.bar_index >= 2:
            if self.low > self.h_(2):
                self.gaps.push(Gap(self.bar_index, self.low, self.h_(2), True))
            elif self.high < self.l_(2):
                self.gaps.push(Gap(self.bar_index, self.l_(2), self.high, False))
        if self.gaps.size() > 80:
            self.gaps.shift()
        for g in self.gaps:
            if g.bar < self.bar_index and not g.filled:
                if (g.bull and self.close < g.bottom) or (not g.bull and self.close > g.top):
                    g.filled = True

        # timeframe.in_seconds() = 900 (15m chart); timeframe.in_seconds(iLtfTf) = 300 (the engine's LTF data is 5m)
        tfSec = self.timeframe_in_seconds
        ltfSec = 300
        self.LTF_DATA = (self.iLtf or self.iLtfMss) and tfSec > ltfSec
        self.LTF_ON = self.LTF_DATA and self.iLtf
        self.LTF_MSS = self.LTF_DATA and self.iLtfMss
        self.LTF_MS = ltfSec * 1000
        self.LTF_N = pmax(1, int(tfSec / pmax(1, ltfSec)))
        # L731 [lH, lL, lC, lT, lO] = request.security_lower_tf(...): filled by Base.prelude (self.lH / lL / lC / lT / lO)
        # with the 5m candles; when LTF_DATA is false Pine requests the chart timeframe -> one element (this bar)
        if not self.LTF_DATA:
            self.lH = afrom(self.high)
            self.lL = afrom(self.low)
            self.lC = afrom(self.close)
            self.lT = afrom(self.time)
            self.lO = afrom(self.open)

    # ---- L732-755: lower-timeframe state ----
    def init_732(self):
        self.l5h = PArr()
        self.l5l = PArr()
        self.l5t = PArr()
        self.l5b = PArr()
        self.gaps5 = PArr()         # array<Gap>
        self.used5 = PArr()
        # lower-timeframe candles for the stop hunt + MSS at the zone; an LTF candle's running index is n5 - size + position
        self.x5h = PArr()
        self.x5l = PArr()
        self.x5o = PArr()
        self.x5c = PArr()
        self.x5a = PArr()
        self.x5t = PArr()
        self.x5b = PArr()
        self.n5 = 0
        self.atr5 = NA
        self.s5hI = PArr()
        self.s5hP = PArr()
        self.s5lI = PArr()
        self.s5lP = PArr()
        self.i5hI = PArr()
        self.i5hP = PArr()
        self.i5lI = PArr()
        self.i5lP = PArr()

    # L756
    def f_p5(self, gi):
        return gi - (self.n5 - self.x5h.size())

    # L757
    def f_bar5(self, gi, fb):
        pos = self.f_p5(gi)
        return self.x5b.get(pos) if (pos >= 0 and pos < self.x5b.size()) else fb

    # L760: LTF swing; a swing higher (lower) than its neighbours is an LTF ITH (ITL)
    def f_on5Swing(self, gi, p, isHigh):
        sb = self.s5hI if isHigh else self.s5lI
        sp = self.s5hP if isHigh else self.s5lP
        ib = self.i5hI if isHigh else self.i5lI
        ip = self.i5hP if isHigh else self.i5lP
        sb.push(gi)
        sp.push(p)
        n = sb.size()
        if n >= 3:
            p1 = sp.get(n - 2)
            if ((p1 > sp.get(n - 3) and p1 > p) if isHigh else (p1 < sp.get(n - 3) and p1 < p)):
                ib.push(sb.get(n - 2))
                ip.push(p1)
        if sb.size() > 300:
            sb.shift()
            sp.shift()
        if ib.size() > 300:
            ib.shift()
            ip.shift()
        return n

    # ---- L780-831: walk the LTF candles of this chart bar: candle arrays, ATR, swings, LTF FVGs ----
    def top_780(self):
        if self.LTF_DATA and self.lH.size() > 0:
            for j in prange(0, self.lH.size() - 1):
                hh = self.lH.get(j)
                ll = self.lL.get(j)
                cc = self.lC.get(j)
                if self.LTF_MSS:
                    pc = self.x5c.last() if self.x5c.size() > 0 else NA
                    tr5 = (hh - ll) if na(pc) else pmax(hh - ll, pabs(hh - pc), pabs(ll - pc))
                    self.atr5 = tr5 if na(self.atr5) else (self.atr5 * 13 + tr5) / 14
                    self.x5h.push(hh)
                    self.x5l.push(ll)
                    self.x5o.push(self.lO.get(j))
                    self.x5c.push(cc)
                    self.x5a.push(self.atr5)
                    self.x5t.push(self.lT.get(j))
                    self.x5b.push(self.bar_index)
                    self.n5 += 1
                    if self.x5h.size() > 1000:
                        self.x5h.shift()
                        self.x5l.shift()
                        self.x5o.shift()
                        self.x5c.shift()
                        self.x5a.shift()
                        self.x5t.shift()
                        self.x5b.shift()
                    s = self.x5h.size()
                    if s >= 3:
                        mh = self.x5h.get(s - 2)
                        ml = self.x5l.get(s - 2)
                        if mh > self.x5h.get(s - 3) and mh >= hh:
                            self.f_on5Swing(self.n5 - 2, mh, True)
                        if ml < self.x5l.get(s - 3) and ml <= ll:
                            self.f_on5Swing(self.n5 - 2, ml, False)
                for g in self.gaps5:
                    if not g.filled and ((cc < g.bottom) if g.bull else (cc > g.top)):
                        g.filled = True
                self.l5h.push(hh)
                self.l5l.push(ll)
                self.l5t.push(self.lT.get(j))
                self.l5b.push(self.bar_index)
                if self.l5h.size() > 3:
                    self.l5h.shift()
                    self.l5l.shift()
                    self.l5t.shift()
                    self.l5b.shift()
                if self.l5h.size() == 3:
                    if ll > self.l5h.get(0):
                        self.gaps5.push(Gap(self.bar_index, ll, self.l5h.get(0), True, False, True, self.l5t.get(0), self.lT.get(j), self.l5b.get(0)))
                    elif hh < self.l5l.get(0):
                        self.gaps5.push(Gap(self.bar_index, self.l5l.get(0), hh, False, False, True, self.l5t.get(0), self.lT.get(j), self.l5b.get(0)))
            while self.gaps5.size() > 150:
                self.gaps5.shift()

    # L833
    def f_gapEntry(self, g, buy):
        return ((g.top if buy else g.bottom) if self.iEdge == "Proximal" else (g.top + g.bottom) / 2)

    # L834
    def f_drOk(self, px, buy, drEq):
        return (not self.useDR) or na(drEq) or ((px < drEq) if buy else (px > drEq))

    # L837: fromT > 0: setup found on the lower timeframe - its FVG starts at the LTF extreme (the hunt candle may be the middle one)
    def f_best5(self, gapBull, fromBar, eq, ceRule, toBar, fromT, drEq):
        best = None
        if (self.LTF_ON or fromT > 0) and self.gaps5.size() > 0:
            for g in self.gaps5:
                startOk = (g.t1 + (self.LTF_MS if self.iDispHunt else 0) >= fromT) if fromT > 0 else (g.b0 >= fromBar)
                if startOk and g.bar <= toBar and not g.filled and g.bull == gapBull and not self.used5.includes(g.t2) and self.f_drOk(self.f_gapEntry(g, gapBull), gapBull, drEq):
                    ce = (g.top + g.bottom) / 2
                    pdOk = (not self.iPD) or (((ce <= eq) if ceRule else (g.bottom <= eq)) if gapBull else ((ce >= eq) if ceRule else (g.top >= eq)))
                    if pdOk and (best is None or ((g.top > best.top) if gapBull else (g.bottom < best.bottom))):
                        best = g
        return best

    # L848
    def f_useGap(self, g, buy):
        if g.ltf and not g.nofvg:
            self.used5.push(g.t2)
            if self.used5.size() > 100:
                self.used5.shift()
        elif not g.nofvg:
            self.usedFvg.push(g.bar if buy else -g.bar)
            if self.usedFvg.size() > 100:
                self.usedFvg.shift()
        return g.bar

    # L859: no FVG in the displacement leg -> entry at market / MSS level / 50% (never on the wrong side of the 50%)
    def f_noFvg(self, gapBull, farBar, mssPx, eq):
        g = None
        if self.iNoFvg != "Off" and farBar < self.bar_index:
            px = self.close if self.iNoFvg == "Market" else (mssPx if self.iNoFvg == "MSS level" else eq)
            if not na(px) and ((px > eq) if gapBull else (px < eq)):
                px = NA if self.iNoFvgPd == "Skip" else (eq if self.iNoFvgPd == "Clamp to 50%" else px)
            if not na(px):
                g = Gap(self.bar_index, px, px, gapBull, nofvg=True)
        return g

    # L869: drawing only (FVG box / no-FVG line); returns g.bar like the Pine
    def f_drawFvg(self, g, buy):
        return g.bar

    # ---- L881-893: liquidity sweeps of this bar ----
    def top_881(self):
        self.sweptNow = PArr()      # non-var: new each bar
        if self.levels.size() > 0:
            for i in prange(self.levels.size() - 1, 0):
                l = self.levels.get(i)
                if not l.swept and l.bar < self.bar_index and not na(l.price):
                    if (l.bsl and self.high > l.price) or (not l.bsl and self.low < l.price):
                        l.swept = True
                        self.sweptNow.unshift(Sweep(self.bar_index, l.bsl, l.name, l.kind, l.price))
                        self.levels.remove(i)
        for sw in self.sweptNow:
            self.sweeps.push(sw)
        while self.sweeps.size() > 0 and self.sweeps.first().bar < self.bar_index - 10:
            self.sweeps.shift()

    # ---- L895: dealing range ----
    def init_895(self):
        self.dr = DRng()

    # L896
    def top_896(self):
        self.DR_CHART = self.iDrUse == self.DRU_CHART

    # L897
    def f_drReady(self):
        return not na(self.dr.hi) and not na(self.dr.lo) and self.dr.hi > self.dr.lo

    # L898
    def f_drLiq(self, sw):
        if self.iDrLiq == self.DRL_EXT:
            return sw.kind == "day" or sw.kind == "week"
        return self.iDrLiq == self.DRL_ANY or sw.kind != "swing" or sw.name.startswith("Equal") or sw.name.startswith("Hunt")

    # L899
    def f_addWhy(self, w, nm):
        return w if (nm in w) else (nm if w == "" else w + ", " + nm)
