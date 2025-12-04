import argparse
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.commodity_features import compute_commodity_features

def main():
    parser = argparse.ArgumentParser(description="Compute Commodity features.")
    parser.add_argument("--date", type=str, required=True, help="Date (YYYY-MM-DD)")
    parser.add_argument("--symbol", type=str, default="GOLD", help="Underlying symbol")
    
    args = parser.parse_args()
    
    try:
        as_of = datetime.strptime(args.date, "%Y-%m-%d").date()
        compute_commodity_features(as_of, args.symbol)
    except ValueError:
        print("Invalid date format.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
