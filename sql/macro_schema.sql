-- 1. Sovereign Yields (US/JP)
CREATE TABLE IF NOT EXISTS raw_rates_yields (
    id          BIGSERIAL PRIMARY KEY,
    as_of       DATE NOT NULL,
    country     TEXT NOT NULL,        -- 'US', 'JP'
    tenor_yrs   NUMERIC(4,1) NOT NULL, -- 2.0, 10.0, 30.0
    yield_pct   NUMERIC(8,4) NOT NULL,
    source      TEXT NOT NULL,        -- 'FRED', 'BOJ'
    created_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE (as_of, country, tenor_yrs, source)
);

-- 2. JPY FX Features
CREATE TABLE IF NOT EXISTS features_fx_jpy (
    as_of                   DATE PRIMARY KEY,
    usd_jpy_close           NUMERIC(18,6),
    usd_jpy_ret_20d         NUMERIC(18,6),
    usd_jpy_realised_vol_20d NUMERIC(18,6),
    dxy_ret_20d             NUMERIC(18,6),
    fx_vol_regime           TEXT,              -- 'CALM', 'ELEVATED', 'CRISIS'
    created_at              TIMESTAMPTZ DEFAULT now()
);

-- 3. Rates Spreads Features
CREATE TABLE IF NOT EXISTS features_rates_spreads (
    as_of               DATE PRIMARY KEY,
    us10y               NUMERIC(8,4),
    jp10y               NUMERIC(8,4),
    us2y                NUMERIC(8,4),
    jp2y                NUMERIC(8,4),
    spread_usjp_10y     NUMERIC(8,4),  -- US10Y - JP10Y
    spread_usjp_2y      NUMERIC(8,4),
    jgb_2s10s           NUMERIC(8,4),
    ust_2s10s           NUMERIC(8,4),
    policy_error_risk   TEXT,          -- 'LOW', 'RISING', 'HIGH'
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- 4. Japan Reflexivity Signals
CREATE TABLE IF NOT EXISTS features_reflexivity_jp (
    as_of                       DATE PRIMARY KEY,
    yen_weakening_with_infl     BOOLEAN,
    jgb_yields_rising           BOOLEAN,
    reflexive_loop_active       BOOLEAN,
    comment                     TEXT,
    created_at                  TIMESTAMPTZ DEFAULT now()
);

-- 5. Cross-Border Flow Proxies
CREATE TABLE IF NOT EXISTS features_crossborder_fx_equity (
    as_of                DATE PRIMARY KEY,
    spx_ret_20d          NUMERIC(8,4),
    dxy_ret_20d          NUMERIC(8,4),
    corr_spx_dxy_60d     NUMERIC(8,4),
    fx_equity_stress     TEXT,         -- 'NORMAL', 'WARNING', 'ALERT'
    created_at           TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS features_crossborder_equity_fxhedge (
    as_of                       DATE PRIMARY KEY,
    spx_local_ret_60d           NUMERIC(8,4),
    spx_usdhedged_ret_60d       NUMERIC(8,4),
    fx_drag_bps_annualised      NUMERIC(8,4),
    fx_drag_regime              TEXT,          -- 'TAILWIND', 'NEUTRAL', 'HEADWIND'
    created_at                  TIMESTAMPTZ DEFAULT now()
);

-- 6. Equity Concentration (Shell)
CREATE TABLE IF NOT EXISTS features_equity_concentration (
    as_of               DATE PRIMARY KEY,
    top7_weight_share   NUMERIC(5,2),
    ai_theme_perf_60d   NUMERIC(8,4),
    concentration_risk  TEXT,          -- 'LOW', 'ELEVATED', 'EXTREME'
    created_at          TIMESTAMPTZ DEFAULT now()
);
