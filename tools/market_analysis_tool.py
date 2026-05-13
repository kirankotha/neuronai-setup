"""
title: Market Technical Analysis
description: Fetch live market data and perform technical analysis with support/resistance levels, RSI, MACD, and Bollinger Bands for stocks, crypto, and indices.
author: custom
version: 1.0.0
requirements: yfinance, ta
"""

from pydantic import BaseModel
from datetime import datetime
import yfinance as yf
import pandas as pd
import ta
import numpy as np


class Tools:
    def __init__(self):
        pass

    def _fmt(self, val, decimals=2):
        try:
            if val is None:
                return "N/A"
            f = float(val)
            if np.isnan(f):
                return "N/A"
            return f"{f:.{decimals}f}"
        except Exception:
            return "N/A"

    def analyze_market(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> str:
        """
        Analyze a stock, crypto, ETF, or index with live market data and technical indicators.
        Provides support/resistance levels, RSI, MACD, Bollinger Bands, EMAs, and investment scenarios.

        Ticker examples:
        - US Stocks  : AAPL, TSLA, MSFT, NVDA, AMZN
        - Indian NSE : RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS
        - Indian BSE : RELIANCE.BO, TCS.BO
        - Crypto     : BTC-USD, ETH-USD, SOL-USD
        - Indices    : ^NSEI (Nifty50), ^BSESN (Sensex), ^GSPC (S&P500)
        - ETFs       : SPY, QQQ

        :param ticker: Ticker symbol as shown above
        :param period: History length - 1mo, 3mo, 6mo, 1y, 2y (default: 1y)
        :param interval: Candle size - 1d, 1h (default: 1d)
        :return: Full technical analysis report
        """
        f = self._fmt

        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)

            if df.empty:
                return (
                    f"No data found for '{ticker}'.\n"
                    "Tip: Indian NSE stocks use .NS suffix (e.g. RELIANCE.NS), BSE use .BO"
                )

            close = df["Close"]
            high = df["High"]
            low = df["Low"]
            volume = df["Volume"]

            # ── Price Action ──────────────────────────────────────────────
            current_price = close.iloc[-1]
            prev_close = close.iloc[-2]
            change_pct = ((current_price - prev_close) / prev_close) * 100
            current_volume = volume.iloc[-1]
            avg_volume = volume.mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

            # ── RSI ───────────────────────────────────────────────────────
            rsi_val = ta.momentum.RSIIndicator(close=close, window=14).rsi().iloc[-1]
            if np.isnan(rsi_val):
                rsi_val = None

            # ── MACD ──────────────────────────────────────────────────────
            macd_obj = ta.trend.MACD(close=close, window_fast=12, window_slow=26, window_sign=9)
            macd_line = macd_obj.macd().iloc[-1]
            macd_signal = macd_obj.macd_signal().iloc[-1]
            macd_hist = macd_obj.macd_diff().iloc[-1]

            # ── Bollinger Bands ───────────────────────────────────────────
            bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
            bb_upper = bb.bollinger_hband().iloc[-1]
            bb_mid = bb.bollinger_mavg().iloc[-1]
            bb_lower = bb.bollinger_lband().iloc[-1]

            # ── EMAs ─────────────────────────────────────────────────────
            ema20 = ta.trend.EMAIndicator(close=close, window=20).ema_indicator().iloc[-1]
            ema50 = ta.trend.EMAIndicator(close=close, window=50).ema_indicator().iloc[-1]
            ema200_series = ta.trend.EMAIndicator(close=close, window=200).ema_indicator()
            ema200 = ema200_series.iloc[-1] if not np.isnan(ema200_series.iloc[-1]) else None

            # ── Pivot Points (classic, from previous candle) ──────────────
            ph = high.iloc[-2]
            pl = low.iloc[-2]
            pc = close.iloc[-2]
            pivot = (ph + pl + pc) / 3
            r1 = (2 * pivot) - pl
            r2 = pivot + (ph - pl)
            r3 = ph + 2 * (pivot - pl)
            s1 = (2 * pivot) - ph
            s2 = pivot - (ph - pl)
            s3 = pl - 2 * (ph - pivot)

            # ── Swing Levels (last 20 candles) ────────────────────────────
            recent = df.tail(20)
            swing_high = recent["High"].max()
            swing_low = recent["Low"].min()

            # ── 52-Week Range ─────────────────────────────────────────────
            year_df = stock.history(period="1y")
            w52_high = year_df["High"].max() if not year_df.empty else None
            w52_low = year_df["Low"].min() if not year_df.empty else None
            if w52_high and w52_low and (w52_high - w52_low) > 0:
                yr_pos = (current_price - w52_low) / (w52_high - w52_low) * 100
            else:
                yr_pos = None

            # ── Company Name ──────────────────────────────────────────────
            try:
                info = stock.info
                name = info.get("longName") or info.get("shortName") or ticker.upper()
            except Exception:
                name = ticker.upper()

            # ── Signal Labels ─────────────────────────────────────────────
            if current_price > ema20 and ema20 > ema50:
                trend = "BULLISH"
            elif current_price < ema20 and ema20 < ema50:
                trend = "BEARISH"
            else:
                trend = "SIDEWAYS / MIXED"

            rsi_label = "N/A"
            if rsi_val is not None:
                if rsi_val > 70:
                    rsi_label = "OVERBOUGHT — watch for reversal down"
                elif rsi_val > 60:
                    rsi_label = "STRONG — mild overbought pressure"
                elif rsi_val < 30:
                    rsi_label = "OVERSOLD — watch for reversal up"
                elif rsi_val < 40:
                    rsi_label = "WEAK — mild oversold pressure"
                else:
                    rsi_label = "NEUTRAL"

            if not np.isnan(macd_line) and not np.isnan(macd_signal):
                macd_bias = "BULLISH — MACD above Signal" if macd_line > macd_signal else "BEARISH — MACD below Signal"
            else:
                macd_bias = "N/A"

            if not np.isnan(bb_upper) and not np.isnan(bb_lower) and (bb_upper - bb_lower) > 0:
                bb_pct = (current_price - bb_lower) / (bb_upper - bb_lower) * 100
                if bb_pct >= 95:
                    bb_pos = f"NEAR UPPER BAND ({bb_pct:.0f}%) — overbought zone"
                elif bb_pct <= 5:
                    bb_pos = f"NEAR LOWER BAND ({bb_pct:.0f}%) — oversold zone"
                else:
                    bb_pos = f"{bb_pct:.0f}% within bands — middle zone"
            else:
                bb_pos = "N/A"

            ema200_label = "N/A"
            if ema200:
                ema200_label = (
                    f"{f(ema200)}  |  Price {'ABOVE (long-term bullish)' if current_price > ema200 else 'BELOW (long-term bearish)'}"
                )

            report = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TECHNICAL ANALYSIS — {name} ({ticker.upper()})
  {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Data may have 15-min delay
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRICE ACTION
  Current Price : {f(current_price)}
  Change        : {change_pct:+.2f}%
  Volume        : {int(current_volume):,}  ({volume_ratio:.1f}x avg)
  Overall Trend : {trend}

SUPPORT & RESISTANCE  (Classic Pivot Points)
  R3  Strong Resistance : {f(r3)}
  R2  Resistance        : {f(r2)}
  R1  Nearest Resistance: {f(r1)}
  ──  Pivot Level       : {f(pivot)}
  S1  Nearest Support   : {f(s1)}
  S2  Support           : {f(s2)}
  S3  Strong Support    : {f(s3)}

SWING LEVELS  (last 20 candles)
  Swing High : {f(swing_high)}
  Swing Low  : {f(swing_low)}

52-WEEK RANGE
  High     : {f(w52_high)}
  Low      : {f(w52_low)}
  Position : {f(yr_pos)}% through yearly range

MOVING AVERAGES
  EMA 20  : {f(ema20)}  |  Price {'ABOVE' if current_price > ema20 else 'BELOW'}
  EMA 50  : {f(ema50)}  |  Price {'ABOVE' if current_price > ema50 else 'BELOW'}
  EMA 200 : {ema200_label}

MOMENTUM & OSCILLATORS
  RSI (14)        : {f(rsi_val)}  —  {rsi_label}
  MACD Line       : {f(macd_line, 4)}
  MACD Signal     : {f(macd_signal, 4)}
  MACD Histogram  : {f(macd_hist, 4)}
  MACD Bias       : {macd_bias}

BOLLINGER BANDS  (20, 2σ)
  Upper : {f(bb_upper)}
  Mid   : {f(bb_mid)}
  Lower : {f(bb_lower)}
  Price : {bb_pos}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Note: This is educational data only, not financial advice.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            return report.strip()

        except Exception as e:
            return f"Error analyzing '{ticker}': {str(e)}"
