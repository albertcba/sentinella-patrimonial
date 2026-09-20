# import yfinance as yf
# t = yf.Ticker("META")
# print(t.options)

import yfinance as yf

t = yf.Ticker("META")
chain_dec = t.option_chain("2026-12-18")
print(chain_dec.calls.columns)
print(chain_dec.calls.head())
