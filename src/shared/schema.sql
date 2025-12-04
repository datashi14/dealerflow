-- 1. Raw Data Tables

CREATE TABLE IF NOT EXISTS raw_options (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    underlying VARCHAR(20) NOT NULL, -- e.g., 'SPX'
    option_symbol VARCHAR(50) NOT NULL,
    type VARCHAR(4) NOT NULL, -- 'call' or 'put'
    strike NUMERIC NOT NULL,
    expiry DATE NOT NULL,
    underlying_price NUMERIC,
    bid NUMERIC,
    ask NUMERIC,
    last NUMERIC,
    open_interest NUMERIC,
    implied_volatility NUMERIC,
    delta NUMERIC,
    gamma NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_options_as_of_underlying ON raw_options(as_of, underlying);


CREATE TABLE IF NOT EXISTS raw_futures (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    underlying VARCHAR(20) NOT NULL, -- e.g., 'GOLD'
    contract_symbol VARCHAR(50) NOT NULL,
    expiry DATE,
    settle_price NUMERIC,
    open_interest NUMERIC,
    volume NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_futures_as_of_underlying ON raw_futures(as_of, underlying);


CREATE TABLE IF NOT EXISTS raw_cot (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    market VARCHAR(50) NOT NULL, -- e.g., 'GOLD', 'AUD'
    hedger_long NUMERIC,
    hedger_short NUMERIC,
    spec_long NUMERIC,
    spec_short NUMERIC,
    small_long NUMERIC,
    small_short NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_cot_as_of_market ON raw_cot(as_of, market);


CREATE TABLE IF NOT EXISTS raw_fx (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    pair VARCHAR(10) NOT NULL, -- e.g., 'AUDUSD'
    spot_price NUMERIC,
    short_rate_base NUMERIC, -- e.g. AUD rate
    short_rate_quote NUMERIC, -- e.g. USD rate
    implied_vol_1m NUMERIC,
    implied_vol_3m NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_fx_as_of_pair ON raw_fx(as_of, pair);


CREATE TABLE IF NOT EXISTS raw_macro_rates (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    fed_rate NUMERIC,
    rba_rate NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_credit (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    hy_ig_spread_proxy NUMERIC,
    curve_slope_2s10s NUMERIC,
    funding_spread_proxy NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 2. Feature Tables

CREATE TABLE IF NOT EXISTS features_equity (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    underlying VARCHAR(20) NOT NULL,
    net_gamma NUMERIC,
    gamma_below_spot NUMERIC,
    gamma_above_spot NUMERIC,
    gamma_near_expiry NUMERIC,
    near_term_gamma_ratio NUMERIC,
    gamma_slope NUMERIC,
    put_call_oi_ratio NUMERIC,
    net_delta NUMERIC,
    gamma_flip_level NUMERIC,
    feature_vector JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_features_equity_unique ON features_equity(as_of, underlying);


CREATE TABLE IF NOT EXISTS features_commodity (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    underlying VARCHAR(20) NOT NULL,
    hedger_net_position NUMERIC,
    spec_net_position NUMERIC,
    backwardation_pct NUMERIC,
    roll_yield NUMERIC,
    oi_change NUMERIC,
    vol_term_structure NUMERIC,
    feature_vector JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_features_commodity_unique ON features_commodity(as_of, underlying);


CREATE TABLE IF NOT EXISTS features_fx (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    pair VARCHAR(10) NOT NULL,
    cot_net_position NUMERIC,
    rate_diff NUMERIC, -- RBA - Fed
    carry_attractiveness NUMERIC,
    fx_vol_level NUMERIC,
    fx_vol_slope NUMERIC,
    feature_vector JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_features_fx_unique ON features_fx(as_of, pair);


CREATE TABLE IF NOT EXISTS features_credit (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    hy_ig_spread NUMERIC,
    spread_trend_1m NUMERIC,
    funding_proxy NUMERIC,
    curve_slope_2s10s NUMERIC,
    curve_inversion_days INTEGER,
    credit_risk_score NUMERIC, -- 0-1
    credit_regime VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_features_credit_unique ON features_credit(as_of);


CREATE TABLE IF NOT EXISTS features_rates (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    fed_rate NUMERIC,
    rba_rate NUMERIC,
    rate_diff NUMERIC,
    rate_diff_3m_change NUMERIC,
    liquidity_score NUMERIC, -- 0-1
    rate_regime VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_features_rates_unique ON features_rates(as_of);


-- 3. Unified Scores Table

CREATE TABLE IF NOT EXISTS asset_scores (
    id SERIAL PRIMARY KEY,
    as_of DATE NOT NULL,
    asset_type VARCHAR(20) NOT NULL, -- 'EQUITY', 'COMMODITY', 'FX'
    symbol VARCHAR(20) NOT NULL,
    instability_index NUMERIC, -- 0-100
    regime VARCHAR(20), -- 'STABLE', 'FRAGILE', 'EXPLOSIVE'
    pressure_direction VARCHAR(20), -- 'UP', 'DOWN', 'NEUTRAL'
    flow_risk NUMERIC, -- 0-1
    vol_risk NUMERIC, -- 0-1
    narrative_risk NUMERIC, -- 0-1
    contagion_risk NUMERIC, -- 0-1
    credit_risk NUMERIC, -- 0-1
    global_flow_score NUMERIC, -- 0-100
    meta JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_asset_scores_unique ON asset_scores(as_of, symbol);
