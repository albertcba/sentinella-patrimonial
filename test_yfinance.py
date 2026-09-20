# import yfinance as yf
# t = yf.Ticker("META")
# print(t.options)

# # # # # # # # # # # # # # # # 

# import yfinance as yf

# t = yf.Ticker("META")
# chain_dec = t.option_chain("2026-12-18")
# print(chain_dec.calls.columns)
# print(chain_dec.calls.head())

# # # # # # # # # # # # # # # # 

import yfinance as yf

t = yf.Ticker("META")

dec = t.option_chain("2026-12-18")
jan = t.option_chain("2027-01-15")

call_dec = dec.calls[
    dec.calls["strike"] == 680
]

call_jan = jan.calls[
    jan.calls["strike"] == 680
]

print("\nDEC")
print(
    call_dec[
        [
            "strike",
            "bid",
            "ask",
            "impliedVolatility",
            "openInterest"
        ]
    ]
)

print("\nJAN")
print(
    call_jan[
        [
            "strike",
            "bid",
            "ask",
            "impliedVolatility",
            "openInterest"
        ]
    ]
)

