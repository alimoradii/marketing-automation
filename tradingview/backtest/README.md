# Backtest of MZ_SDP.pine (Python port)

A line-by-line Python port of the indicator's trading logic (signals, fills, partial / target / stop, cancel and
expiry, news close), drawing left out. It reproduces the indicator's own trade accounting (R per trade) and adds
costs and a one-trade-at-a-time view (like the strategy version).

Data (not in the repo): OANDA EURUSD 5-minute candles from
https://huggingface.co/datasets/jukik45/mt5_eurusd -> put `EURUSD_MT5_OANDA_MASTER_M5_2025-05-17_to_2026-09-18.csv`
into `tradingview/backtest/data/` (or set MZ_DATA). 15m, 4h (from 17:00 NY) and daily candles are built from it.

    python3 sim.py                       # defaults of the indicator
    python3 sim.py iLtfMss=False         # any input by its Pine name
    python3 batch.py NAME base k=v ...   # results/NAME.json (full period and 2025 / 2026 halves)
    python3 table.py                     # comparison table

Not simulated: SMT (no GBPUSD data; it only changes the grade), CPI / NFP news (only the built-in FOMC days).
Prices differ slightly from FOREXCOM; TradingView's Strategy Tester stays the reference.
Port conventions: PORTING.md. After changing MZ_SDP.pine, port the change into the matching sec*.py.
