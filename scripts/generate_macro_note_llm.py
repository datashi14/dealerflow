import argparse
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.llm.macro_state import build_macro_state

def call_llm_mock(system_prompt, user_prompt):
    """
    Mock LLM call for portfolio demo without API key.
    """
    return f"""
# Macro Note: The Reflexive Edge

**Date:** {datetime.now().strftime('%Y-%m-%d')}

## 1. Structural Flow
The DealerFlow engine flags SPX as **FRAGILE** (Score 48). Dealers are in negative gamma territory, meaning they are forced to sell into weakness and buy into strength. This mechanical hedging flow amplifies volatility but hasn't yet reached "Explosive" extremes. Meanwhile, cross-border flows show signs of stress, with the Dollar strengthening alongside falling equity markets.

## 2. Reflexivity
A classic reflexive loop is forming in Japan. Rising JGB yields are failing to attract capital because the Yen is simultaneously weakening. This suggests the carry trade unwind is not over; instead, capital is fleeing Japan despite higher nominal rates, which forces the BOJ into a corner.

## 3. The Truth
Consensus believes the "Soft Landing" is locked in. The truth is that structural liquidity conditions are deteriorating. The equity market is supporting the economy, not the other way around. If SPX breaks key dealer levels, the feedback loop reverses.

## 4. Signals to Watch
*   **USDJPY**: If it breaks 152 despite rising JGB yields, the reflexive loop accelerates.
*   **SPX Net Gamma**: Currently negative. Watch for a flip back to positive to signal stability.

## 5. How DealerFlow Tracks This
Our composite instability index captures the interaction between Option Gamma, FX Carry, and Rates Spreads. Today, 3 out of 5 pillars are flashing warning signs.

## 6. Stance
**Cautious / Hedged.** Structurally, the environment favors volatility-aware positioning rather than passive long-only risk. Net Gamma suggests jagged price action ahead.
"""

def generate_macro_note(as_of):
    print(f"Generating Macro Note for {as_of}...")
    
    ms = build_macro_state(as_of)
    
    # Summary for Prompt
    summary = f"""
    Date: {ms.as_of}
    SPX: {ms.spx_instability} ({ms.spx_regime})
    AUD/USD: {ms.audusd_instability} ({ms.audusd_regime})
    USD/JPY: {ms.jpy_instability} (FRAGILE)
    Reflexivity Loop: {ms.reflexive_loop_active}
    Rates Spread: {ms.spread_usjp_10y:.2f}%
    DXY 20d: {ms.dxy_ret_20d:.2f}%
    FX Equity Stress: {ms.fx_equity_stress}
    """
    
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'macro_note.txt')
    with open(prompt_path, 'r') as f:
        system_prompt = f.read()
        
    # In a real app, you'd call OpenAI here
    # note = call_openai(system_prompt, summary)
    note = call_llm_mock(system_prompt, summary)
    
    output_path = os.path.join(os.path.dirname(__file__), '..', 'reports', f'macro_note_{ms.as_of}.md')
    with open(output_path, 'w', encoding="utf-8") as f:
        f.write(note)
        
    print(f"Macro Note saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default="2024-01-05")
    args = parser.parse_args()
    generate_macro_note(datetime.strptime(args.date, "%Y-%m-%d").date())
