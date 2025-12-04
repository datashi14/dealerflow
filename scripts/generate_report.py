import argparse
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.reporting.report_generator import generate_report, save_report

def main():
    parser = argparse.ArgumentParser(description="Generate DealerFlow Report.")
    parser.add_argument("--date", type=str, required=True, help="Date of report (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    try:
        as_of = datetime.strptime(args.date, "%Y-%m-%d").date()
        report = generate_report(as_of)
        if report:
            save_report(report, as_of)
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
