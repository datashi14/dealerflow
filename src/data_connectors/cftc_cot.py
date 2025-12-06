import pandas as pd
import requests
import io
import zipfile
from datetime import date

class CFTCConnector:
    def __init__(self):
        # Financial Futures (AUD, etc.) - Traders in Financial Futures (TFF)
        # URL Pattern: https://www.cftc.gov/files/dea/history/...
        self.base_url = "https://www.cftc.gov/files/dea/history"
        
    def fetch_financial_cot(self, year: int = 2025) -> pd.DataFrame:
        """
        Fetches Traders in Financial Futures (TFF) data.
        Includes AUD, etc.
        """
        url = f"{self.base_url}/fin_fut_txt_{year}.zip"
        print(f"Downloading CFTC Financial COT from {url}...")
        
        return self._download_and_parse(url, "fin")

    def fetch_disagg_cot(self, year: int = 2025) -> pd.DataFrame:
        """
        Fetches Disaggregated Futures data (Commodities).
        Includes Gold, Oil, etc.
        """
        url = f"{self.base_url}/fut_disagg_txt_{year}.zip"
        print(f"Downloading CFTC Disaggregated COT from {url}...")
        
        return self._download_and_parse(url, "disagg")

    def _download_and_parse(self, url: str, report_type: str) -> pd.DataFrame:
        try:
            r = requests.get(url)
            r.raise_for_status()
            
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                # Usually contains a single .txt file
                filename = z.namelist()[0]
                with z.open(filename) as f:
                    # Parsing logic depends on format. 
                    # CFTC files are CSV-like but sometimes messy headers.
                    # We'll use standard pandas read_csv with loose settings.
                    df = pd.read_csv(f, low_memory=False)
                    
            # Basic normalization
            # Columns are huge and messy. We need to map them.
            # Standard Names:
            # 'Market_and_Exchange_Names' -> Underlying
            # 'Report_Date_as_MM_DD_YYYY' -> Date
            
            # Normalize columns to lower strip
            df.columns = [c.strip().lower() for c in df.columns]
            
            # Debug columns if key missing
            if 'report_date_as_mm_dd_yyyy' not in df.columns:
                print(f"Columns found: {df.columns.tolist()[:5]}...")
            
            # Date parsing
            # Try known formats
            if 'report_date_as_yyyy-mm-dd' in df.columns:
                 df['report_date_as_mm_dd_yyyy'] = pd.to_datetime(df['report_date_as_yyyy-mm-dd'])
            elif 'report_date_as_mm_dd_yyyy' in df.columns:
                 df['report_date_as_mm_dd_yyyy'] = pd.to_datetime(df['report_date_as_mm_dd_yyyy'])
            else:
                 print(f"Date column not found. Columns: {df.columns.tolist()[:5]}")
                 return pd.DataFrame()

            df['as_of'] = df['report_date_as_mm_dd_yyyy'].dt.date
            
            return df
            
        except Exception as e:
            print(f"Error fetching CFTC data: {e}")
            return pd.DataFrame()
            
    def filter_gold(self, df_disagg: pd.DataFrame) -> pd.DataFrame:
        """
        Filters for Gold (GC).
        Usually 'GOLD - COMMODITY EXCHANGE INC.'
        """
        mask = df_disagg['market_and_exchange_names'].str.contains("GOLD", case=False, na=False)
        return df_disagg[mask].copy()
        
    def filter_aud(self, df_fin: pd.DataFrame) -> pd.DataFrame:
        """
        Filters for Australian Dollar.
        Usually 'AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE'
        """
        mask = df_fin['market_and_exchange_names'].str.contains("AUSTRALIAN DOLLAR", case=False, na=False)
        return df_fin[mask].copy()
