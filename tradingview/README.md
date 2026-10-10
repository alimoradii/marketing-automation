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
