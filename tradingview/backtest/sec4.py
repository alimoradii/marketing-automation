"""Section 4 of the MZ_SDP.pine port: Pine lines 1705-2228.

notes (f_grayNote: label dropped, the st.note* state kept), f_reject, f_note, f_touch, f_resetSetup, lower-timeframe
follow-up (f_track5, f_disp5, f_farFrom5), confirmations (f_3pd, f_smt), the zone-reversal signal f_signal (Trade + siglog)
and the zone-reversal leg step f_stepLeg.
L1706 `var array<label> noteLbs` is drawing only (dropped). The range has no other top-level code, so there are no
init_ / top_ methods. Line numbers are the pre-bedea9e ones (as in sec1-sec3); in the current Pine file this range is
L1752-2275 (+47), unchanged in content.
"""
from base import *


def _utc_stamp(t):
    """str.format_time(t, "yyyyMMddHHmm", "UTC")"""
    return datetime.fromtimestamp(t / 1000, tz=timezone.utc).strftime("%Y%m%d%H%M")


class Sec4:
    # ---- L1707: gray note under / over the price; only its state is kept (the label is drawing) ----
    def f_grayNote(self, buySide, txt):
        st = self.st
        # dupNote (L1708) only decides whether the label is drawn
        if buySide:
            st.noteTxtDn = txt
            st.noteTxtDnBar = self.bar_index
        else:
            st.noteTxtUp = txt
            st.noteTxtUpBar = self.bar_index
        slot = 0
        if buySide:
            slot = (st.noteSlotDn + 1) % 4 if self.bar_index - st.noteBarDn <= 12 else 0
            st.noteBarDn = self.bar_index
            st.noteSlotDn = slot
        else:
            slot = (st.noteSlotUp + 1) % 4 if self.bar_index - st.noteBarUp <= 12 else 0
            st.noteBarUp = self.bar_index
            st.noteSlotUp = slot
        # L1725-1731: label position / label.new / noteLbs - drawing only
        return None   # Pine returns the label (na when not drawn)

    # ---- L1734 ----
    def f_reject(self, lg, why):
        self.st.rejected += 1
        if self.iShowRej:
            self.f_grayNote(lg.bear, why)
        return why

    # ---- L1740 ----
    def f_note(self, lg, buySide, why):
        if self.iShowRej and lg.note != why:
            lg.note = why
            self.f_grayNote(buySide, why)
        return why

    # ---- L1746 ----
    def f_touch(self, lg, z, ext):
        lg.zone = z
        lg.touchBar = self.bar_index
        lg.extreme = ext
        lg.extremeBar = self.bar_index
        lg.mssBar = -1
        lg.mssLevel = NA
        lg.ithBar = -1
        lg.z5 = Ltf()
        return z

    # ---- L1757 ----
    def f_resetSetup(self, lg):
        lg.zone = ""
        lg.touchBar = -1
        lg.extreme = NA
        lg.extremeBar = -1
        lg.mssBar = -1
        lg.mssLevel = NA
        lg.ithBar = -1
        lg.z5 = Ltf()
        return lg.zone

    # ---- L1768-1819: walk the lower-timeframe candles not seen yet, in order (the first time: from chart bar fromBar on).
    # A new extreme resets the MSS and, when needHunt, must take an LTF swing (stop hunt); a later candle beyond the LTF
    # swing before the extreme is the MSS (short-term swing or ITH/ITL, like "MSS must break"). True when this walk ends
    # with an MSS after the last extreme. ----
    def f_track5(self, t, buy, fromBar, needHunt, fbBar):
        hit = False
        s = self.x5h.size()
        if self.LTF_MSS and s > 0:
            base = self.n5 - s
            p0 = t.last + 1 - base
            if t.xi < 0:
                p0 = s
                while p0 > 0 and self.x5b.get(p0 - 1) >= fromBar:
                    p0 -= 1
            p0 = pmax(0, p0)
            win = self.iIthLB * self.LTF_N
            hb = self.s5lI if buy else self.s5hI
            hp = self.s5lP if buy else self.s5hP
            pb = (self.s5hI if buy else self.s5lI) if self.MSS_SHORT else (self.i5hI if buy else self.i5lI)
            pp = (self.s5hP if buy else self.s5lP) if self.MSS_SHORT else (self.i5hP if buy else self.i5lP)
            if p0 <= s - 1:
                for p in prange(p0, s - 1):
                    gi = base + p
                    h = self.x5h.get(p)
                    l = self.x5l.get(p)
                    if t.xi < 0 or ((l < t.xp) if buy else (h > t.xp)):
                        t.xi = gi
                        t.xp = l if buy else h
                        t.xt = self.x5t.get(p)
                        t.hunt = not needHunt
                        hit = False
                        nh = hb.size()
                        if needHunt and nh > 0:
                            for k in prange(nh - 1, 0):
                                b = hb.get(k)
                                if b < gi:
                                    t.hunt = b >= gi - win and ((hp.get(k) > l) if buy else (hp.get(k) < h))
                                    break
                    elif t.hunt and not hit:
                        n = pb.size()
                        if n > 0:
                            for k in prange(n - 1, 0):
                                b = pb.get(k)
                                if b < t.xi:
                                    pk = pp.get(k)
                                    if b >= t.xi - win and ((h > pk) if buy else (l < pk)):
                                        hit = True
                                        pos = self.f_p5(b)
                                        t.zero = pk
                                        t.zeroBar = self.x5b.get(pos) if pos >= 0 else fbBar
                                    break
            t.last = self.n5 - 1
        return hit

    # ---- L1821: displacement on the lower timeframe: a candle from the LTF extreme on with body >= 50% of its range and
    # range >= ATR x ----
    def f_disp5(self, buy, fromI):
        d = False
        s = self.x5h.size()
        p0 = pmax(0, self.f_p5(fromI) + (0 if self.iDispHunt else 1))
        if s > 0 and p0 <= s - 1:
            for p in prange(p0, s - 1):
                rng = self.x5h.get(p) - self.x5l.get(p)
                body = (self.x5c.get(p) - self.x5o.get(p)) if buy else (self.x5o.get(p) - self.x5c.get(p))
                a = self.x5a.get(p)
                if rng > 0 and body >= 0.5 * rng and (na(a) or rng >= self.iDispAtr * a):
                    d = True
                    break
        return d

    # ---- L1836: end of the displacement leg that starts at an LTF extreme: its later LTF candles in that chart bar (not the
    # part of the bar before the extreme), then the chart bars after it; ties go to the earlier bar like the chart loops ----
    def f_farFrom5(self, t, buy, xB):
        far = t.xp
        farB = xB
        s = self.x5h.size()
        p0 = self.f_p5(t.xi)
        if p0 >= 0 and p0 < s:
            for p in prange(p0, s - 1):
                if ne(self.x5b.get(p), xB):
                    break
                if (self.x5h.get(p) > far) if buy else (self.x5l.get(p) < far):
                    far = self.x5h.get(p) if buy else self.x5l.get(p)
        if self.bar_index > xB:
            for k in prange(0, self.bar_index - xB - 1):
                if (self.h_(k) >= far) if buy else (self.l_(k) <= far):
                    far = self.h_(k) if buy else self.l_(k)
                    farB = self.bar_index - k
        return [far, farB]

    # ---- L1856: 3 PD arrays failed (CISD, FVG, wick 50%) - grade only ----
    def f_3pd(self, lg):
        bear = lg.bear
        x = lg.extremeBar
        a0 = pmax(0, lg.ithBar)
        ox = self.bar_index - x
        cnt = 1
        lvl = self.f_cisdAt(ox, not bear)
        cisdFail = False
        if ox >= 1:
            for k in prange(0, ox - 1):
                if (self.c_(k) > lvl) if bear else (self.c_(k) < lvl):
                    cisdFail = True
                    break
        cnt += 1 if cisdFail else 0
        fvgFail = False
        gs = self.gaps.size()
        if gs > 0:
            for idx in prange(0, gs - 1):
                g = self.gaps.get(idx)
                if g.bar >= a0 and g.bar <= x and g.bull != bear:
                    og = self.bar_index - g.bar
                    if og >= 1:
                        for k in prange(0, og - 1):
                            if (self.c_(k) > g.top) if bear else (self.c_(k) < g.bottom):
                                fvgFail = True
                                break
                    if fvgFail:
                        break
        cnt += 1 if fvgFail else 0
        bestO = -1
        bestW = 0.0
        for oi in prange(self.bar_index - a0, ox):   # counts down (or up when a0 > x), like Pine
            rng = self.h_(oi) - self.l_(oi)
            wk = (self.h_(oi) - pmax(self.o_(oi), self.c_(oi))) if bear else (pmin(self.o_(oi), self.c_(oi)) - self.l_(oi))
            if rng > 0 and wk >= 0.5 * rng and wk > bestW:
                bestO = oi
                bestW = wk
        wickFail = False
        if bestO >= 1:
            mid = (self.h_(bestO) - bestW / 2) if bear else (self.l_(bestO) + bestW / 2)
            for k in prange(0, bestO - 1):
                if (self.c_(k) > mid) if bear else (self.c_(k) < mid):
                    wickFail = True
                    break
        cnt += 1 if wickFail else 0
        return cnt

    # ---- L1903: SMT divergence with the second symbol (grade only) ----
    def f_smt(self, lg):
        bear = lg.bear
        b0 = self.f_lastBarBefore(self.slB if bear else self.shB, lg.touchBar)
        res = False
        if b0 >= 0:
            useLow = bear != self.iSmtInv
            ref = NA
            now = NA
            for b in prange(pmax(0, b0 - 1), pmin(self.bar_index, b0 + 1)):
                v = self.smtL_(self.bar_index - b) if useLow else self.smtH_(self.bar_index - b)
                if not na(v):
                    ref = v if na(ref) else (pmin(ref, v) if useLow else pmax(ref, v))
            for b in prange(lg.touchBar, lg.extremeBar):
                v = self.smtL_(self.bar_index - b) if useLow else self.smtH_(self.bar_index - b)
                if not na(v):
                    now = v if na(now) else (pmin(now, v) if useLow else pmax(now, v))
            res = not na(ref) and not na(now) and ((now >= ref) if useLow else (now <= ref))
        return res

    # ---- L1922: signal of the zone reversal (2022 setup at -2..-2.5 / -3.5..-4): filters, targets, Trade ----
    def f_signal(self, lg, g, win, drHi, drHiB, drLo, drLoB):
        PIP = self.PIP
        buy = lg.bear
        side = "buy" if buy else "sell"
        rej = ""
        entry = ((g.top if buy else g.bottom) if self.iEdge == "Proximal" else (g.top + g.bottom) / 2)
        market = False
        if ((self.close <= entry) if buy else (self.close >= entry)) or (self.iMktEntry and not self.iOnRetrace):
            entry = self.close
            market = True
        stop = (lg.extreme - self.iSlPips * PIP) if buy else (lg.extreme + self.iSlPips * PIP)
        drEq = (drHi + drLo) / 2
        if (self.useDR or (self.iMktEntry and not self.iOnRetrace)) and ((entry >= drEq) if buy else (entry <= drEq)):
            rej = "entry in " + ("premium" if buy else "discount") + " of the dealing range (50% = " + self.f_num(drEq) + ")"
        if rej == "" and ((self.iRevDR and not lg.fs) or (self.iMktEntry and not self.iOnRetrace)):
            rEq = self.f_revEq(lg.bear, lg.one, lg.oneBar)
            if not na(rEq) and ((entry > rEq) if buy else (entry < rEq)):
                rej = "zone in " + ("premium" if buy else "discount") + " of the move it retraces (50% = " + self.f_num(rEq) + ")"
        if rej == "":
            rej = self.f_htfRej(buy, entry)
        if rej == "" and not self.TFOK:
            rej = "chart is " + self.timeframe_period + "m - signals only on 15m (setting)"
        if rej == "" and self.iOneSwing and self.usedStops.includes(pround(stop / PIP * 10) * (1 if buy else -1)):
            rej = "this stop-hunt swing already gave a trade (one trade per swing)"
        risk = (entry - stop) if buy else (stop - entry)
        if risk <= 0:
            rej = "invalid risk"
        elif self.iUseMinStop and risk < self.iMinStop * PIP:
            rej = "stop too tight (" + tstr(risk / PIP, "0.0") + " pips)"
        # entry leg: zone extreme (fib 1) to the swing before it (fib 0) - on the lower timeframe when the MSS came from there
        tz = lg.z5.zero if lg.z5.mss else self.f_lastBefore(self.shB if buy else self.slB, self.shP if buy else self.slP, lg.extremeBar)
        tzB = lg.z5.zeroBar if lg.z5.mss else self.f_lastBarBefore(self.shB if buy else self.slB, lg.extremeBar)
        if rej == "" and na(tz):
            rej = "no swing for the entry leg"
        unit = NA if na(tz) else ((tz - lg.extreme) if buy else (lg.extreme - tz))
        if rej == "" and unit <= 0:
            rej = "entry leg invalid"
        main = NA
        partial = NA
        rr = 0.0
        tpWhy = ""
        tpTag = ""
        extMode = self.iTgtMode == "External liquidity"
        if rej == "":
            m0, w0, g0 = self.f_mainTarget(buy, entry, risk, tz, lg.extreme, drEq, drHi if buy else drLo,
                                           lg.drOne if extMode else ((tz + self.iTgt * unit) if buy else (tz - self.iTgt * unit)),
                                           "fib 1 of the hunt leg" if extMode else "-" + tstr(self.iTgt))
            main = m0
            tpWhy = w0
            tpTag = g0
            if (main <= entry) if buy else (main >= entry):
                rej = "target not beyond entry"
            partial = drEq if extMode else ((tz + self.iPart * unit) if buy else (tz - self.iPart * unit))
            partial = (partial - self.iTpBuf * PIP) if buy else (partial + self.iTpBuf * PIP)
            if not ((entry < partial and partial < main) if buy else (main < partial and partial < entry)):
                partial = NA
            rr = ((main - entry) if buy else (entry - main)) / risk
            if rej == "" and self.iMinRR > 0 and rr < self.iMinRR:
                rej = "R:R 1:" + tstr(rr, "0.0") + " below the minimum 1:" + tstr(self.iMinRR, "0.0") + tpWhy
        warn = ""
        if rej == "" and self.MOF and not na(self.midOpen) and ((entry >= self.midOpen) if buy else (entry <= self.midOpen)):
            if self.STRICT or self.iMOHard:
                rej = "wrong side of NY Open"
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
            self.f_reject(lg, rej)
        else:
            st = self.st
            nPD = self.f_3pd(lg) if self.iUse3PD else 0
            pd3 = self.iUse3PD and nPD >= 3
            htfOk = self.iUseHTF and self.htfTrend == (1 if buy else -1)
            # no second-symbol data in the engine (smtH / smtL = this symbol): iUseSMT_data keeps SMT from confirming
            smtOk = self.iUseSMT and self.iUseSMT_data and self.f_smt(lg)
            sbOk = self.iUseSB and self.inSB
            dblOk = self.f_lastBarBefore(self.slB if buy else self.shB, self.bar_index) > lg.mssBar
            maxScore = 2 + (1 if self.iUseSB else 0) + (1 if self.iUse3PD else 0) + (1 if self.iUseHTF else 0) + (1 if self.iUseSMT else 0)
            score = (1 if pd3 else 0) + (1 if htfOk else 0) + (1 if sbOk else 0) + (1 if smtOk else 0) + (1 if lg.tsoup else 0) + (1 if dblOk else 0)
            grade = "A+" if score >= 3 else "A" if score >= 1 else "B"
            if eqLeft != "" or warn != "":
                grade = "B"
            emitted = True
            lg.signaled = True
            st.dayCount += 1
            st.signals += 1
            sid = self.TK + "-" + self.timeframe_period + "-" + side + "-" + _utc_stamp(self.time_close) + "-" + tstr(st.signals)  # unique: two setups can signal on one bar
            trNew = Trade(sid, not buy, entry, stop, partial, main, self.bar_index + self.validBars, market, legBar=lg.oneBar)
            trNew.warn = self.f_warn(buy, entry)
            self.trades.push(trNew)
            self.f_stratOpen(trNew, grade)   # no-op in the indicator (sec3), kept for the Pine call order
            kind = ("FS" if lg.fs else "zone -2" if lg.zone == "Z2" else "zone -3.5") + ((" " + self.iLtfTf + "m") if lg.z5.mss else "")
            self.siglog.append(dict(id=sid, bar=self.bar_index, time=self.time, side='sell' if trNew.sell else 'buy',
                                    entry=trNew.entry, stop=trNew.stop, tp1=trNew.tp1, tpMain=trNew.tpMain, market=trNew.market,
                                    kind=kind, grade=grade, warn=trNew.warn,
                                    setup="failure_swing" if lg.fs else "reversal", zone=lg.zone, ltf=lg.z5.mss,
                                    score=score, maxScore=maxScore, rr=rr, tpTag=tpTag, legBar=lg.oneBar, tz=tz, tzB=tzB,
                                    drHi=drHi, drLo=drLo, win=win))
            self.usedStops.push(pround(stop / PIP * 10) * (1 if buy else -1))
            if self.usedStops.size() > 50:
                self.usedStops.shift()
            st.liveLeg = lg.oneBar
            st.lastSig = lg.oneBar
            # L2035-2071: zoneTxt / ltfTxt, trade lines, dealing-range boxes, FVG box, entry-leg SDP, signal label
            # (trNew.lab / tip / mini / kind are only set for drawing; DRAW is True so mini / kind stay unset) and alerts:
            # drawing / alerts only
        return emitted

    # ---- L2074: one step of a zone-reversal leg: zone -2..-2.5 / -3.5..-4 reached, stop hunt + MSS, displacement, FVG ----
    def f_stepLeg(self, lg):
        out = False
        bear = lg.bear
        ext = self.low if bear else self.high
        go = True
        if (self.close > lg.one) if bear else (self.close < lg.one):
            lg.done = True
            lg.endWhy = "closed beyond fib 1"
            go = False
        if go and lg.z2Alive:
            cb = self.f_beyond(bear, self.close, self.f_lvl(lg, self.iZ2b))
            kill = False
            if self.iZ2Grace and lg.z2Pend >= 0 and self.bar_index > lg.z2Pend:
                lg.z2Pend = -1
                kill = cb
            elif cb:
                if self.iZ2Grace:
                    lg.z2Pend = self.bar_index
                else:
                    kill = True
            if kill:
                lg.z2Alive = False
                if lg.zone == "Z2":
                    self.f_resetSetup(lg)
        if go and lg.z3Alive and self.f_beyond(bear, self.close, self.f_lvl(lg, self.iZ3b)):
            lg.z3Alive = False
            lg.done = True
            lg.endWhy = "closed beyond -4, redraw"
            go = False
        if go and lg.zone == "":
            if lg.z2Alive and self.f_reach(bear, ext, self.f_lvl(lg, self.iZ2a)):
                self.f_touch(lg, "Z2", ext)
            elif not lg.z2Alive and lg.z3Alive and self.f_reach(bear, ext, self.f_lvl(lg, self.iZ3a)):
                self.f_touch(lg, "Z3", ext)
            if lg.zone == "":
                go = False
        if go and ((self.low < lg.extreme) if bear else (self.high > lg.extreme)):
            lg.extreme = ext
            lg.extremeBar = self.bar_index
            lg.mssBar = -1
            lg.mssLevel = NA
            lg.ithBar = -1
            lg.z5.mss = False
        if go and lg.extremeBar == self.bar_index:
            for sw in self.sweptNow:
                if sw.bsl != bear:
                    lg.tsoup = True
        if go and lg.mssBar < 0:
            m5 = False
            if self.LTF_MSS:
                m5 = self.f_track5(lg.z5, bear, lg.touchBar, True, lg.extremeBar)
            bI = -1
            pI = NA
            m15 = False
            if self.bar_index > lg.extremeBar:
                pb = (self.shB if bear else self.slB) if self.MSS_SHORT else (self.ithB if bear else self.itlB)
                pp = (self.shP if bear else self.slP) if self.MSS_SHORT else (self.ithP if bear else self.itlP)
                n = pb.size()
                if n > 0:
                    for k in prange(n - 1, 0):
                        b = pb.get(k)
                        if b < lg.extremeBar:
                            if b >= lg.extremeBar - self.iIthLB:
                                bI = b
                                pI = pp.get(k)
                            break
                m15 = bI >= 0 and ((self.high > pI) if bear else (self.low < pI))
            if not m15 and m5:  # the chart timeframe first; the lower one only when it shows no MSS (notes: 15m main, 5m when 15m has no clear leg)
                bI = lg.z5.zeroBar
                pI = lg.z5.zero
            if m15 or m5:
                lg.mssBar = self.bar_index
                lg.mssLevel = pI
                lg.ithBar = bI
                lg.z5.mss = not m15
                drMid = (lg.extreme + lg.drOne) / 2
                if self.useDR and ((pI > drMid) if bear else (pI < drMid)):
                    self.f_reject(lg, "MSS in premium of dealing range (turtle soup)" if bear else "MSS in discount of dealing range (turtle soup)")
                    lg.done = True
                    lg.endWhy = "fake MSS (turtle soup)"
                    go = False
                else:
                    self.f_drawMss(bI, pI, ("MSS " + self.iLtfTf + "m") if lg.z5.mss else "MSS")
            else:
                go = False
        if go and self.iDisp:
            disp = False
            ob = self.bar_index - lg.extremeBar
            if ob >= 1:
                for k in prange(0, ob - (0 if self.iDispHunt else 1)):
                    rng = self.h_(k) - self.l_(k)
                    body = (self.c_(k) - self.o_(k)) if bear else (self.o_(k) - self.c_(k))
                    if rng > 0 and body >= 0.5 * rng and (na(self.atr_(k)) or rng >= self.iDispAtr * self.atr_(k)):
                        disp = True
                        break
            if not disp and lg.z5.mss:
                disp = self.f_disp5(bear, lg.z5.xi)
            if not disp:
                self.f_note(lg, bear, "MSS without displacement (candle >= " + tstr(self.iDispAtr) + " ATR) - no signal yet")
            go = disp
        if go:
            ox = self.bar_index - lg.extremeBar
            far = self.high if bear else self.low
            farBar = self.bar_index
            for k in prange(0, ox):
                if (self.h_(k) >= far) if bear else (self.l_(k) <= far):
                    far = self.h_(k) if bear else self.l_(k)
                    farBar = self.bar_index - k
            if lg.z5.mss:
                f5, f5B = self.f_farFrom5(lg.z5, bear, self.f_bar5(lg.z5.xi, lg.extremeBar))
                far = f5
                farBar = f5B
            dispEnd = farBar if self.iFvgDisp else self.bar_index
            # dealing range: BSL = the hunt of the SDP (fib 1), SSL = the zone extreme (mirror for a sell); wider if price went past fib 1
            oneB = lg.parentBar if lg.fs else lg.oneBar
            farOut = (far > lg.drOne) if bear else (far < lg.drOne)
            drHi = (far if farOut else lg.drOne) if bear else lg.extreme
            drHiB = (farBar if farOut else oneB) if bear else lg.extremeBar
            drLo = lg.extreme if bear else (far if farOut else lg.drOne)
            drLoB = lg.extremeBar if bear else (farBar if farOut else oneB)
            drEq = (drHi + drLo) / 2
            if self.DR_CHART and self.f_drReady():  # the dealing range on the chart (BSL <-> SSL) as it is now
                drHi = self.dr.hi
                drHiB = self.dr.hiB
                drLo = self.dr.lo
                drLoB = self.dr.loB
                drEq = (drHi + drLo) / 2
            eq = (lg.extreme + far) / 2
            if self.useDR:
                eq = pmin(eq, drEq) if bear else pmax(eq, drEq)
            best = self.f_mssMkt(bear, eq) if lg.mssBar == self.bar_index else None
            gs = self.gaps.size() if best is None else 0
            if gs > 0:
                for idx in prange(pmax(0, gs - 60), gs - 1):
                    g = self.gaps.get(idx)
                    if (g.bar - (1 if self.iDispHunt else 2) >= lg.extremeBar and g.bar <= dispEnd and not g.filled and g.bull == bear
                            and not self.usedFvg.includes(g.bar if bear else -g.bar) and self.f_drOk(self.f_gapEntry(g, bear), bear, drEq)):
                        ce = (g.top + g.bottom) / 2
                        if not self.iPD or ((ce <= eq) if bear else (ce >= eq)):
                            if best is None or ((g.top > best.top) if bear else (g.bottom < best.bottom)):
                                best = g
            if best is None:
                best = self.f_best5(bear, lg.extremeBar, eq, True, dispEnd, lg.z5.xt if lg.z5.mss else 0, drEq)
            if best is None:
                best = self.f_noFvg(bear, farBar, lg.mssLevel, eq)
            if best is None:
                self.f_note(lg, bear, "MSS" + ((" " + self.iLtfTf + "m") if lg.z5.mss else "") + " ✓ · FVG in " + ("discount" if bear else "premium") + " ✕ (waiting)")
            elif self.winNow == "":
                self.f_note(lg, bear, "MSS ✓ · FVG ✓ · killzone / silver bullet ✕")
            if best is None or self.winNow == "":
                go = False
            if go:
                lg.done = True
                self.f_useGap(best, bear)
                out = self.f_signal(lg, best, self.winNow, drHi, drHiB, drLo, drLoB)
        return out
