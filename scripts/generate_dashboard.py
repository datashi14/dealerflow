import argparse
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.llm.macro_state import build_macro_state

try:
    from jinja2 import Template
except ImportError:
    print("Jinja2 not installed. Please pip install jinja2")
    sys.exit(1)

def generate_dashboard(as_of):
    print(f"Generating Dashboard for {as_of}...")
    
    # Build Macro State
    ms = build_macro_state(as_of)
    
    # Prepare Context
    context = {
        "date": ms.as_of,
        "spx_idx": f"{ms.spx_instability:.1f}",
        "spx_regime": ms.spx_regime,
        "aud_idx": f"{ms.audusd_instability:.1f}",
        "aud_regime": ms.audusd_regime,
        "jpy_idx": f"{ms.jpy_instability:.1f}",
        "jpy_regime": "FRAGILE", # Mocked in build_macro_state or derived
        "wti_idx": f"{ms.wti_instability:.1f}",
        "wti_regime": "FRAGILE", # Mock
        "nem_idx": f"{ms.nem_instability:.1f}",
        "nem_regime": "FRAGILE", # Mock
        
        "dxy_ret": f"{ms.dxy_ret_20d:.2f}",
        "fx_equity_stress": ms.fx_equity_stress,
        
        "us10y": f"{ms.us10y:.2f}",
        "jp10y": f"{ms.jp10y:.2f}",
        "spread": f"{ms.spread_usjp_10y * 100:.0f}",
        
        "reflexive": "YES" if ms.reflexive_loop_active else "NO"
    }
    
    # Load Template
    template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'dashboard.md.j2')
    with open(template_path, 'r') as f:
        t = Template(f.read())
        
    dashboard_md = t.render(**context)
    
    # Save
    output_path = os.path.join(os.path.dirname(__file__), '..', 'reports', f'dashboard_{ms.as_of}.md')
    with open(output_path, 'w', encoding="utf-8") as f:
        f.write(dashboard_md)
        
    print(f"Dashboard saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default="2024-01-05")
    args = parser.parse_args()
    generate_dashboard(datetime.strptime(args.date, "%Y-%m-%d").date())
