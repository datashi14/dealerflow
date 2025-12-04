import argparse
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scoring.scoring_engine import compute_asset_scores

def main():
    parser = argparse.ArgumentParser(description="Compute Instability Index and Regimes.")
    parser.add_argument("--date", type=str, required=True, help="Date to score (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    try:
        as_of = datetime.strptime(args.date, "%Y-%m-%d").date()
        compute_asset_scores(as_of)
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
    except Exception as e:
        print(f"Error scoring assets: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
