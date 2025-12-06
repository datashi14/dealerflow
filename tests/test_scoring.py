# import pytest

def calculate_spx_instability(net_gamma, gamma_slope):
    """
    Replicates SPX scoring logic for testing.
    """
    # Flow Risk
    flow_risk = 50
    if net_gamma < 0:
        flow_risk += 30
    else:
        flow_risk -= 20
        
    # Vol Risk
    vol_risk = min(abs(gamma_slope) * 100, 100)
    
    # Index
    instability = (flow_risk * 0.6) + (vol_risk * 0.4)
    return max(0, min(100, instability))

def classify_regime(instability):
    if instability < 30: return "STABLE"
    if instability > 70: return "EXPLOSIVE"
    return "FRAGILE"

def test_spx_stable_regime():
    # Positive Gamma (reward), Low Slope
    score = calculate_spx_instability(net_gamma=1000, gamma_slope=0.0)
    # Flow Risk = 50 - 20 = 30
    # Vol Risk = 0
    # Score = 30*0.6 + 0 = 18
    assert score == 18
    assert classify_regime(score) == "STABLE"

def test_spx_explosive_regime():
    # Negative Gamma (penalty), High Slope
    score = calculate_spx_instability(net_gamma=-1000, gamma_slope=0.8)
    # Flow Risk = 50 + 30 = 80
    # Vol Risk = 80
    # Score = 80*0.6 + 80*0.4 = 48 + 32 = 80
    assert score == 80
    assert classify_regime(score) == "EXPLOSIVE"

def test_spx_fragile_regime():
    # Negative Gamma, Low Slope
    score = calculate_spx_instability(net_gamma=-1000, gamma_slope=0.0)
    # Flow Risk = 80
    # Vol Risk = 0
    # Score = 80*0.6 = 48
    assert score == 48
    assert classify_regime(score) == "FRAGILE"

if __name__ == "__main__":
    # Simple runner if pytest not installed
    try:
        test_spx_stable_regime()
        test_spx_explosive_regime()
        test_spx_fragile_regime()
        print("All tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
