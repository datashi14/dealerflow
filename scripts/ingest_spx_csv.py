import argparse
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion.ingest_spx_csv import ingest_spx_from_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest SPX options from a CSV file into raw_options."
    )
    parser.add_argument(
        "csv_path",
        type=str,
        help="Path to the SPX options CSV file",
    )
    parser.add_argument(
        "--as-of",
        type=str,
        default=None,
        help="As-of date in YYYY-MM-DD format (default: today)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not os.path.exists(args.csv_path):
        raise FileNotFoundError(f"CSV file not found: {args.csv_path}")

    as_of = None
    if args.as_of:
        as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date()

    inserted = ingest_spx_from_csv(args.csv_path, as_of=as_of)
    print(f"Inserted {inserted} SPX option rows into raw_options.")


if __name__ == "__main__":
    main()
