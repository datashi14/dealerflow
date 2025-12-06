-- 1. Oil & Gas Futures (WTI, Brent, etc.)
CREATE TABLE IF NOT EXISTS raw_energy_oil_futures (
    id              BIGSERIAL PRIMARY KEY,
    as_of           DATE NOT NULL,
    symbol          TEXT NOT NULL,              -- 'WTI', 'BRENT'
    contract_month  DATE NOT NULL,              -- First day of contract month
    contract_code   TEXT NOT NULL,              -- e.g. 'CLM24'
    price_settle    NUMERIC(18,6) NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'USD',
    source          TEXT NOT NULL,              -- 'EIA', 'NASDAQ'
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (as_of, symbol, contract_month, source)
);

-- 2. Oil Inventories (Weekly)
CREATE TABLE IF NOT EXISTS raw_energy_oil_inventories (
    id              BIGSERIAL PRIMARY KEY,
    as_of           DATE NOT NULL,
    product         TEXT NOT NULL,                 -- 'CRUDE_TOTAL', 'GASOLINE_TOTAL', 'DISTILLATE_TOTAL'
    region          TEXT NOT NULL,                 -- 'US_TOTAL', 'CUSHING'
    stock_mmbbl     NUMERIC(18,3) NOT NULL,
    source          TEXT NOT NULL DEFAULT 'EIA',
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (as_of, product, region, source)
);

-- 3. Natural Gas Prices (Henry Hub)
CREATE TABLE IF NOT EXISTS raw_energy_gas_prices (
    id              BIGSERIAL PRIMARY KEY,
    as_of           DATE NOT NULL,
    hub             TEXT NOT NULL,                -- 'HENRY_HUB'
    price_spot      NUMERIC(18,6) NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'USD',
    unit            TEXT NOT NULL DEFAULT 'USD/MMBtu',
    source          TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (as_of, hub, source)
);

-- 4. Power Prices (NEM/WEM)
CREATE TABLE IF NOT EXISTS raw_energy_power_prices (
    id                      BIGSERIAL PRIMARY KEY,
    as_of                   DATE NOT NULL,
    region                  TEXT NOT NULL,         -- 'NSW1', 'VIC1', 'WA1'
    price_average           NUMERIC(18,6) NOT NULL,
    price_min               NUMERIC(18,6),
    price_max               NUMERIC(18,6),
    demand_mw_average       NUMERIC(18,3),
    demand_mw_peak          NUMERIC(18,3),
    currency                TEXT NOT NULL DEFAULT 'AUD',
    source                  TEXT NOT NULL DEFAULT 'AEMO',
    created_at              TIMESTAMPTZ DEFAULT now(),
    UNIQUE (as_of, region, source)
);

-- 5. Power Mix (Renewables/Fuel)
CREATE TABLE IF NOT EXISTS raw_energy_power_mix (
    id                  BIGSERIAL PRIMARY KEY,
    as_of               DATE NOT NULL,
    region              TEXT NOT NULL,
    fuel_type           TEXT NOT NULL,     -- 'COAL', 'GAS', 'WIND', 'SOLAR'
    generation_mwh      NUMERIC(18,3) NOT NULL,
    share_pct           NUMERIC(9,4),
    source              TEXT NOT NULL DEFAULT 'AEMO',
    created_at          TIMESTAMPTZ DEFAULT now(),
    UNIQUE (as_of, region, fuel_type, source)
);

-- 6. Weather (HDD/CDD)
CREATE TABLE IF NOT EXISTS raw_energy_weather_daily (
    id              BIGSERIAL PRIMARY KEY,
    as_of           DATE NOT NULL,
    location_code   TEXT NOT NULL,           -- 'NSW_SYD'
    tmin_c          NUMERIC(6,2),
    tmax_c          NUMERIC(6,2),
    tmean_c         NUMERIC(6,2),
    hdd_18c         NUMERIC(6,2),
    cdd_18c         NUMERIC(6,2),
    source          TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (as_of, location_code, source)
);

-- 7. Carbon Prices
CREATE TABLE IF NOT EXISTS raw_energy_carbon_prices (
    id              BIGSERIAL PRIMARY KEY,
    as_of           DATE NOT NULL,
    scheme          TEXT NOT NULL,           -- 'EU_ETS', 'ACCU'
    price_per_tco2  NUMERIC(18,6) NOT NULL,
    currency        TEXT NOT NULL,
    source          TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (as_of, scheme, source)
);
