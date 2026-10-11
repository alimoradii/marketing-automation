# Porting MZ_SDP.pine to Python (backtest engine)

Source: /home/user/marketing-automation/tradingview/MZ_SDP.pine (Pine v6, read-only).
Engine dir: tradingview/backtest
Already done in base.py (read it first): inputs (self.iXxx with the Pine defaults), derived globals of lines 13-191 and
369-386, the Pine types (Level, Sweep, Sess, Gap, Hunt, Ltf, Leg, Trade, DRng, Stats as Python classes with the same field
names / defaults, positional args in field order), helpers of lines 362-480 (f_hm .. f_cisdAt as methods), the HTF
request.security values (lines 481-553) and the per-bar built-ins (Base.prelude).

The goal is a FAITHFUL transliteration of the trading logic - the backtest must give the same signals / fills / exits as
TradingView. Do not "improve" or simplify logic. Drop only drawing / alerts / tables / text that nothing reads.

## Structure
* Your file `secN.py` starts with `from base import *` and defines `class SecN:` (a mixin; the final class is
  `class Sim(Sec1, Sec2, Sec3, Sec4, Sec5, Base)`), so every method can call every other Pine function as self.f_xxx.
* Every Pine global (var or not) is an attribute `self.<same name>`. Every Pine function `f_name(a, b)` becomes
  `def f_name(self, a, b)` with the same parameter names. Keep Pine names exactly (other sections call them).
* `var` declarations in your line range -> assign them in `def init_<LINE>(self)` (LINE = Pine line number of the first
  declaration of that block). The runner calls all init_* methods once, sorted by LINE, before bar 0.
* Top-level statements (non-var declarations and if/for blocks outside functions) in your range -> `def top_<LINE>(self)`
  (LINE = Pine line of the first statement of the block). The runner calls all top_* methods every bar sorted by LINE,
  after Base.prelude. Split top-level code at every function definition so the order stays exactly the Pine order.
  A non-var global like `array<Sweep> sweptNow = array.new<Sweep>()` is re-created each bar inside its top_ method.
* Function-local `var` (if any) -> an attribute of self initialised in an init_ method, with a unique name.

## Pine -> Python rules
* na -> `NA` (float nan). `na(x)` -> `na(x)`. `nz(x, y)` -> `nz(x, y)`.
* Pine `a != b` where a or b can be na -> `ne(a, b)` (Pine gives false on na; Python nan != x is True). `==`, `<`, `>`
  with nan are already false in Python, like Pine.
* math.max/min -> `pmax/pmin` (na-propagating), math.abs -> `pabs`, math.round -> `pround`, int(x) -> `pint(x)` when x
  may be na, math.floor/ceil -> pfloor/pceil.
* `for i = a to b` -> `for i in prange(a, b)` ALWAYS (inclusive; counts down when b < a, like Pine).
  `for x in arr` -> `for x in arr` (if the loop body removes from / pushes to that same array, iterate over a copy
  `list(arr)` only if Pine semantics require it - Pine evaluates the array as it is at each step; flag it in a comment).
  `for [i, x] in arr` -> `for i, x in enumerate(arr)`.
* Ternary `c ? a : b` -> `(a if c else b)`; Pine chains are right-associative.
* Arrays: `array.new<T>()` -> `PArr()`; `array.from(...)` -> `afrom(...)`. PArr has the Pine methods: size get set push
  shift unshift first last remove(index) includes indexof pop clear copy. Do NOT use list.remove(value).
* UDT: `Leg.new(a, b, x = 1)` -> `Leg(a, b, x=1)`. `na` object -> `None` (test with `x is None`; `na(obj)` also works).
  Fields that are UDTs default to None (Leg.z5 / Leg.c5 are Ltf objects created where Pine creates them).
* Tuples `[a, b] = f()` -> `a, b = self.f()`; a function returning `[x, y]` returns a list/tuple.
* Built-ins of the current bar: self.open, self.high, self.low, self.close, self.time (open time, ms UTC),
  self.time_close, self.bar_index, self.atr14, self.rngHi, self.rngLo, self.ph, self.pl, self.mod, self.calKey,
  self.htfTrend, self.dTrend, self.h4DrHi, self.h4DrLo, self.dBias, self.dDrHi, self.dDrLo, self.dDrEq, self.dDrOk,
  self.dReact, self.dBT, self.dBB, self.dST, self.dSB, self.dBiasS, self.smtH, self.smtL, self.barstate_isfirst,
  self.barstate_islast, self.change_D (timeframe.change("D")), self.change_W, self.lH/lL/lC/lT/lO (PArr of the 5m candles
  of this 15m bar = request.security_lower_tf result).
* History `high[k]` -> `self.h_(k)`; likewise `low[k]` l_, `close[k]` c_, `open[k]` o_, `time[k]` t_, `atr14[k]` atr_,
  `smtH[k]` smtH_, `smtL[k]` smtL_. (`high[bar_index - b]` -> `self.h_(self.bar_index - b)` or `self.H[b]`.)
  Absolute arrays: self.O, self.H, self.L, self.C, self.T, self.ATR.
* Time: `hour(t, TZ)`, `minute`, `dayofmonth`, `month`, `year`, `dayofweek` -> module functions of the same name;
  `timestamp(TZ, y, m, d, hh, mm)` -> `timestamp(TZ, y, m, d, hh, mm)`; `str.format_time(t, ...)` -> `format_time(t)`.
  `timeframe.change("D")` -> self.change_D; `timeframe.period` -> self.timeframe_period ("15");
  `timeframe.in_seconds()` -> 900; `timeframe.in_seconds(iLtfTf)` -> 300; `timeframe.isintraday` -> True.
* Strings: str.contains(a, b) -> `b in a`; str.startswith(a, b) -> `a.startswith(b)`; str.tostring(x[, fmt]) -> `tstr(x[, fmt])`;
  str.length -> len; str.substring(s, a, b) -> s[a:b]; string concatenation with + as in Pine. Keep every string that
  any logic compares or tests (names, reasons, rej / warn / note texts that are compared with "" or searched).
* Drawing (line/label/box/table/plot/bgcolor/fill) and alert(): delete. If a drawing call returns an object stored in
  state (e.g. `lg.lns.push(line.new(...))`) just drop it. If code READS drawing state (line.get_x1 ...) only for drawing,
  drop that code. Never drop state changes that the trading logic uses. `DRAW` is always True, `iShow*` inputs only
  gate drawing - keep the logic that is under such an `if` when it changes non-drawing state.
* str.tostring formats in ids do not matter.

## Logging (needed by the backtest)
* Where a signal creates a Trade (trades.push(trNew)) also do
  `self.siglog.append(dict(id=..., bar=self.bar_index, time=self.time, side='sell' if trNew.sell else 'buy', entry=..., stop=..., tp1=..., tpMain=..., market=..., kind=<setup name>, grade=grade, warn=trNew.warn))`.
* In f_update(tr, ev, px, r) append `dict(id=tr.id, ev=ev, bar=self.bar_index, time=self.time, px=px, r=r)` to
  `self.trlog` (keep calling everything f_update calls that matters; f_stratEvent/f_stratOpen are no-ops in the indicator).

## Quality
* Port every line of your range in order. Keep Pine comments that explain logic (short).
* At the end, `python3 -c "import ast; ast.parse(open('secN.py').read())"` must pass.
* List in your final answer: methods defined (init_/top_/f_), anything ambiguous, any Pine semantic you were unsure of.
