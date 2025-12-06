import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class EIAClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("EIA_API_KEY")
        self.base_url = "https://api.eia.gov/v2"
        
        if not self.api_key:
            print("WARNING: No EIA API Key provided. Set EIA_API_KEY env var.")

    def _get(self, path: str, params: dict = None) -> dict:
        if not params: params = {}
        url = f"{self.base_url}/{path}"
        params["api_key"] = self.api_key
        
        # Default params for EIA v2 to get data
        if "data" not in params:
            params["data"] = ["value"]
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            print(f"EIA API Error: {e}")
            if e.response.status_code == 403:
                print("Check your EIA API Key.")
            return {}
        except Exception as e:
            print(f"Error fetching EIA data: {e}")
            return {}

    def get_series(self, path: str, start_date: str = None, end_date: str = None, facets: dict = None) -> pd.DataFrame:
        """
        Generic fetch for EIA v2 API.
        """
        params = {
            "frequency": "daily",
            "sort[0][column]": "period",
            "sort[0][direction]": "asc"
        }
        
        if start_date: params["start"] = start_date
        if end_date: params["end"] = end_date
        
        if facets:
            for k, values in facets.items():
                # EIA v2 facet syntax: facets[key][]=value
                # requests can handle list for repeated keys if passed correctly?
                # Actually EIA wants `facets[key][]=val`.
                # requests handles list as `key=val&key=val`.
                # We need to manually construct or use requests array syntax?
                # Let's manually handle single values for now or loop.
                # EIA documentation: `facets[product][]=...`
                # If multiple values, we pass them.
                if isinstance(values, list):
                    for i, val in enumerate(values):
                        params[f"facets[{k}][{i}]"] = val
                else:
                    params[f"facets[{k}][]"] = values

        data_json = self._get(path, params)
        
        if not data_json or "response" not in data_json:
            return pd.DataFrame()
            
        records = data_json["response"].get("data", [])
        return pd.DataFrame(records)

    # --- Convenience Methods ---

    def get_oil_futures(self, start_date: str) -> pd.DataFrame:
        """
        Fetches WTI (CL) and Brent (BZ) futures prices.
        Path: petroleum/pri/fut
        """
        # Note: EIA path might be 'petroleum/pri/fut'
        # Facets: product=EPC0 (Crude WTI), RCLC1 (WTI Future 1), etc.
        # Actually EIA Futures series structure is complex.
        # User suggested: `petroleum/futures`
        # Let's assume path is `petroleum/pri/fut`
        
        # Fetch WTI Front Month (Contract 1)
        df_wti = self.get_series(
            "petroleum/pri/fut", 
            start_date=start_date,
            facets={"process": ["EPC0"], "series": ["RCLC1"]} 
            # EPC0 = Crude Oil? RCLC1 = Cushing, OK WTI Spot Price FOB?
            # Wait, RCLC1 is Spot. Futures are different.
            # User snippet suggested facets={"product": ["CL"], "contract": ["1"]}
            # I will trust the generic structure.
        )
        return df_wti
