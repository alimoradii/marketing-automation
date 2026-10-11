"""Section 5 of the MZ_SDP.pine port: Pine lines 2229-2784.

the hunt-leg step f_stepCont, the silver-bullet step
f_stepSb, f_stepBook, leg upkeep (f_hasTrade, f_showSig, f_freezeLeg, f_hide, f_primary, f_upkeep; drawings dropped, the
lns / lbs / bxs sizes kept like sec2 because the Clean-view logic tests them), the per-bar loops over both sides and the
Clean-view history pruning. The dashboard (L2734-2783: table, f_row, f_contTxt, f_bookTxt) is display only and dropped
(its f_newsAt / f_drReady calls have no side effects).
Line numbers (and the init_ / top_ names) are the pre-bedea9e ones, like sec1-sec4; in the current Pine file this range
is L2276-2831 (+47), unchanged in content.
"""
from base import *


def _utc_stamp5(t):
    """str.format_time(t, "yyyyMMddHHmm", "UTC")"""
    return datetime.fromtimestamp(t / 1000, tz=timezone.utc).strftime("%Y%m%d%H%M")


def _nsz(a):
    """size of a leg drawing array (Pine creates every leg with lns / lbs / bxs = array.new; None only if not)"""
    return 0 if a is None else a.size()


class Sec5:
    # ---- L2371: hunt-leg setup: fib 1 hunted, MSS of the ITH/ITL (or fib 0) with displacement, FVG in discount / premium ----
    def f_stepCont(self, lg):
        out = False
        bi = self.bar_index
        H = self.H
        L = self.L
        O = self.O
        C = self.C
        ATR = self.ATR
        buy = not lg.bear
        go = self.iHunt and not lg.cDone
        if go and ((self.close < lg.one) if buy else (self.close > lg.one)):
            lg.cDone = True
            go = False
        if go:
            lg.cFar = ((self.high if buy else self.low) if na(lg.cFar)
                       else (pmax(lg.cFar, self.high) if buy else pmin(lg.cFar, self.low)))
            if (lg.cFar >= self.f_fib(lg, -self.iPart)) if buy else (lg.cFar <= self.f_fib(lg, -self.iPart)):
                lg.cDone = True
                go = False
        if go:
            if not lg.cMss:
                if na(lg.cLevel):
                    pI = NA
                    pb = self.ithB if buy else self.itlB
                    pp = self.ithP if buy else self.itlP
                    nI = pb.size()
                    if nI > 0:
                        for k in prange(nI - 1, max(0, nI - 60)):
                            b = pb.get(k)
                            pk = pp.get(k)
                            # no break: lg.cLvlBar moves with each match (b > lg.cLvlBar), like the Pine
                            if b < lg.oneBar and b >= lg.oneBar - self.iIthLB and b > lg.cLvlBar and ((pk >= lg.zero) if buy else (pk <= lg.zero)):
                                pI = pk
                                lg.cLvlBar = b
                    lg.cLevel = lg.zero if na(pI) else pI
                    if na(pI):
                        lg.cLvlBar = lg.zeroBar
                if (self.high > lg.cLevel) if buy else (self.low < lg.cLevel):
                    if not lg.cMssDrawn:
                        lg.cMssDrawn = True
                        self.f_drawMss(lg.cLvlBar, lg.cLevel, "MSS")
                    ob = bi - lg.oneBar
                    disp = not self.iDisp or self.f_disp(buy, ob, ob - (0 if self.iDispHunt else 1))
                    if disp:
                        lg.cMss = True
                        lg.cMssBar = bi
                    else:
                        self.f_note(lg, buy, "MSS without displacement (candle >= " + tstr(self.iDispAtr) + " ATR) - no signal yet")
                # the chart never broke the level: the lower timeframe - break of the LTF swing before the hunt extreme (the hunt is the stop hunt)
                if not lg.cMss and not lg.cMssDrawn and self.LTF_MSS:
                    if self.f_track5(lg.c5, buy, lg.oneBar, False, lg.oneBar):
                        if not self.iDisp or self.f_disp5(buy, lg.c5.xi):
                            lg.cMss = True
                            lg.cMssBar = bi
                            lg.c5.mss = True
                            self.f_drawMss(lg.c5.zeroBar, lg.c5.zero, "MSS " + self.iLtfTf + "m")
                        else:
                            self.f_note(lg, buy, "MSS " + self.iLtfTf + "m without displacement (candle >= " + tstr(self.iDispAtr) + " ATR) - no signal yet")
                go = lg.cMss
        if go:
            # MSS from the lower timeframe: its extreme is the hunt (a wick past fib 1 that did not close there counts)
            ltf = lg.c5.mss
            hl = ((pmin(lg.one, lg.c5.xp) if buy else pmax(lg.one, lg.c5.xp)) if (ltf and not na(lg.c5.xp)) else lg.one)
            hlB = max(lg.oneBar, self.f_bar5(lg.c5.xi, lg.oneBar)) if ltf else lg.oneBar
            oxc = bi - lg.oneBar
            farC = self.high if buy else self.low
            farCBar = bi
            for k in prange(0, oxc):
                j = bi - k
                if (H[j] >= farC) if buy else (L[j] <= farC):
                    farC = H[j] if buy else L[j]
                    farCBar = bi - k
            # displacement leg: from the hunt (15m) or from the LTF extreme, which can be a later wick past fib 1
            farD = farC
            farDBar = farCBar
            if ltf:
                f5, f5B = self.f_farFrom5(lg.c5, buy, hlB)
                farD = f5
                farDBar = f5B
            eq = (hl + (farD if ltf else lg.cFar)) / 2
            dispEndC = farDBar if self.iFvgDisp else bi
            # dealing range: SSL = the hunt (buy), BSL = the last opposite stop hunt beyond it, else fib 0; wider if price went past it
            base = self.f_oppHunt(lg)
            farOut = (farC > base) if buy else (farC < base)
            drHi = self.dr.hi if self.drOn else (farC if farOut else base) if buy else hl
            drLo = self.dr.lo if self.drOn else hl if buy else (farC if farOut else base)
            drEq = (drHi + drLo) / 2
            eqD = (pmin(eq, drEq) if buy else pmax(eq, drEq)) if self.useDR else eq
            best = self.f_mssMkt(buy, eqD) if lg.cMssBar == bi else None
            if best is None:
                best = self.f_bestGap(buy, hlB + (1 if self.iDispHunt else 2), min(bi - 1, dispEndC), False, eq, drEq)
            if best is None:
                best = self.f_best5(buy, hlB if ltf else lg.oneBar + 1, eq, False, dispEndC, lg.c5.xt if ltf else 0, drEq)
            if best is None:
                best = self.f_noFvg(buy, farDBar, lg.c5.zero if ltf else lg.cLevel, eqD)
            if best is None:
                self.f_note(lg, buy, "MSS" + ((" " + self.iLtfTf + "m") if ltf else "") + " ✓ · FVG in " + ("discount" if buy else "premium") + " ✕ (waiting)")
            elif self.winNow == "":
                self.f_note(lg, buy, "MSS ✓ · FVG ✓ · killzone / silver bullet ✕")
            if best is None or self.winNow == "":
                go = False
            if go and self.MOF and (self.STRICT or self.iMOHard) and not na(self.midOpen):
                ent = self.f_gapEntry(best, buy)
                if ((self.close <= ent) if buy else (self.close >= ent)) or (self.iMktEntry and not self.iOnRetrace):
                    ent = self.close
                if (ent >= self.midOpen) if buy else (ent <= self.midOpen):
                    go = False
                    self.f_note(lg, buy, "MSS ✓ · FVG ✓ · entry " + ("below" if buy else "above") + " NY Open ✕ (waiting)")
            if go:
                for x in (self.bearLegs if buy else self.bullLegs):  # a hunt at a reversal zone (lg.inZone) is not "against"
                    if (self.AGL >= 0 and not lg.inZone and not x.done and x.oneBar < lg.oneBar
                            and ((lg.one < x.zero and lg.one > self.f_lvl(x, self.AGL if self.AGL > 0 else self.iZ2a)) if buy
                                 else (lg.one > x.zero and lg.one < self.f_lvl(x, self.AGL if self.AGL > 0 else self.iZ2a)))):
                        lg.cDone = True
                        go = False
                        self.st.rejected += 1
                        if self.iShowRej:
                            self.f_grayNote(buy, "hunt setup against the live " + ("bearish" if buy else "bullish") + " SDP (inside its 0..-2)")
                        break
            if go:
                lg.cDone = True
                self.f_useGap(best, buy)
                self.rqs.append((lg, best, self.winNow, hl if ltf else lg.one, NA, "continuation", drHi, drLo))
                out = True
        return out

    # ---- L2509: silver bullet at -1..-1.5 (with the move, target -2) ----
    def f_stepSb(self, lg):
        out = False
        bi = self.bar_index
        H = self.H
        L = self.L
        O = self.O
        C = self.C
        ATR = self.ATR
        buy = not lg.bear
        if self.iSbEntry and not lg.sbDone and not lg.done and not lg.fs and lg.zone == "":
            onePx = self.f_fib(lg, -self.iZ1a)
            twoPx = self.f_fib(lg, -self.iZ2a)
            farNow = self.high if buy else self.low
            back = self.low if buy else self.high
            if (farNow >= twoPx) if buy else (farNow <= twoPx):
                lg.sbDone = True
            elif lg.sbTouch < 0:
                if (farNow >= onePx) if buy else (farNow <= onePx):
                    lg.sbTouch = bi
            elif (back < lg.zero) if buy else (back > lg.zero):
                lg.sbDone = True
            elif na(lg.sbExt) or ((back < lg.sbExt) if buy else (back > lg.sbExt)):
                lg.sbExt = back
                lg.sbExtBar = bi
                lg.sbMss = False
            else:
                if not lg.sbMss:
                    pI, b0 = self.f_lastBefore(self.shB if buy else self.slB, self.shP if buy else self.slP, lg.sbExtBar)
                    bI = b0 if b0 >= lg.sbTouch - self.iIthLB else -1
                    if bI >= 0 and ((self.high > pI) if buy else (self.low < pI)):
                        ob = bi - lg.sbExtBar
                        disp = not self.iDisp or self.f_disp(buy, ob, ob - 1)
                        if disp:
                            lg.sbMss = True
                            lg.sbLvl = pI
                            self.f_drawMss(bI, pI, "MSS")
                if lg.sbMss and self.inSB:
                    ox = bi - lg.sbExtBar
                    far = self.high if buy else self.low
                    for k in prange(0, ox):
                        far = pmax(far, H[bi - k]) if buy else pmin(far, L[bi - k])
                    eq = (lg.sbExt + far) / 2
                    # dealing range: the pullback extreme to the top (buy) / bottom (sell) of the move since the hunt
                    rTop = self.high if buy else self.low
                    for k in prange(0, bi - lg.oneBar):
                        rTop = pmax(rTop, H[bi - k]) if buy else pmin(rTop, L[bi - k])
                    drHi = self.dr.hi if self.drOn else rTop if buy else lg.sbExt
                    drLo = self.dr.lo if self.drOn else lg.sbExt if buy else rTop
                    drEq = (drHi + drLo) / 2
                    best = self.f_bestGap(buy, lg.sbExtBar + 2, bi, True, eq, drEq)
                    if best is not None:
                        lg.sbDone = True
                        self.usedFvg.push(best.bar if buy else -best.bar)
                        if self.usedFvg.size() > 100:
                            self.usedFvg.shift()
                        self.rqs.append((lg, best, "silver_bullet" if self.winNow == "" else self.winNow, lg.sbExt, twoPx,
                                         "silver_bullet", drHi, drLo))
                        out = True
        return out

    # ---- L2599: one bar of every leg of a book: expiry / orphan FS, deeper hunt, hunt-leg + silver-bullet + zone steps ----
    def f_stepBook(self, book):
        fired = False
        firedC = False
        bi = self.bar_index
        n = book.size()
        if n > 0:
            for k in prange(0, n - 1):
                lg = book.get(k)
                if not lg.done and lg.createdBar != bi:
                    orphan = False
                    if lg.fs:
                        orphan = True
                        for x in book:
                            if x.oneBar == lg.parentBar and not x.fs and not x.done:
                                orphan = False
                    if bi - lg.oneBar > self.iLegAge or orphan:
                        lg.done = True
                        lg.endWhy = "main leg ended" if orphan else "zone not reached (expired)"
                    if not lg.mssOk and ((self.low < lg.zero) if lg.bear else (self.high > lg.zero)):
                        lg.mssOk = True
                    swingAfter = ((self.slB.size() > 0 and self.slB.last() > lg.oneBar) if lg.bear
                                  else (self.shB.size() > 0 and self.shB.last() > lg.oneBar))
                    if not lg.done and lg.zone == "" and not lg.cMss and not lg.fs and not lg.hasFs and not swingAfter:
                        deeper = (self.high > lg.one and self.close <= lg.one) if lg.bear else (self.low < lg.one and self.close >= lg.one)
                        if deeper:
                            lg.one = self.high if lg.bear else self.low
                            lg.oneBar = bi
                            lg.drOne = lg.one
                            lg.redraw = True
                    else:
                        # note: a leg that expired on this bar (lg.done) still gets f_stepCont (it does not test lg.done), like the Pine
                        fsOnly = lg.hasFs and not lg.fs and self.iFsOnly != "Off"
                        fsAll = fsOnly and self.iFsOnly == "Every setup of the main leg"
                        # the hunt-leg setup, then the silver bullet (only if the first gave no signal), then the zone
                        # reversal; Pine: one f_signal call site
                        for step in (0, 1, 2):
                            if ((not fired and not lg.done and not fsOnly) if step == 2 else
                                    (not firedC and not fsAll and ((self.iHunt and not lg.cDone) if step == 0 else (self.iSbEntry and not lg.sbDone)))):
                                self.rqs = []
                                asked = self.f_stepCont(lg) if step == 0 else self.f_stepSb(lg) if step == 1 else self.f_stepLeg(lg)
                                if asked and len(self.rqs) > 0:
                                    ok = self.f_signal(*self.rqs.pop())
                                    if step == 2:
                                        fired = ok
                                    else:
                                        firedC = ok
        return fired

    # ---- L2637 ----
    def init_2637(self):
        self.histLegs = PArr()   # array<Leg>

    # ---- L2638 ----
    def f_hasTrade(self, lg):
        has = False
        for tr in self.trades:
            if tr.legBar == lg.oneBar:
                has = True
        return has

    # ---- L2644 ----
    def f_showSig(self, lg):
        return lg.signaled and (lg.oneBar == self.st.lastSig or self.f_hasTrade(lg))

    # ---- L2645: only moves drawings; returns x2 like the Pine ----
    def f_freezeLeg(self, lg):
        x2 = pmin(self.bar_index, self.f_fibEnd(lg))
        return x2

    # ---- L2657: deletes the drawings and empties the arrays (their sizes are tested in f_upkeep / f_signal) ----
    def f_hide(self, lg):
        if lg.lns is not None:
            lg.lns.clear()
        if lg.lbs is not None:
            lg.lbs.clear()
        if lg.bxs is not None:
            lg.bxs.clear()
        return _nsz(lg.lns)

    # ---- L2669: Clean view: the leg of a book that is drawn ----
    def f_primary(self, book):
        best = -1
        bestPri = -1
        n = book.size()
        if n > 0:
            for k in prange(0, n - 1):
                lg = book.get(k)
                if not lg.done and (lg.mssOk or not self.iMssDraw) and (self.st.liveLeg < 0 or lg.oneBar == self.st.liveLeg):
                    pri = 2 if (lg.zone != "" or (lg.cMss and not lg.cDone)) else 0 if lg.fs else 1
                    if pri >= bestPri:
                        best = k
                        bestPri = pri
        return best

    # ---- L2683: drawings of the legs + finished legs leave the book (kept in histLegs for display) ----
    def f_upkeep(self, book):
        prim = self.f_primary(book) if self.iClean else -1
        n = book.size()
        if n > 0:
            for k in prange(n - 1, 0):
                lg = book.get(k)
                if lg.redraw:
                    lg.redraw = False
                    self.f_hide(lg)
                    if not self.iClean:
                        self.f_drawLeg(lg)
                if not lg.done:
                    if not self.iClean:
                        if _nsz(lg.lns) == 0:  # a new leg, or one from before the drawing window when it reaches it
                            self.f_drawLeg(lg)
                        else:
                            self.f_extendLeg(lg)
                    elif k == prim or self.f_showSig(lg):
                        if _nsz(lg.lns) == 0:
                            self.f_drawLeg(lg)
                        else:
                            self.f_extendLeg(lg)
                    elif _nsz(lg.lns) > 0:
                        self.f_hide(lg)
                if lg.done:
                    if not lg.cleaned:
                        keep = ((self.iHist != "Live legs only" and (not self.iClean or self.f_showSig(lg))) if lg.signaled
                                else (not self.iClean and self.iHist == "All legs" and lg.endWhy != "replaced by the last stop hunt"))
                        if keep and self.iClean and _nsz(lg.lns) == 0:
                            self.f_drawLeg(lg)
                        if keep and _nsz(lg.lns) > 0:
                            self.f_freezeLeg(lg)
                            if not lg.signaled and lg.endWhy != "":
                                lg.lbs.push(0)  # label "SDP ended: " + lg.endWhy (drawing; placeholder keeps the size)
                            self.histLegs.push(lg)
                            while self.histLegs.size() > self.iHistN:
                                self.f_deleteLeg(self.histLegs.shift())
                        else:
                            self.f_deleteLeg(lg)
                    book.remove(k)
        return book.size()

    # ---- L2723-2732: one call site each, looped over both sides; then the Clean-view history pruning ----
    def top_2723(self):
        for side in prange(0, 1):
            self.f_stepBook(self.bearLegs if side == 0 else self.bullLegs)
        for side in prange(0, 1):
            self.f_upkeep(self.bearLegs if side == 0 else self.bullLegs)
        if self.iClean and self.histLegs.size() > 0:  # Clean view: a finished leg stays only while its trade is open or it gave the newest signal
            for i in prange(self.histLegs.size() - 1, 0):
                h = self.histLegs.get(i)
                if not self.f_showSig(h):
                    self.f_deleteLeg(h)
                    self.histLegs.remove(i)

    # ---- L2734-2783: dashboard (var table dash, f_row, f_contTxt, f_bookTxt, the barstate.islast rows) - display only, dropped ----
