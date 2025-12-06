import requests
import pandas as pd
import io
from datetime import datetime

class AEMOClient:
    """
    Client for fetching public NEM data from AEMO.
    Targeting 'Price and Demand' aggregated files.
    """
    BASE_URL = "https://aemo.com.au/aemo/data/nem/priceanddemand"

    def fetch_price_and_demand(self, year: int, month: int, region: str) -> pd.DataFrame:
        """
        Fetches monthly CSV for a specific region.
        URL: PRICE_AND_DEMAND_{YYYY}{MM}_{REGION}.csv
        """
        # Format: 202401
        ym = f"{year}{month:02d}"
        filename = f"PRICE_AND_DEMAND_{ym}_{region}.csv"
        url = f"{self.BASE_URL}/{filename}"
        
        print(f"Downloading {url}...")
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            
            # Parse CSV
            # AEMO CSVs usually have headers like: REGION,SETTLEMENTDATE,TOTALDEMAND,RRP,PERIODTYPE
            df = pd.read_csv(io.StringIO(resp.text))
            return df
            
        except requests.exceptions.HTTPError as e:
            print(f"AEMO HTTP Error: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching AEMO data: {e}")
            return pd.DataFrame()

    def aggregate_daily(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates 30-min/5-min interval data to Daily summary.
        """
        if df.empty: return df
        
        # Normalize columns
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Parse Date (SETTLEMENTDATE)
        # Format usually '2024/01/01 00:30:00'
        df['DATETIME'] = pd.to_datetime(df['SETTLEMENTDATE'])
        df['DATE'] = df['DATETIME'].dt.date
        
        # Group by Date
        # Metrics: RRP (Price), TOTALDEMAND (MW)
        # We want: Avg Price, Min Price, Max Price, Avg Demand, Peak Demand
        
        # Weighted Average Price? (Volume Weighted)
        # VWAP = sum(Price * Demand) / sum(Demand)
        # Simple Average is often used for "Time Weighted Average", but VWAP is better for economics.
        # Let's calculate both or just simple average for MVP as requested.
        # User schema has price_average. Let's use simple average of RRP.
        
        daily = df.groupby('DATE').agg({
            'RRP': ['mean', 'min', 'max'],
            'TOTALDEMAND': ['mean', 'max']
        })
        
        # Flatten columns
        daily.columns = ['price_average', 'price_min', 'price_max', 'demand_mw_average', 'demand_mw_peak']
        daily = daily.reset_index()
        daily.rename(columns={'DATE': 'as_of'}, inplace=True)
        
        return daily
