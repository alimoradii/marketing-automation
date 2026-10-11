"""Section 5 of the MZ_SDP.pine port: Pine lines 2229-2784.

the hunt-leg / silver-bullet signal f_signalCont (Trade + siglog), the hunt-leg step f_stepCont, the silver-bullet step
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
    # ---- L2230: signal of the hunt-leg setup ("continuation") or the silver bullet at -1..-1.5 ("silver_bullet") ----
    def f_signalCont(self, lg, g, win, stopRef, mainPx, setupName, drHi, drHiB, drLo, drLoB):
        PIP = self.PIP
        isSb = setupName == "silver_bullet"
        buy = not lg.bear
        side = "buy" if buy else "sell"
        rej = ""
        entry = ((g.top if buy else g.bottom) if self.iEdge == "Proximal" else (g.top + g.bottom) / 2)
        market = False
        if ((self.close <= entry) if buy else (self.close >= entry)) or (self.iMktEntry and not self.iOnRetrace):
            entry = self.close
            market = True
        sRef = lg.one if na(stopRef) else stopRef
        # hunt setup entered on the lower timeframe: targets on the LTF leg (hunt extreme -> LTF swing it broke), like the zone setup
        ltf = (not isSb) and lg.c5.mss
        lz = lg.c5.zero if ltf else lg.zero
        l1 = sRef if ltf else lg.one
        drEq = (drHi + drLo) / 2
        if (self.useDR or (self.iMktEntry and not self.iOnRetrace)) and ((entry >= drEq) if buy else (entry <= drEq)):
            rej = "entry in " + ("premium" if buy else "discount") + " of the dealing range (50% = " + self.f_num(drEq) + ")"
        if rej == "":
            rej = self.f_htfRej(buy, entry)
        if rej == "" and not self.TFOK:
            rej = "chart is " + self.timeframe_period + "m - signals only on 15m (setting)"
        stop = (sRef - self.iSlPips * PIP) if buy else (sRef + self.iSlPips * PIP)
        if rej == "" and self.iOneSwing and self.usedStops.includes(pround(stop / PIP * 10) * (1 if buy else -1)):
            rej = "this stop-hunt swing already gave a trade (one trade per swing)"
        risk = (entry - stop) if buy else (stop - entry)
        main = NA
        partial = lz - self.iPart * (l1 - lz)
        partial = (partial - self.iTpBuf * PIP) if buy else (partial + self.iTpBuf * PIP)
        rr = 0.0
        tpWhy = ""
        tpTag = ""
        if risk <= 0:
            rej = "invalid risk"
        elif self.iUseMinStop and risk < self.iMinStop * PIP:
            rej = "stop too tight (" + tstr(risk / PIP, "0.0") + " pips)"
        if rej == "":
            # silver bullet keeps its -2 (the move goes on); the hunt setup takes the first SDP zone of the hunt leg in premium / discount
            m0, w0, g0 = self.f_mainTarget(buy, entry, risk, lz, l1, NA if isSb else drEq, drHi if buy else drLo,
                                           (lz - self.iTgt * (l1 - lz)) if na(mainPx) else mainPx,
                                           "-" + tstr(self.iZ2a if isSb else self.iTgt))
            main = m0
            tpWhy = w0
            tpTag = g0
            if (main <= entry) if buy else (main >= entry):
                rej = "target not beyond entry"
            if not ((entry < partial and partial < main) if buy else (main < partial and partial < entry)):
                partial = NA
            rr = ((main - entry) if buy else (entry - main)) / risk
            if rej == "" and self.iMinRR > 0 and rr < self.iMinRR:
                rej = "R:R 1:" + tstr(rr, "0.0") + " below the minimum 1:" + tstr(self.iMinRR, "0.0") + tpWhy
        warn = ""
        if rej == "" and self.MOF and not na(self.midOpen) and ((entry >= self.midOpen) if buy else (entry <= self.midOpen)):
            if self.iMOHard:  # (the zone setup also rejects on STRICT; this one only on iMOHard, like the Pine)
                rej = "entry " + ("above" if buy else "below") + " NY Open " + self.f_num(self.midOpen)
            else:
                warn += "wrong side of NY Open; "
        eqLeft = ""
        if rej == "" and self.iUB:
            farPx = (stop - self.iUBPips * PIP) if buy else (stop + self.iUBPips * PIP)
            eqName = "Equal Lows" if buy else "Equal Highs"
            for l in self.levels:
                near = l.bsl != buy and ((l.price >= farPx and l.price <= entry) if buy else (l.price <= farPx and l.price >= entry))
                if near and (l.kind == "session" or l.kind == "day" or l.kind == "week") and warn == "":
                    if self.STRICT:
                        rej = "unfinished business: " + l.name + " " + self.f_num(l.price) + " not taken"
                        break
                    else:
                        warn += "unfinished business: " + l.name + " " + self.f_num(l.price) + "; "
                if near and l.name == eqName and eqLeft == "":
                    eqLeft = l.name + " " + self.f_num(l.price)
            if rej == "" and eqLeft != "" and self.iUBEq and self.STRICT:
                rej = "unfinished business: " + eqLeft + " not taken"
        if rej == "" and self.iHtfReq and ne(self.htfTrend, (1 if buy else -1)):
            rej = "against higher timeframe"
        if rej == "":
            nws = self.f_newsAt(self.time_close) if self.iUseNews else ""
            if nws != "":
                rej = "news: " + nws
        emitted = False
        if rej != "":
            self.st.rejected += 1
            if self.iShowRej:
                self.f_grayNote(buy, ("silver bullet setup: " if isSb else "hunt setup: ") + rej)
        else:
            st = self.st
            htfOk = self.iUseHTF and self.htfTrend == (1 if buy else -1)
            sbOk = self.iUseSB and self.inSB
            maxScore = (1 if self.iUseSB else 0) + (1 if self.iUseHTF else 0)
            score = (1 if htfOk else 0) + (1 if sbOk else 0)
            grade = "A+" if score >= 2 else "A" if score == 1 else "B"
            if eqLeft != "" or warn != "":
                grade = "B"
            emitted = True
            lg.signaled = True
            st.dayCount += 1
            st.signals += 1
            sid = self.TK + "-" + self.timeframe_period + "-" + side + "-" + _utc_stamp5(self.time_close) + "-" + tstr(st.signals)  # unique: two setups can signal on one bar
            trNew = Trade(sid, not buy, entry, stop, partial, main, self.bar_index + self.validBars, market, legBar=lg.oneBar)
            trNew.warn = self.f_warn(buy, entry)
            self.trades.push(trNew)
            self.f_stratOpen(trNew, grade)
            kind = "SB" if isSb else (("hunt " + self.iLtfTf + "m") if ltf else "hunt")  # = trNew.kind of the small marker (L2357)
            self.siglog.append(dict(id=sid, bar=self.bar_index, time=self.time, side='sell' if trNew.sell else 'buy',
                                    entry=trNew.entry, stop=trNew.stop, tp1=trNew.tp1, tpMain=trNew.tpMain, market=trNew.market,
                                    kind=kind, grade=grade, warn=trNew.warn,
                                    setup=setupName, zone="", ltf=ltf,
                                    score=score, maxScore=maxScore, rr=rr, tpTag=tpTag, legBar=lg.oneBar, tz=lz, tzB=(lg.c5.zeroBar if ltf else lg.zeroBar),
                                    drHi=drHi, drLo=drLo, win=win))
            self.usedStops.push(pround(stop / PIP * 10) * (1 if buy else -1))
            if self.usedStops.size() > 50:
                self.usedStops.shift()
            st.liveLeg = lg.oneBar
            st.lastSig = lg.oneBar
            # L2334-2368: zoneTxt / ltfTxt, trade lines (f_tradeLines), dealing-range boxes (f_drawDR), FVG box (f_drawFvg),
            # f_clearSigSdp / entry-leg SDP (f_sigSdp), signal label (trNew.lab / tip; DRAW is True so mini / kind stay unset)
            # and alerts: drawing / alerts only
        return emitted

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
                    disp = not self.iDisp
                    ob = bi - lg.oneBar
                    if not disp and ob >= 1:
                        for k in prange(0, ob - (0 if self.iDispHunt else 1)):
                            j = bi - k  # high[k] = H[bar_index - k]
                            rng = H[j] - L[j]
                            body = (C[j] - O[j]) if buy else (O[j] - C[j])
                            a = ATR[j]
                            if rng > 0 and body >= 0.5 * rng and (na(a) or rng >= self.iDispAtr * a):
                                disp = True
                                break
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
            self.f_oppHunt(lg)
            base = lg.zero if na(lg.oppPx) else lg.oppPx
            baseB = lg.zeroBar if na(lg.oppPx) else lg.oppBar
            farOut = (farC > base) if buy else (farC < base)
            drHi = (farC if farOut else base) if buy else hl
            drHiB = (farCBar if farOut else baseB) if buy else hlB
            drLo = hl if buy else (farC if farOut else base)
            drLoB = hlB if buy else (farCBar if farOut else baseB)
            drEq = (drHi + drLo) / 2
            if self.DR_CHART and self.f_drReady():  # the dealing range on the chart (BSL <-> SSL) as it is now
                drHi = self.dr.hi
                drHiB = self.dr.hiB
                drLo = self.dr.lo
                drLoB = self.dr.loB
                drEq = (drHi + drLo) / 2
            eqD = (pmin(eq, drEq) if buy else pmax(eq, drEq)) if self.useDR else eq
            best = self.f_mssMkt(buy, eqD) if lg.cMssBar == bi else None
            gs = self.gaps.size() if best is None else 0
            if gs > 0:
                for idx in prange(max(0, gs - 60), gs - 1):
                    g = self.gaps.get(idx)
                    if (g.bar - (1 if self.iDispHunt else 2) >= hlB and g.bar < bi and g.bar <= dispEndC and not g.filled and g.bull == buy
                            and not self.usedFvg.includes(g.bar if buy else -g.bar) and self.f_drOk(self.f_gapEntry(g, buy), buy, drEq)):
                        if not self.iPD or ((g.bottom <= eq) if buy else (g.top >= eq)):
                            if best is None or ((g.top > best.top) if buy else (g.bottom < best.bottom)):
                                best = g
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
                ent = ((best.top if buy else best.bottom) if self.iEdge == "Proximal" else (best.top + best.bottom) / 2)
                if ((self.close <= ent) if buy else (self.close >= ent)) or (self.iMktEntry and not self.iOnRetrace):
                    ent = self.close
                if (ent >= self.midOpen) if buy else (ent <= self.midOpen):
                    go = False
                    self.f_note(lg, buy, "MSS ✓ · FVG ✓ · entry " + ("below" if buy else "above") + " NY Open ✕ (waiting)")
            if go:
                oppBook = self.bearLegs if buy else self.bullLegs
                for x in (PArr() if lg.inZone else oppBook):  # a hunt at a reversal zone is not "against"
                    if (self.AGL >= 0 and not x.done and x.oneBar < lg.oneBar
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
                out = self.f_signalCont(lg, best, self.winNow, hl if ltf else NA, NA, "continuation", drHi, drHiB, drLo, drLoB)
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
                    pb = self.shB if buy else self.slB
                    pp = self.shP if buy else self.slP
                    bI = -1
                    pI = NA
                    n = pb.size()
                    if n > 0:
                        for k in prange(n - 1, 0):
                            b = pb.get(k)
                            if b < lg.sbExtBar:
                                if b >= lg.sbTouch - self.iIthLB:
                                    bI = b
                                    pI = pp.get(k)
                                break
                    if bI >= 0 and ((self.high > pI) if buy else (self.low < pI)):
                        disp = not self.iDisp
                        ob = bi - lg.sbExtBar
                        if not disp and ob >= 1:
                            for k in prange(0, ob - 1):
                                j = bi - k
                                rng = H[j] - L[j]
                                body = (C[j] - O[j]) if buy else (O[j] - C[j])
                                a = ATR[j]
                                if rng > 0 and body >= 0.5 * rng and (na(a) or rng >= self.iDispAtr * a):
                                    disp = True
                                    break
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
                    rTopB = bi
                    for k in prange(0, bi - lg.oneBar):
                        j = bi - k
                        if (H[j] > rTop) if buy else (L[j] < rTop):
                            rTop = H[j] if buy else L[j]
                            rTopB = bi - k
                    drHi = rTop if buy else lg.sbExt
                    drHiB = rTopB if buy else lg.sbExtBar
                    drLo = lg.sbExt if buy else rTop
                    drLoB = lg.sbExtBar if buy else rTopB
                    drEq = (drHi + drLo) / 2
                    if self.DR_CHART and self.f_drReady():  # the dealing range on the chart (BSL <-> SSL) as it is now
                        drHi = self.dr.hi
                        drHiB = self.dr.hiB
                        drLo = self.dr.lo
                        drLoB = self.dr.loB
                        drEq = (drHi + drLo) / 2
                    best = None
                    gs = self.gaps.size()
                    if gs > 0:
                        for idx in prange(max(0, gs - 60), gs - 1):
                            g = self.gaps.get(idx)
                            if (g.bar - 2 >= lg.sbExtBar and g.bar <= bi and not g.filled and g.bull == buy
                                    and not self.usedFvg.includes(g.bar if buy else -g.bar) and self.f_drOk(self.f_gapEntry(g, buy), buy, drEq)):
                                ce = (g.top + g.bottom) / 2
                                if not self.iPD or ((ce <= eq) if buy else (ce >= eq)):
                                    if best is None or ((g.top > best.top) if buy else (g.bottom < best.bottom)):
                                        best = g
                    if best is not None:
                        lg.sbDone = True
                        self.usedFvg.push(best.bar if buy else -best.bar)
                        if self.usedFvg.size() > 100:
                            self.usedFvg.shift()
                        out = self.f_signalCont(lg, best, "silver_bullet" if self.winNow == "" else self.winNow, lg.sbExt, twoPx,
                                                "silver_bullet", drHi, drHiB, drLo, drLoB)
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
                        if not firedC and self.iHunt and not lg.cDone and not fsAll:
                            firedC = self.f_stepCont(lg)
                        if not firedC and self.iSbEntry and not lg.sbDone and not fsAll:
                            firedC = self.f_stepSb(lg)
                        if not fired and not lg.done and not fsOnly:
                            fired = self.f_stepLeg(lg)
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

    # ---- L2657: deletes the drawings and empties the arrays (their sizes are tested in f_upkeep / f_signalCont) ----
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
