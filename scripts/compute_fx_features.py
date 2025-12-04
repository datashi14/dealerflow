import argparse
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.fx_features import compute_fx_features

def main():
    parser = argparse.ArgumentParser(description="Compute FX features.")
    parser.add_argument("--date", type=str, required=True, help="Date (YYYY-MM-DD)")
    parser.add_argument("--pair", type=str, default="AUDUSD", help="FX Pair")
    
    args = parser.parse_args()
    
    try:
        as_of = datetime.strptime(args.date, "%Y-%m-%d").date()
        compute_fx_features(as_of, args.pair)
    except ValueError:
        print("Invalid date format.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
