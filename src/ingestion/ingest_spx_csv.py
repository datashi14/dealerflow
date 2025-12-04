import os
from datetime import date
from typing import Optional

import pandas as pd

from src.shared.db import get_db_connection


REQUIRED_COLUMNS = {
    "option_symbol",
    "type",
    "strike",
    "expiry",
    "underlying_price",
    "bid",
    "ask",
    "last",
    "open_interest",
    "implied_volatility",
    "delta",
    "gamma",
}


def _validate_columns(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {sorted(missing)}")


def ingest_spx_from_csv(
    csv_path: str,
    as_of: Optional[date] = None,
    underlying: str = "SPX",
) -> int:
    """Ingest SPX options from a CSV file into raw_options.

    The CSV must contain at least the columns in REQUIRED_COLUMNS.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file.
    as_of : date, optional
        Trade date to store in `as_of`. Defaults to today.
    underlying : str
        Underlying symbol label to store (default: "SPX").

    Returns
    -------
    int
        Number of rows inserted.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    as_of = as_of or date.today()

    df = pd.read_csv(csv_path)
    _validate_columns(df)

    # Ensure expiry is a proper date
    if df["expiry"].dtype == object:
        df["expiry"] = pd.to_datetime(df["expiry"]).dt.date

    records = [
        (
            as_of,
            underlying,
            row["option_symbol"],
            row["type"],
            float(row["strike"]),
            row["expiry"],
            float(row["underlying_price"]),
            float(row["bid"]),
            float(row["ask"]),
            float(row["last"]),
            float(row["open_interest"]),
            float(row["implied_volatility"]),
            float(row["delta"]),
            float(row["gamma"]),
        )
        for _, row in df.iterrows()
    ]

    sql = """
        INSERT INTO raw_options (
            as_of,
            underlying,
            option_symbol,
            type,
            strike,
            expiry,
            underlying_price,
            bid,
            ask,
            last,
            open_interest,
            implied_volatility,
            delta,
            gamma
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, records)
        conn.commit()

    return len(records)
