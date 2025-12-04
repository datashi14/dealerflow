import argparse
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.spx_features import compute_spx_features

def main():
    parser = argparse.ArgumentParser(description="Compute SPX features from raw_options.")
    parser.add_argument("--date", type=str, required=True, help="Date to compute features for (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    try:
        as_of = datetime.strptime(args.date, "%Y-%m-%d").date()
        compute_spx_features(as_of)
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
    except Exception as e:
        print(f"Error computing features: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
