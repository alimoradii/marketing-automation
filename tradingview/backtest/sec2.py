"""Section 2 of the MZ_SDP.pine port: Pine lines 900-1253.

dealing-range pending grabs from sweptNow, f_inter, f_onSwing (swings, ITH/ITL, equal highs/lows, failure swing queue,
dealing-range turn credit, hunts), the ph/pl swing calls, swing level cleanup, day lines (drawing only), f_drawMss (no-op),
leg drawing helpers (only the state they keep), zr* reversal-zone memory, f_zoneHit, f_inPriorZone, f_oppHunt,
f_drTarget, f_mainTarget, f_revEq.
"""
from base import *

# Pine commit bedea9e ("dealing range from external liquidity") added these DRng fields (Pine L340-348 now) and the
# input iDrExt (Pine L109 now); base.py predates it, so they are added here (no-op once base.py has them).
# Method names below keep the pre-bedea9e line numbers (as sec1 / sec3 / sec4 do) so the run order is unchanged.
for _f in (('cHi', NA), ('cHiB', -1), ('cHiWhy', ""), ('cLo', NA), ('cLoB', -1), ('cLoWhy', "")):
    if _f[0] not in dict(DRng._fields):
        DRng._fields = DRng._fields + (_f,)


class Sec2:
    # ---- input iDrExt (Pine L109 since bedea9e, default true; false = the previous behaviour) ----
    def init_109(self):
        if not hasattr(self, 'iDrExt'):
            self.iDrExt = self.cfg.get('iDrExt', True)

    # ---- L900-908: a grab of buy-side / sell-side liquidity waits for the swing where price turns (see f_onSwing) ----
    def top_901(self):
        dr = self.dr
        for sw in self.sweptNow:
            if self.f_drLiq(sw):
                if sw.bsl:
                    dr.pHiBar = sw.bar if dr.pHiBar < 0 else dr.pHiBar
                    dr.pHiWhy = self.f_addWhy(dr.pHiWhy, sw.name)
                else:
                    dr.pLoBar = sw.bar if dr.pLoBar < 0 else dr.pLoBar
                    dr.pLoWhy = self.f_addWhy(dr.pLoWhy, sw.name)

    # ---- L910 ----
    def f_inter(self, ib, ip, b, p):
        dup = False
        n = ib.size()
        if n > 0:
            for k in prange(n - 1, max(0, n - 3)):
                if ib.get(k) == b:
                    dup = True
        if not dup:
            ib.push(b)
            ip.push(p)
        return dup

    # ---- L922 ----
    def f_onSwing(self, i, price, isHigh):
        sb = self.shB if isHigh else self.slB
        sp = self.shP if isHigh else self.slP
        sb.push(i)
        sp.push(price)
        if sb.size() > 300:
            sb.shift()
            sp.shift()
        ib = self.ithB if isHigh else self.itlB
        ip = self.ithP if isHigh else self.itlP
        n = sb.size()
        if n >= 3:
            p0 = sp.get(n - 3)
            p1 = sp.get(n - 2)
            p2 = sp.get(n - 1)
            if (isHigh and p1 > p0 and p1 > p2) or (not isHigh and p1 < p0 and p1 < p2):
                b1 = sb.get(n - 2)
                self.f_inter(ib, ip, b1, p1)
                # note: no l.bsl test in the Pine (a swing level of either side at bar b1 is renamed)
                for l in self.levels:
                    if l.kind == "swing" and l.bar == b1 and not l.name.startswith("Equal") and not l.name.startswith("Hunt"):
                        l.name = "ITH" if isHigh else "ITL"
        # a swing that trades into an unfilled opposite FVG and closes back out of it is an intermediate swing too
        gs = self.gaps.size()
        if gs > 0:
            for k in prange(max(0, gs - 40), gs - 1):
                g = self.gaps.get(k)
                if g.bar < i and not g.filled:
                    ci = self.c_(self.bar_index - i)
                    if (isHigh and not g.bull and price >= g.bottom and ci <= g.top) or (not isHigh and g.bull and price <= g.top and ci >= g.bottom):
                        self.f_inter(ib, ip, i, price)
                        break
        if ib.size() > 300:
            ib.shift()
            ip.shift()
        nm = "Swing High" if isHigh else "Swing Low"
        if ib.size() > 0 and ib.last() == i:
            nm = "ITH" if isHigh else "ITL"
        for l in self.levels:
            if l.kind == "swing" and l.bsl == isHigh and pabs(l.price - price) <= self.iEqPips * self.PIP:
                l.name = "Equal Highs" if isHigh else "Equal Lows"
                nm = l.name
        self.levels.push(Level(nm, price, i, isHigh, "swing"))
        # failure swing: a lower high (higher low) after fib 1 of a live leg, whose -2/-2.5 overlaps the leg's -1/-1.5
        if self.iFS:
            fb = self.bearLegs if isHigh else self.bullLegs
            for lg in fb:
                if (not lg.done and not lg.fs and not lg.hasFs and i > lg.oneBar and (price < lg.one if isHigh else price > lg.one)
                        and (self.iFsBig <= 0 or na(self.atr14) or abs(lg.one - lg.zero) >= self.iFsBig * self.atr14)):
                    zb = self.f_lastBarBefore(self.slB if isHigh else self.shB, i)
                    z = self.f_lastBefore(self.slB if isHigh else self.shB, self.slP if isHigh else self.shP, i)
                    if zb > lg.oneBar and not na(z) and (z < price if isHigh else z > price) and abs(price - z) >= self.iMinLeg * self.PIP:
                        u = abs(price - z)
                        a2 = z - self.iZ2a * u if isHigh else z + self.iZ2a * u
                        b2 = z - self.iZ2b * u if isHigh else z + self.iZ2b * u
                        a1 = self.f_lvl(lg, self.iZ1a)
                        b1 = self.f_lvl(lg, self.iZ1b)
                        if pmax(pmin(a2, b2), pmin(a1, b1)) <= pmin(pmax(a2, b2), pmax(a1, b1)):
                            lg.hasFs = True
                            self.fsq.push(Hunt(isHigh, price, z, i, NA, lg.names, False, lg.oneBar, zb))
        # liquidity this swing took (sweeps of the last 3 bars on its side)
        names = ""
        ext = False
        key = NA
        for sw in self.sweeps:
            important = (sw.kind != "swing" or sw.name == "Equal Highs" or sw.name == "Equal Lows" or sw.name == "ITH"
                         or sw.name == "ITL" or sw.name == "Hunt High" or sw.name == "Hunt Low")
            if sw.bsl == isHigh and sw.bar >= i - 3 and sw.bar <= i and important:
                if not (("," + sw.name + ",") in ("," + names + ",")):
                    names = sw.name if names == "" else names + "," + sw.name
                ext = ext or sw.kind != "swing"
                key = sw.price if na(key) else (pmax(key, sw.price) if isHigh else pmin(key, sw.price))
        # dealing range: this swing took the waiting buy-side (sell-side) grab if it is the highest high (lowest low) since it
        dr = self.dr
        pB = dr.pHiBar if isHigh else dr.pLoBar
        if pB >= 0 and pB <= i:
            turn = i - pB <= 300
            if turn:
                for b in prange(pB, i):
                    if (self.h_(self.bar_index - b) > price) if isHigh else (self.l_(self.bar_index - b) < price):
                        turn = False
                        break
            if i - pB > 300 or turn:
                why = dr.pHiWhy if isHigh else dr.pLoWhy
                # external range: a turn that is not the range's own extreme (where price took the edge) is internal liquidity
                inner = turn and self.iDrExt and self.f_drReady() and i != (dr.hiB if isHigh else dr.loB)
                if isHigh:
                    if inner:
                        if na(dr.cHi) or price > dr.cHi:
                            dr.cHi = price
                            dr.cHiB = i
                            dr.cHiWhy = why
                    elif turn:
                        if na(dr.hi) or ne(price, dr.hi) or i != dr.hiB:
                            dr.isNew = True
                        if self.iDrExt and not na(dr.cLo) and not na(dr.lo) and dr.cLoB <= i:
                            m = dr.cLo  # the pullback low before the run: lowest low since the inside sell-side grab
                            mB = dr.cLoB
                            for b in prange(max(dr.cLoB, i - 1500), i):
                                if self.l_(self.bar_index - b) < m:
                                    m = self.l_(self.bar_index - b)
                                    mB = b
                            if m < (dr.lo + price) / 2:  # it reached discount: the new leg starts there
                                dr.lo = m
                                dr.loB = mB
                                dr.loWhy = dr.cLoWhy
                                dr.isNew = True
                        dr.hi = price
                        dr.hiB = i
                        dr.hiWhy = why
                        dr.cHi = NA
                        dr.cLo = NA
                    dr.pHiBar = -1
                    dr.pHiWhy = ""
                else:
                    if inner:
                        if na(dr.cLo) or price < dr.cLo:
                            dr.cLo = price
                            dr.cLoB = i
                            dr.cLoWhy = why
                    elif turn:
                        if na(dr.lo) or ne(price, dr.lo) or i != dr.loB:
                            dr.isNew = True
                        if self.iDrExt and not na(dr.cHi) and not na(dr.hi) and dr.cHiB <= i:
                            m = dr.cHi  # the pullback high before the run: highest high since the inside buy-side grab
                            mB = dr.cHiB
                            for b in prange(max(dr.cHiB, i - 1500), i):
                                if self.h_(self.bar_index - b) > m:
                                    m = self.h_(self.bar_index - b)
                                    mB = b
                            if m > (price + dr.hi) / 2:  # it reached premium: the new leg starts there
                                dr.hi = m
                                dr.hiB = mB
                                dr.hiWhy = dr.cHiWhy
                                dr.isNew = True
                        dr.lo = price
                        dr.loB = i
                        dr.loWhy = why
                        dr.cHi = NA
                        dr.cLo = NA
                    dr.pLoBar = -1
                    dr.pLoWhy = ""
        if names != "":
            zero, zeroB = self.f_huntOrigin(self.slB if isHigh else self.shB, self.slP if isHigh else self.shP, i, isHigh)
            own = self.levels.last()
            if own.bar == i:
                own.name = "Hunt High" if isHigh else "Hunt Low"
            if ext:
                (self.hsHB if isHigh else self.hsLB).push(i)
                (self.hsHP if isHigh else self.hsLP).push(price)
            if not na(zero) and (zero < price if isHigh else zero > price) and abs(price - zero) >= self.iMinLeg * self.PIP:
                imp = ext or ("Hunt" in names) or (self.iChainIth and (("ITH" in names) or ("ITL" in names)))
                self.hunts.push(Hunt(isHigh, price, zero, i, key, names, imp, -1, zeroB))
        return names

    # ---- L1030-1038: confirmed pivots, then swing levels older than the lookback go ----
    def top_1030(self):
        if not na(self.ph):
            self.f_onSwing(self.bar_index - self.iPivot, self.ph, True)
        if not na(self.pl):
            self.f_onSwing(self.bar_index - self.iPivot, self.pl, False)
        levels = self.levels
        if levels.size() > 0:
            for i in prange(levels.size() - 1, 0):
                l = levels.get(i)
                if l.kind == "swing" and self.bar_index - l.bar > self.iSwingLB:
                    levels.remove(i)

    # ---- L1040-1047: day separator lines (drawing only; dayLines dropped). The flags are kept as globals, nothing reads them ----
    def top_1041(self):
        prevT = self.t_(1)
        self.newNyDay = (not na(prevT)) and dayofmonth(self.time) != dayofmonth(prevT)
        self.dChange = self.change_D
        self.dayStart = self.bar_index > 0 and (self.newNyDay if self.iDayLine == "NY midnight" else self.change_D if self.iDayLine == "Daily candle (17:00 NY)" else False)

    # ---- L1050: MSS line + label (drawing only; mssLines / mssLabels dropped). Pine returns mssLines.size(), unused ----
    def f_drawMss(self, fromBar, lvl, txt):
        return 0

    # ---- L1065 ----
    def f_fibEnd(self, lg):
        if self.iFibTv:
            return pmax(pmax(lg.zeroBar, lg.oneBar), pmin(lg.zeroBar if lg.zeroBar >= 0 else lg.oneBar, lg.oneBar) + 2)
        return pmin(self.bar_index + 3, lg.oneBar + self.iFibLen) if self.iFibLen > 0 else self.bar_index + 3

    def _sec2_legArrs(self, lg):
        # Pine creates every Leg with lns / lbs / bxs = array.new (L1266 / L1326); make sure they exist here
        if lg.lns is None:
            lg.lns = PArr()
        if lg.lbs is None:
            lg.lbs = PArr()
        if lg.bxs is None:
            lg.bxs = PArr()

    # ---- L1067: the drawings are not simulated; only the sizes of lg.lns / lbs / bxs are kept like Pine
    # (f_upkeep and f_signalCont test lg.lns.size()), with placeholder items ----
    def f_drawLeg(self, lg):
        self._sec2_legArrs(lg)
        if self.iShowLegs and self.DRAW:
            if self.iFibTv and lg.zeroBar >= 0:
                lg.lns.push(0)
            for k in (1.0, 0.786, 0.705, 0.618, 0.5, 0.0, -1.0, -1.5, -2.0, -2.5, -3.5, -4.0):
                if self.iFibTv:
                    lg.lns.push(0)
                elif k <= 0.0 or k >= 1.0:
                    lg.lns.push(0)
                lg.lbs.push(0)
            if self.iShowBoxes:
                lg.bxs.push(0)
            if self.iShowBoxes:
                lg.bxs.push(0)
            if self.iShowBoxes:
                lg.bxs.push(0)
        return lg.lns.size()

    # ---- L1091: only moves drawings ----
    def f_extendLeg(self, lg):
        x2 = self.f_fibEnd(lg)
        return x2

    # ---- L1103: line/label/box.delete do not empty the arrays in Pine; only the flag changes ----
    def f_deleteLeg(self, lg):
        lg.cleaned = True
        return lg.cleaned

    # ---- L1113-1116: reversal-zone memory of the accepted hunt legs (pushed in the hunts block, L1285-1293) ----
    def init_1113(self):
        self.zrBear = PArr()
        self.zrOne = PArr()
        self.zrZero = PArr()
        self.zrBar = PArr()

    # ---- L1117 ----
    def f_zoneHit(self, k, newBear, one, oneBar):
        ok = False
        ob = self.zrBar.get(k)
        if self.zrBear.get(k) != newBear and ob < oneBar and oneBar - ob <= self.iLegAge:
            zb = self.zrBear.get(k)
            o1 = self.zrOne.get(k)
            o0 = self.zrZero.get(k)
            u = abs(o1 - o0)
            worst = o0
            broken = False
            for b in prange(ob + 1, oneBar):
                cb = self.c_(self.bar_index - b)
                if (cb > o1) if zb else (cb < o1):
                    broken = True
                worst = pmin(worst, cb) if zb else pmax(worst, cb)
            if not broken:
                z2a = o0 - self.iZ2a * u if zb else o0 + self.iZ2a * u
                z2b = o0 - self.iZ2b * u if zb else o0 + self.iZ2b * u
                z3a = o0 - self.iZ3a * u if zb else o0 + self.iZ3a * u
                z3b = o0 - self.iZ3b * u if zb else o0 + self.iZ3b * u
                if zb:
                    ok = (one <= z2a and worst >= z2b) or (one <= z3a and worst >= z3b)
                else:
                    ok = (one >= z2a and worst <= z2b) or (one >= z3a and worst <= z3b)
        return ok

    # ---- L1143 ----
    def f_inPriorZone(self, newBear, one, oneBar):
        ok = False
        n = self.zrBar.size()
        if n > 0:
            for k in prange(n - 1, 0):
                if not ok and self.f_zoneHit(k, newBear, one, oneBar):
                    ok = True
        return ok

    # ---- L1152-1174: other side of a hunt setup's dealing range: the opposite stop hunt whose -2..-2.5 / -3.5..-4 this
    # hunt reached, else the last opposite stop hunt beyond it; computed once per leg ----
    def f_oppHunt(self, lg):
        if not lg.oppDone:
            lg.oppDone = True
            px = NA
            pb = -1
            n = self.zrBar.size()
            if n > 0:
                for k in prange(n - 1, 0):
                    ob = self.zrBar.get(k)
                    o1 = self.zrOne.get(k)
                    if na(lg.oppPx) and self.zrBear.get(k) != lg.bear and ob < lg.oneBar and lg.oneBar - ob <= self.iLegAge and (o1 < lg.one if lg.bear else o1 > lg.one):
                        if pb < 0:
                            px = o1
                            pb = ob
                        if self.f_zoneHit(k, lg.bear, lg.one, lg.oneBar):
                            lg.oppPx = o1
                            lg.oppBar = ob
            if na(lg.oppPx):
                lg.oppPx = px
                lg.oppBar = pb
        return lg.oppBar

    # ---- L1176-1204: SDP zones of the leg zero -> one, nearest first: the first one fully in premium (buy) / discount
    # (sell) of the dealing range is the target at its first level (-1 / -2 / -3.5); a zone across the 50% makes the 50%
    # the target ----
    def f_drTarget(self, buy, zero, one, drEq, entry):
        t = NA
        why = ""
        tag = ""
        side = "premium" if buy else "discount"
        for z in prange(0, 2):
            if na(t):
                a = self.iZ1a if z == 0 else self.iZ2a if z == 1 else self.iZ3a
                b = self.iZ1b if z == 0 else self.iZ2b if z == 1 else self.iZ3b
                pa = zero - a * (one - zero)
                pb = zero - b * (one - zero)
                zLo = pmin(pa, pb)
                zHi = pmax(pa, pb)
                zt = "-" + tstr(a) + "/-" + tstr(b)
                if ((zLo >= drEq) if buy else (zHi <= drEq)) and ((pa > entry) if buy else (pa < entry)):
                    t = pa
                    why = "-" + tstr(a) + ": zone " + zt + " in " + side
                    tag = "-" + tstr(a)
                elif zLo < drEq and zHi > drEq and ((drEq > entry) if buy else (drEq < entry)):
                    t = drEq
                    why = "50% of the dealing range: zone " + zt + " across it"
                    tag = "50%"
        if na(t):
            t = drEq
            why = "50% of the dealing range: no SDP zone in " + side
            tag = "50%"
        return [t, why, tag]

    # ---- L1206-1241: main target with the TP buffer and the R cap; legacy = target of the other modes; edge = BSL (buy) /
    # SSL (sell) of the dealing range ----
    def f_mainTarget(self, buy, entry, risk, zero, one, drEq, edge, legacy, legacyWhy):
        cap = entry + self.iMaxRR * risk if buy else entry - self.iMaxRR * risk
        t = NA
        why = ""
        tag = ""
        capTxt = tstr(self.iMaxRR) + "R cap"
        if self.iTgtMode == self.TGT_DR and not na(drEq):
            t0, w0, g0 = self.f_drTarget(buy, zero, one, drEq, entry)
            t1 = t0
            lvl = w0  # short name of the level for the cap texts
            tag = g0
            why = " (" + w0 + ")"
            if self.iTgtLiq and not na(edge) and ((t0 > edge) if buy else (t0 < edge)):  # the SDP level is past the opposite liquidity: that BSL / SSL is the target
                t1 = edge
                lvl = ("BSL" if buy else "SSL") + " of the dealing range"
                tag = "BSL" if buy else "SSL"
                why = " (" + lvl + "; " + w0 + " at " + self.f_num(t0) + " is past it)"
            t = t1
            if (t1 > cap) if buy else (t1 < cap):
                t = pmax(cap, drEq) if buy else pmin(cap, drEq)
                if t == cap:
                    why = " (" + capTxt + "; " + lvl + " at " + self.f_num(t1) + ")"
                    tag = capTxt
                elif ne(t1, drEq):
                    why = " (50% of the dealing range: " + lvl + " at " + self.f_num(t1) + " is past the " + capTxt + ")"
                    tag = "50%"
            t = t - self.iTpBuf * self.PIP if buy else t + self.iTpBuf * self.PIP
        else:
            lTag = "fib 1" if legacyWhy.startswith("fib 1") else legacyWhy
            t = legacy - self.iTpBuf * self.PIP if buy else legacy + self.iTpBuf * self.PIP
            capped = (t > cap) if buy else (t < cap)
            why = (" (" + capTxt + "; " + legacyWhy + " at " + self.f_num(t) + ")") if capped else (" (" + legacyWhy + ")")
            tag = capTxt if capped else lTag
            t = pmin(t, cap) if buy else pmax(t, cap)
        return [t, why, tag]

    # ---- L1243: 50% of the biggest opposite move (prior opposite hunt leg) this leg retraces ----
    def f_revEq(self, legBear, one, oneBar):
        eq = NA
        big = 0.0
        n = self.zrBar.size()
        if n > 0:
            for k in prange(n - 1, 0):
                ob = self.zrBar.get(k)
                o1 = self.zrOne.get(k)
                if self.zrBear.get(k) != legBear and ob < oneBar and oneBar - ob <= self.iLegAge and (o1 < one if legBear else o1 > one) and abs(o1 - one) > big:
                    big = abs(o1 - one)
                    eq = (o1 + one) / 2
        return eq
