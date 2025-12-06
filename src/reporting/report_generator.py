import pandas as pd
from datetime import date
from src.shared.db import get_db_connection

def generate_spx_commentary(score_row, feature_row):
    """
    Generates rule-based commentary for SPX.
    """
    instability = score_row.get('instability_index', 50)
    regime = score_row.get('regime', 'FRAGILE')
    net_gamma = feature_row.get('net_gamma', 0)
    gamma_slope = feature_row.get('gamma_slope', 0)
    
    # Regime Commentary
    intro = ""
    if regime == "EXPLOSIVE":
        intro = "SPX is in an EXPLOSIVE regime. Dealer positioning is fragile, and flows are likely to amplify volatility rather than dampen it."
    elif regime == "STABLE":
        intro = "SPX is in a STABLE regime. Dealer flows are supportive and likely to suppress volatility."
    else:
        intro = "SPX is in a FRAGILE regime. Market structure is mixed, creating a path-dependent environment."

    # Gamma Commentary
    gamma_note = ""
    if net_gamma < 0:
        gamma_note = "With Net Gamma deeply negative, dealers are forced to hedge in the direction of the trend (selling into drops, buying into rallies), creating asymmetric risk."
    elif net_gamma > 0:
        gamma_note = "Positive Net Gamma implies dealers are acting as mean-reversion agents, selling rips and buying dips."
        
    return f"{intro} {gamma_note}"

def generate_gold_commentary(score_row, feature_row):
    """
    Generates rule-based commentary for Gold.
    """
    instability = score_row.get('instability_index', 50)
    regime = score_row.get('regime', 'FRAGILE')
    back_pct = feature_row.get('backwardation_pct', 0)
    spec_net = feature_row.get('spec_net_position', 0)
    
    intro = f"Gold is in a {regime} regime (Score: {instability})."
    
    structure_note = ""
    if back_pct > 0:
        structure_note = "The futures curve is in backwardation, signalling physical tightness and immediate demand."
    else:
        structure_note = "The futures curve is in contango, indicating ample near-term supply."
        
    pos_note = ""
    if spec_net > 150000:
        pos_note = "Speculative positioning is stretched long, raising the risk of a washout if momentum stalls."
    else:
        pos_note = "Speculative positioning is moderate."
        
    return f"{intro} {structure_note} {pos_note}"

def generate_fx_commentary(score_row, feature_row):
    """
    Generates rule-based commentary for FX (AUDUSD).
    """
    instability = score_row.get('instability_index', 50)
    regime = score_row.get('regime', 'FRAGILE')
    pressure = score_row.get('pressure_direction', 'NEUTRAL')
    
    carry = float(feature_row.get('carry_attractiveness', 0))
    vol = float(feature_row.get('fx_vol_level', 0))
    
    # Safe access to pct_oi inside JSONB
    pct_oi = 0.0
    try:
        import json
        fv = feature_row.get('feature_vector')
        if fv:
            if isinstance(fv, str): fv = json.loads(fv)
            pct_oi = float(fv.get('cot_net_spec_pct_oi', 0))
    except:
        pass

    intro = f"AUDUSD is in a {regime} regime (Score: {instability:.1f})."
    
    detail = ""
    if regime == "STABLE":
        if carry > 0:
            detail = "Carry is supportive and volatility is contained."
        else:
            detail = "Despite negative carry headwinds, volatility remains contained and positioning is not extreme."
    elif regime == "FRAGILE":
        if pressure == "DOWN":
            detail = "Speculative positioning is stretched long against a backdrop that risks a washout."
        elif pressure == "UP":
            detail = "Positioning is short against positive carry, creating squeeze risk."
        else:
            detail = "Macro signals are mixed, suggesting chop."
    else:
        detail = "Elevated volatility and extreme positioning signal high instability."
        
    return f"{intro} {detail}"

