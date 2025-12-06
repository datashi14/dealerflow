import os
import requests
import pandas as pd
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

class AlphaVantageConnector:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_KEY")
        self.base_url = "https://www.alphavantage.co/query"
        
        if not self.api_key:
            print("WARNING: No Alpha Vantage API Key provided. Set ALPHA_VANTAGE_KEY env var.")

    def _fetch(self, function: str, symbol: str = None, from_symbol: str = None, to_symbol: str = None, outputsize: str = "compact"):
        params = {
            "function": function,
            "apikey": self.api_key,
            "datatype": "json",
            "outputsize": outputsize
        }
        if symbol: params["symbol"] = symbol
        if from_symbol: params["from_symbol"] = from_symbol
        if to_symbol: params["to_symbol"] = to_symbol
        
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage Error: {data['Error Message']}")
        if "Note" in data:
            # Rate limit warning
            print(f"Alpha Vantage Note: {data['Note']}")
            
        return data

    def get_fx_daily(self, from_symbol: str = "AUD", to_symbol: str = "USD") -> pd.DataFrame:
        """
        Fetches daily FX rates. Returns DataFrame with ['date', 'pair', 'close'].
        """
        print(f"Fetching FX daily for {from_symbol}/{to_symbol}...")
        data = self._fetch("FX_DAILY", from_symbol=from_symbol, to_symbol=to_symbol, outputsize="full")
        
        ts_key = "Time Series FX (Daily)"
        if ts_key not in data:
            print("No data found in response.")
            return pd.DataFrame()
            
        rows = []
        for date_str, metrics in data[ts_key].items():
            rows.append({
                "as_of": date_str, # Will parse later
                "pair": f"{from_symbol}{to_symbol}",
                "spot_price": float(metrics["4. close"]),
                # Rate diffs not provided by FX_DAILY, usually need separate macro series
                "short_rate_base": 0.0, # Stub
                "short_rate_quote": 0.0, # Stub
                "implied_vol_1m": 0.0 # Stub
            })
            
        df = pd.DataFrame(rows)
        df['as_of'] = pd.to_datetime(df['as_of']).dt.date
        return df

    def get_commodity_daily(self, symbol: str = "GOLD") -> pd.DataFrame:
        """
        Fetches commodity prices via GLD ETF proxy (TIME_SERIES_DAILY).
        """
        print(f"Fetching commodity spot for {symbol} (via GLD ETF)...")
        # Use GLD ETF
        data = self._fetch("TIME_SERIES_DAILY", symbol="GLD", outputsize="full")
        
        ts_key = "Time Series (Daily)"
        if ts_key not in data:
            print(f"No data found for {symbol}. Response keys: {list(data.keys())}")
            if "Note" in data: print(f"Note: {data['Note']}")
            return pd.DataFrame()
            
        rows = []
        for date_str, metrics in data[ts_key].items():
            rows.append({
                "as_of": date_str,
                "pair": "XAUUSD", # Keeping internal pair name consistent
                "spot_price": float(metrics["4. close"]),
                "short_rate_base": 0.0,
                "short_rate_quote": 0.0,
                "implied_vol_1m": 0.0
            })
            
        df = pd.DataFrame(rows)
        df['as_of'] = pd.to_datetime(df['as_of']).dt.date
        return df

    def get_treasury_yield(self, interval: str = "daily", maturity: str = "3month") -> pd.DataFrame:
        """
        Fetches treasury yields (for USD Rate).
        function=TREASURY_YIELD
        """
        print(f"Fetching Treasury Yield ({maturity})...")
        data = self._fetch("TREASURY_YIELD", interval=interval, maturity=maturity)
        # Parsing logic would go here
        # For MVP, we might skip strict macro rates unless vital
        return pd.DataFrame()
