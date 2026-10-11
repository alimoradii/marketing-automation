"""Section 3 of the MZ_SDP.pine port: Pine lines 1254-1704.

hunts -> SDP legs (bearLegs / bullLegs), failure-swing queue fsq, live dealing range widening (its drawing dropped),
f_fadeBox / f_hideBox (drawing), daily bias / HTF texts, f_warn / f_htfRej / f_mssMkt / f_dFvgTxt, text helpers,
signal drawing helpers (only the state they keep), strategy hooks (no-ops), f_update (logs to self.trlog), f_close,
f_manage, the trade loop (fills, void, cancel, expiry, SL / TP / partial, news close) and the trade windows.
Line numbers (and the top_ / init_ names) are those of MZ_SDP.pine at commit 1beecc4, like the other sections; commit
bedea9e shifted this range to 1301-1751 without changing its content.
"""
from base import *


class Sec3:
    # ---- L1256-1330: a hunt whose close is back past its level becomes an SDP leg; failure swings join their main leg ----
    def top_1256(self):
        if self.hunts.size() > 0:
            still = PArr()
            for hu in self.hunts:
                back = (self.close < hu.level) if hu.bear else (self.close > hu.level)
                if back:
                    book = self.bearLegs if hu.bear else self.bullLegs
                    dup = False
                    for x in book:
                        if x.oneBar == hu.bar:
                            dup = True
                    lg = Leg(hu.bear, hu.one, hu.zero, hu.bar, self.bar_index, hu.names, drOne=hu.one, zeroBar=hu.zeroBar,
                             z5=Ltf(), c5=Ltf(), lns=PArr(), lbs=PArr(), bxs=PArr())
                    took = False
                    if not dup:
                        lg.inZone = self.f_inPriorZone(hu.bear, hu.one, hu.bar)
                        if self.iSupersede:
                            for x in book:
                                if (not x.done and not x.fs and x.zone == "" and not x.signaled and x.oneBar < hu.bar
                                        and (((hu.one > x.one) if hu.bear else (hu.one < x.one)) or pabs(hu.zero - x.zero) <= self.iEqPips * self.PIP)):
                                    took = True
                                    lg.inZone = lg.inZone or x.inZone
                    if not dup and self.iChain and not lg.inZone and not hu.external and not took:
                        dup = True
                    if not dup and took:
                        for x in book:
                            if (not x.done and not x.fs and x.zone == "" and not x.signaled and x.oneBar < hu.bar
                                    and (((hu.one > x.one) if hu.bear else (hu.one < x.one)) or pabs(hu.zero - x.zero) <= self.iEqPips * self.PIP)):
                                x.done = True
                                x.endWhy = "replaced by the last stop hunt"
                    if not dup:
                        if self.useHZ and not lg.inZone:
                            lg.cDone = True
                        self.zrBear.push(hu.bear)
                        self.zrOne.push(hu.one)
                        self.zrZero.push(hu.zero)
                        self.zrBar.push(hu.bar)
                        if self.zrBar.size() > 60:
                            self.zrBear.shift()
                            self.zrOne.shift()
                            self.zrZero.shift()
                            self.zrBar.shift()
                        if not self.iClean:
                            self.f_drawLeg(lg)
                        book.push(lg)
                        live = 0
                        for x in book:
                            if not x.done and not x.fs:
                                live += 1
                        while live > self.iMaxLegs:
                            ks = -1
                            us = NA
                            for k in prange(0, book.size() - 2):  # the newest leg (last) is never the one replaced
                                x = book.get(k)
                                if not x.done and not x.fs and (na(us) or pabs(x.one - x.zero) < us):
                                    us = pabs(x.one - x.zero)
                                    ks = k
                            if ks < 0:
                                break
                            sm = book.get(ks)
                            sm.done = True
                            sm.endWhy = "replaced by bigger legs"
                            live -= 1
                elif self.bar_index - hu.bar <= 3:
                    still.push(hu)
            self.hunts = still
        if self.fsq.size() > 0:
            for hu in self.fsq:
                book = self.bearLegs if hu.bear else self.bullLegs
                pOne = NA
                for x in book:
                    if x.oneBar == hu.parent and not x.fs and not x.done:
                        pOne = x.one
                if not na(pOne):
                    lg = Leg(hu.bear, hu.one, hu.zero, hu.bar, self.bar_index, hu.names, cDone=True, fs=True, parentBar=hu.parent,
                             drOne=pOne, zeroBar=hu.zeroBar, z5=Ltf(), c5=Ltf(), lns=PArr(), lbs=PArr(), bxs=PArr())
                    if not self.iClean:
                        self.f_drawLeg(lg)
                    book.push(lg)
            self.fsq.clear()

    # ---- L1334-1339: live dealing range lines / labels / boxes (ldrT, ldrB, ldrE, ldrL, ldrP, ldrD) - drawing only, dropped ----

    # ---- L1340: drawing only ----
    def f_fadeBox(self, b, c):
        return b

    # ---- L1345: drawing only ----
    def f_hideBox(self, b):
        return b

    # ---- L1350-1413: price past the range takes the buy-side (sell-side) liquidity of its high (low): the range widens,
    # the turn gets it. The live dealing range drawing (L1362-1412) is dropped ----
    def top_1350(self):
        dr = self.dr
        if not na(dr.hi) and self.high > dr.hi:
            dr.pHiBar = self.bar_index if dr.pHiBar < 0 else dr.pHiBar
            dr.pHiWhy = self.f_addWhy(dr.pHiWhy, "range high")
            dr.hi = self.high
            dr.hiB = self.bar_index
            dr.hiWhy = "taking the range high"
        if not na(dr.lo) and self.low < dr.lo:
            dr.pLoBar = self.bar_index if dr.pLoBar < 0 else dr.pLoBar
            dr.pLoWhy = self.f_addWhy(dr.pLoWhy, "range low")
            dr.lo = self.low
            dr.loB = self.bar_index
            dr.loWhy = "taking the range low"
        # L1362-1412: if iShowLDR and DRAW and f_drReady() -> lines / label / boxes of the live range (drawing only)
        dr.isNew = False

    # ---- L1415 ----
    def f_dBiasTxt(self, buy):
        b = "Bullish" if self.dBias == 1 else "Bearish" if self.dBias == -1 else "Neutral"
        why = ("" if self.iBiasMode == "Simple"
               else (" - rejected " + ("bear" if self.dReact < 0 else "bull") + " D-FVG") if ne(self.dReact, 0)
               else (" - daily " + ("premium " if self.close > self.dDrEq else "discount ") + tstr(pround(100 * (self.close - self.dDrLo) / (self.dDrHi - self.dDrLo)))
                     + "% of " + self.f_num(self.dDrLo) + "-" + self.f_num(self.dDrHi)) if self.dDrOk
               else "")
        return b + why + ("" if self.dBias == 0 else (" (with the trade)" if (self.dBias == 1) == buy else " (against the trade)"))

    # ---- L1419 ----
    def f_drPos(self, hi, lo, px, buy):
        t = "—"
        ok = 0
        if not na(hi) and not na(lo) and hi > lo:
            eq = (hi + lo) / 2
            w = (px < eq) if buy else (px > eq)
            ok = 1 if w else -1
            t = ("discount " if px < eq else "premium ") + tstr(pround(100 * (px - lo) / (hi - lo))) + "% (" + ("with" if w else "against") + ")"
        return [t, ok]

    # ---- L1428 ----
    def f_warn(self, buy, px):
        t4, o4 = self.f_drPos(self.h4DrHi, self.h4DrLo, px, buy)
        bAg = ne(self.dBias, 0) and (self.dBias == 1) != buy
        rAg = o4 == -1
        tAg = self.iWarnTrend and ne(self.dTrend, 0) and (self.dTrend == 1) != buy
        w = (" + against daily trend" if tAg else "") + (" + against daily bias" if bAg else "") + (" + wrong side of 4h range" if rAg else "")
        return "" if w == "" else "⚠ " + w[3:] + " → reduce size"

    # ---- L1435 ----
    def f_htfTxt(self, buy, px):
        t4, o4 = self.f_drPos(self.h4DrHi, self.h4DrLo, px, buy)
        tD, oD = self.f_drPos(self.dDrHi, self.dDrLo, px, buy)
        return "4h: " + t4 + " · D: " + tD

    # ---- L1439 ----
    def f_htfRej(self, buy, px):
        t4, o4 = self.f_drPos(self.h4DrHi, self.h4DrLo, px, buy)
        tD, oD = self.f_drPos(self.dDrHi, self.dDrLo, px, buy)
        known = o4 != 0 or oD != 0
        pass_ = self.HTFF == "Off" or not known or ((o4 == 1 or oD == 1) if self.HTFF == "4h or daily" else (o4 != -1 and oD != -1))
        return "" if pass_ else "entry against the 4h and daily dealing ranges (" + self.f_htfTxt(buy, px) + ")"

    # ---- L1445: entry at market on the MSS bar (setting) ----
    def f_mssMkt(self, gapBull, eq):
        g = None
        if self.iMssMkt != "Off":
            ok = False
            if self.iMssMkt == "Setup range":
                ok = (self.close < eq) if gapBull else (self.close > eq)
            else:
                t4, o4 = self.f_drPos(self.h4DrHi, self.h4DrLo, self.close, gapBull)
                tD, oD = self.f_drPos(self.dDrHi, self.dDrLo, self.close, gapBull)
                ok = o4 == 1 or oD == 1
            if ok:
                g = Gap(self.bar_index, self.close, self.close, gapBull, nofvg=True, atMss=True)
        return g

    # ---- L1459 ----
    def f_dFvgTxt(self, buy):
        t = ""
        if not na(self.dBB) and self.close >= self.dBB and self.close <= self.dBT:
            t = "in bull D-FVG " + self.f_num(self.dBB) + "-" + self.f_num(self.dBT) + (" (with the trade)" if buy else " (against the trade)")
        elif not na(self.dSB) and self.close >= self.dSB and self.close <= self.dST:
            t = "in bear D-FVG " + self.f_num(self.dSB) + "-" + self.f_num(self.dST) + (" (against the trade)" if buy else " (with the trade)")
        elif buy:
            t = "bull D-FVG below: " + ("—" if na(self.dBB) else self.f_num(self.dBB) + "-" + self.f_num(self.dBT))
        else:
            t = "bear D-FVG above: " + ("—" if na(self.dSB) else self.f_num(self.dSB) + "-" + self.f_num(self.dST))
        return t

    # ---- L1471 ----
    def top_1471(self):
        self.ALJSON = self.iAlFmt == "JSON (webhook bot)"

    # ---- L1472-1489: alert texts (kept as functions; the alerts themselves are not simulated) ----
    def f_rTxt(self, r):
        return "" if na(r) else ("+" if r > 0 else "") + tstr(r, "0.00")

    def f_tm(self, t):
        d = datetime.fromtimestamp(t / 1000, tz=timezone.utc)
        return d.astimezone(ZoneInfo("Asia/Tehran")).strftime("%H:%M") + " Tehran / " + d.astimezone(NYZ).strftime("%H:%M") + " NY"

    def f_sigTxt(self, buy, grade, setupTxt, entry, market, stop, partial, main, rr, vb):
        until = self.time_close + vb * self.timeframe_in_seconds * 1000
        return (("🟢 BUY " if buy else "🔴 SELL ") + self.TK + " " + self.timeframe_period + "m · grade " + grade + " · " + setupTxt
                + "\nEntry " + ("MARKET ~" if market else "LIMIT ") + self.f_num(entry) + " · SL " + self.f_num(stop) + " · TP " + self.f_num(main)
                + ("" if na(partial) else " (partial " + self.f_num(partial) + ")") + " · R:R 1:" + tstr(rr, "0.0")
                + ("" if market else "\nValid until " + self.f_tm(until) + ". Cancel the order if TP " + self.f_num(main if na(partial) else partial) + " is reached before the entry.")
                + "\nSignal at " + self.f_tm(self.time_close))

    def f_evTxt(self, tr, ev, px, r):
        s = ("SELL " if tr.sell else "BUY ") + self.TK + " (signal " + tr.id + ")"
        if ev == "filled":
            if self.iOnRetrace:
                return (("🔴 SELL " if tr.sell else "🟢 BUY ") + self.TK + " " + self.timeframe_period + "m NOW at " + self.f_num(px) + " (price is back in the FVG)\nSL "
                        + self.f_num(tr.stop) + " · TP " + self.f_num(tr.tpMain) + ("" if na(tr.tp1) else " (partial " + self.f_num(tr.tp1) + ")")
                        + ("" if tr.warn == "" else "\n" + tr.warn) + "\nSignal " + tr.id)
            return "✅ " + s + " FILLED at " + self.f_num(px)
        if ev == "cancel":
            return "❌ " + s + " CANCELLED: target reached before the entry - delete the limit order, do not enter"
        if ev == "void":
            return "❌ " + s + " NOT ENTERED: price opened at " + self.f_num(px) + ", beyond the stop - skip this signal"
        if ev == "expired":
            return "⌛ " + s + " EXPIRED: not filled in time - delete the limit order"
        if ev == "tp1":
            return "💰 " + s + " PARTIAL hit at " + self.f_num(px) + " - close " + tstr(self.iPartFrac * 100, "0") + "%, keep the stop"
        if ev == "tp":
            return "🎯 " + s + " TARGET hit " + self.f_num(px) + " · " + self.f_rTxt(r) + "R"
        if ev == "sl":
            return "🛑 " + s + " STOP hit " + self.f_num(px) + " · " + self.f_rTxt(r) + "R"
        if ev == "close":
            return "📰 " + s + " CLOSED before red news at " + self.f_num(px) + " · " + self.f_rTxt(r) + "R"
        return s + " " + ev

    # ---- L1490-1491: entry-leg SDP drawings of the newest signal (drawing only; kept empty) ----
    def init_1490(self):
        self.sigSdpL = PArr()
        self.sigSdpT = PArr()

    # ---- L1492: drawing only ----
    def f_clearSigSdp(self):
        self.sigSdpL.clear()
        self.sigSdpT.clear()
        return self.sigSdpL.size()

    # ---- L1500: drawing only; returns ks.size() like the Pine ----
    def f_sigSdp(self, one, zero, b1, b0, full, col, tag):
        if self.iClean:
            self.f_clearSigSdp()
        return 10 if full else 5

    # ---- L1517: entry / SL / TP lines + labels; only the array sizes are kept (placeholders), nothing trades on them ----
    def f_tradeLines(self, tr, full, tpWhy):
        tr.lns = PArr()
        tr.lls = PArr()
        tr.lns.push(0)
        tr.lns.push(0)
        tr.lns.push(0)
        if full and not na(tr.tp1):
            tr.lns.push(0)
        if full or self.iOldLbl:
            tr.lls.push(0)
            tr.lls.push(0)
            tr.lls.push(0)
        if full:
            if not na(tr.tp1):
                tr.lls.push(0)
        return tr.lns.size()

    # ---- L1536: dealing-range boxes of a signal (drawing only; placeholders keep the size) ----
    def f_drawDR(self, tr, hi, hiB, lo, loB, buy):
        tr.bxs = PArr()
        if self.iShowDR and self.DRAW and not na(hi) and not na(lo) and hi > lo:
            tr.bxs.push(0)
            tr.bxs.push(0)
        return tr.bxs.size()

    # ---- L1544: drawing only ----
    def f_extendLines(self, tr):
        return tr.state

    # ---- L1555: drawing only ----
    def f_endLines(self, tr, ev):
        return tr.state

    # ---- L1580: drawing only (signal label text / colour) ----
    def f_markBox(self, tr, ev, r):
        return tr.state

    # ---- L1609-1612: STRATEGY HOOKS - no-ops in the indicator ----
    def f_stratOpen(self, tr, grade):
        return tr.state

    def f_stratEvent(self, tr, ev):
        return ev

    # ---- L1614: alerts are not simulated; every event is logged for the backtest ----
    def f_update(self, tr, ev, px, r):
        self.f_stratEvent(tr, ev)
        self.f_markBox(tr, ev, r)
        self.f_endLines(tr, ev)
        # L1618-1623: quiet / alert(f_evTxt(...)) / JSON alert - dropped
        self.trlog.append(dict(id=tr.id, ev=ev, bar=self.bar_index, time=self.time, px=px, r=r))
        return ev

    # ---- L1626 ----
    def f_close(self, tr, ev, px):
        tr.realized += tr.remaining * ((tr.entry - px) if tr.sell else (px - tr.entry))
        tr.remaining = 0.0
        tr.state = 2
        # tr.risk > 0 always here (a fill needs risk > 0); guard only against a Python ZeroDivisionError
        r = tr.realized / tr.risk if tr.risk else NA
        self.st.closed += 1
        self.st.totalR += r
        if r > 0.05:
            self.st.wins += 1
        elif r < -0.05:
            self.st.losses += 1
        return self.f_update(tr, ev, px, r)

    # ---- L1639 ----
    def f_manage(self, tr, fillBar):
        if not fillBar and self.iNewsClose and self.f_newsAt(self.time) != "":
            self.f_close(tr, "close", self.open)
        if tr.state == 1:
            if (self.high >= tr.stop) if tr.sell else (self.low <= tr.stop):
                self.f_close(tr, "sl", tr.stop)
        if tr.state == 1 and not fillBar:
            if not tr.partialDone and not na(tr.tp1) and ((self.low <= tr.tp1) if tr.sell else (self.high >= tr.tp1)):
                tr.realized += self.iPartFrac * ((tr.entry - tr.tp1) if tr.sell else (tr.tp1 - tr.entry))
                tr.remaining -= self.iPartFrac
                tr.partialDone = True
                if tr.remaining <= 0.000001:  # partial size 1: the whole position closes here
                    self.f_close(tr, "tp", tr.tp1)
                else:
                    self.f_update(tr, "tp1", tr.tp1, NA)
            if tr.state == 1 and ((self.low <= tr.tpMain) if tr.sell else (self.high >= tr.tpMain)):
                self.f_close(tr, "tp", tr.tpMain)
        return tr.state

    # ---- L1658-1691: pending orders (expiry / fill / void / cancel) and open trades ----
    def top_1658(self):
        trades = self.trades
        if trades.size() > 0:
            for i in prange(trades.size() - 1, 0):
                tr = trades.get(i)
                self.f_extendLines(tr)
                if tr.state == 0:
                    firstTp = tr.tpMain if na(tr.tp1) else tr.tp1
                    if self.bar_index > tr.validUntil:
                        tr.state = 2
                        self.f_update(tr, "expired", NA, NA)
                    elif tr.market or ((self.high >= tr.entry) if tr.sell else (self.low <= tr.entry)):
                        if tr.market:
                            tr.entry = self.open
                        tr.risk = pabs(tr.entry - tr.stop)
                        if (tr.entry >= tr.stop) if tr.sell else (tr.entry <= tr.stop):  # market fill would open at / beyond the stop
                            tr.state = 2
                            self.f_update(tr, "void", tr.entry, NA)
                        elif tr.risk <= 0:
                            tr.state = 2  # no f_update in the Pine
                        else:
                            tr.state = 1
                            self.f_update(tr, "filled", tr.entry, NA)
                            # L1679-1681: BUY / SELL fill label - drawing only
                            self.f_manage(tr, True)
                    elif (self.low <= firstTp) if tr.sell else (self.high >= firstTp):
                        tr.state = 2
                        self.f_update(tr, "cancel", NA, NA)
                elif tr.state == 1:
                    self.f_manage(tr, False)
                if tr.state == 2:
                    if tr.legBar == self.st.liveLeg:
                        self.st.liveLeg = -1
                    trades.remove(i)

    # ---- L1693-1703: trade windows (L1704 bgcolor dropped) ----
    def top_1693(self):
        self.w1s = self.f_sStart(self.sW1)
        self.w1e = self.f_sEnd(self.sW1)
        self.w2s = self.f_sStart(self.sW2)
        self.w2e = self.f_sEnd(self.sW2)
        self.w3s = self.f_sStart(self.sW3)
        self.w3e = self.f_sEnd(self.sW3)
        self.w4s = self.f_sStart(self.sW4)
        self.w4e = self.f_sEnd(self.sW4)
        m = self.mod
        self.winReal = ("london" if (self.iW1 and self.f_in(m, self.w1s, self.w1e))
                        else "ny_am" if (self.iW2 and self.f_in(m, self.w2s, self.w2e))
                        else "silver_bullet_am" if (self.iW3 and self.f_in(m, self.w3s, self.w3e))
                        else "silver_bullet_pm" if (self.iW4 and self.f_in(m, self.w4s, self.w4e))
                        else "")
        self.inSB = (self.f_in(m, self.f_sStart(self.sSB1), self.f_sEnd(self.sSB1)) or self.f_in(m, self.f_sStart(self.sSB2), self.f_sEnd(self.sSB2))
                     or self.f_in(m, self.f_sStart(self.sSB3), self.f_sEnd(self.sSB3)))
        self.winNow = self.winReal if self.winReal != "" else ("" if self.iUseWin else "any_time")