def generate_report(as_of: date):
    """
    Generates the full markdown report for a given date.
    """
    print(f"Generating report for {as_of}...")
    
    with get_db_connection() as conn:
        # Fetch Scores
        scores_df = pd.read_sql("SELECT * FROM asset_scores WHERE as_of = %s", conn, params=(as_of,))
        # Fetch Features
        equity_df = pd.read_sql("SELECT * FROM features_equity WHERE as_of = %s", conn, params=(as_of,))
        comm_df = pd.read_sql("SELECT * FROM features_commodity WHERE as_of = %s", conn, params=(as_of,))
        fx_df = pd.read_sql("SELECT * FROM features_fx WHERE as_of = %s", conn, params=(as_of,))
        
    if scores_df.empty:
        print(f"No scores found for {as_of}")
        return None
        
    # Prepare Data
    spx_score = scores_df[scores_df['symbol'] == 'SPX'].iloc[0] if not scores_df[scores_df['symbol'] == 'SPX'].empty else {}
    gold_score = scores_df[scores_df['symbol'] == 'GOLD'].iloc[0] if not scores_df[scores_df['symbol'] == 'GOLD'].empty else {}
    aud_score = scores_df[scores_df['symbol'] == 'AUDUSD'].iloc[0] if not scores_df[scores_df['symbol'] == 'AUDUSD'].empty else {}
    
    spx_features = equity_df.iloc[0] if not equity_df.empty else {}
    gold_features = comm_df.iloc[0] if not comm_df.empty else {}
    fx_features = fx_df.iloc[0] if not fx_df.empty else {}
    
    # Generate Commentary
    spx_commentary = generate_spx_commentary(spx_score, spx_features)
    gold_commentary = generate_gold_commentary(gold_score, gold_features) if gold_score.get('symbol') else "Data pending."
    aud_commentary = generate_fx_commentary(aud_score, fx_features) if aud_score.get('symbol') else "Data pending."
    
    # Extract FX metrics for display
    aud_carry = float(fx_features.get('carry_attractiveness', 0))
    aud_vol = float(fx_features.get('fx_vol_level', 0))
    aud_net_spec = float(fx_features.get('cot_net_spec', 0))

    # Fill Template
    report_base = f"""# DealerFlow Weekly Macro Flow Report
**Date:** {as_of}

## 1. Global Flow Map (Summary)

| Asset | Instability | Regime | Pressure |
|-------|-------------|--------|----------|
| **SPX** | {spx_score.get('instability_index', 'N/A')} | **{spx_score.get('regime', 'N/A')}** | {spx_score.get('pressure_direction', 'N/A')} |
| **GOLD** | {gold_score.get('instability_index', 'N/A')} | **{gold_score.get('regime', 'N/A')}** | {gold_score.get('pressure_direction', 'N/A')} |
| **AUDUSD** | {aud_score.get('instability_index', 'N/A')} | **{aud_score.get('regime', 'N/A')}** | {aud_score.get('pressure_direction', 'N/A')} |

---

## 2. Equity Flow Snapshot (SPX)

**🧠 Structural Signals**
*   **Net Gamma:** {float(spx_features.get('net_gamma', 0)):.2f}
*   **Gamma Slope:** {float(spx_features.get('gamma_slope', 0)):.4f}
*   **Net Delta:** {float(spx_features.get('net_delta', 0)):.2f}

**📌 Interpretation**
{spx_commentary}

---

## 3. Commodity Flow Snapshot (GOLD)

**🧠 Structural Signals**
*   **Backwardation:** {float(gold_features.get('backwardation_pct', 0) * 100):.2f}%
*   **Spec Net Pos:** {float(gold_features.get('spec_net_position', 0)):,.0f} contracts

**📌 Interpretation**
{gold_commentary}

---

## 4. FX Flow Snapshot (AUDUSD)

**🧠 Structural Signals**
*   **Carry:** {aud_carry:.2f}% annualised
*   **Realised Vol (20d):** {aud_vol:.2f}%
*   **COT Net Spec:** {aud_net_spec:,.0f} contracts

**📌 Interpretation**
{aud_commentary}

---
"""

    # Try to load Macro Note (Deep Dive Narrative)
    import os
    macro_note_path = os.path.join(os.path.dirname(__file__), '..', '..', 'reports', f'macro_note_{as_of}.md')
    macro_content = ""
    
    if os.path.exists(macro_note_path):
        with open(macro_note_path, 'r', encoding='utf-8') as f:
            # Skip title/date from note as we already have header
            lines = f.readlines()
            # Simple heuristic: start from first ## header
            start_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("##"):
                    start_idx = i
                    break
            macro_content = "".join(lines[start_idx:])
            
        # Replace Section 5 with Macro Note
        report_base += f"\n{macro_content}\n"
    else:
        # Fallback
        report_base += """
## 5. Cross-Asset Themes
*   Equity instability suggests a cautious approach to risk assets.
*   FX and Commodity signals provide context on capital flows and scarcity.
"""

    report_base += """
---

## Disclaimer
This report is an automated structural-flow viewpoint generated by the DealerFlow engine.
It is not trading advice — purely a technical research signal.
"""
    
    return report_base

def save_report(report_content, as_of):
    filename = f"report_{as_of}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Report saved to {filename}")
