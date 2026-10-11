# MZ SDP (TradingView)

- `MZ_SDP.pine`: the indicator (signals, SDP, dealing range, dashboard, alerts). The single source of the trading rules.
- `MZ_SDP_strategy.pine`: the same rules as a `strategy()` for the Strategy Tester. **Generated** from the indicator; do not edit it by hand.
- `build_strategy.py`: rebuilds the strategy after any change to the indicator: `python3 tradingview/build_strategy.py`.

## How the strategy trades

- A signal places a limit order at its entry (market signals: a market order), with the stop and the targets as exits. The partial target closes the partial size (input "Partial size") and the rest runs to the main target. The stop is not moved.
- A signal the indicator cancels or lets expire cancels its order. Red news closes the position.
- One trade at a time: while a position or an order of an earlier signal is open, new signals are not taken (the indicator's own dashboard statistics still count every signal).
- Size: risk per trade as % of equity (group "📊 Backtest"). "⚠ reduce size" signals trade at half size by default.
- Costs live in the strategy Properties tab. The default commission (0.00005 per unit per side) is about 1 pip round trip on EURUSD; for crypto, switch the commission to % (e.g. 0.05-0.1 per side). Slippage 2 ticks on market and stop orders.
- Margin is 0 (no leverage limit): the size comes from the risk % alone. With Pine's default 100% margin a 1%-risk FX position (often several times the equity) would be cut down or rejected.
- An order the indicator does not fill by its last valid bar is cancelled at that bar's close. A limit the Strategy Tester filled while the indicator did not (cancel / expiry / opened past the stop) is closed at once, so it never sits without exits.

## Backtest (Python port, `backtest/`)

EURUSD 15m, OANDA data 2025-05-18 to 2026-09-17, cost 1 pip per round trip (spread + slippage), R per trade as the
indicator counts it. "One at a time" = the strategy's rule (no new signal while a position or order is open).

| Version | Trades | Win | Net R | PF | Max DD | 2025 / 2026 net R |
|---|---|---|---|---|---|---|
| Before 2026-10-11 (range from every grab, target past the range allowed) | 684 | 31.6% | -66.3 | 0.88 | 156 | +44.0 / -110.3 |
| Range from day / week liquidity (default now) | 520 | 34.2% | +23.7 | 1.06 | 106 | +73.9 / -50.2 |
| … and 5m stop hunt + MSS off (`iLtfMss` off) | 271 | 35.8% | +60.7 | 1.31 | 28.5 | +31.7 / +29.0 |
| … the same, one at a time | 191 | 35.1% | +36.4 | 1.26 | 21.7 | +21.6 / +14.8 |
| Range from day / week liquidity, no 5m at all, Strict mode | 69 | 42.0% | +32.4 | 1.72 | 9.1 | +19.1 / +13.2 |
