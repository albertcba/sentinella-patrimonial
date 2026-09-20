import yfinance as yf
t = yf.Ticker("META")
print(t.options)
