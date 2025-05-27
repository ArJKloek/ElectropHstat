import numpy as np
import pandas as pd
from scipy.optimize import curve_fit, root_scalar

# ── 1) FIXED constants ─────────────────────────────────────────────────
Y0      = 4600    # fixed intercept
Plateau = 300    # fixed asymptote

# ── 2) MODEL with only 3 free params ──────────────────────────────────
def biexp3(x, PercentFast, KFast, KSlow):
    span_fast = (Y0 - Plateau) * (PercentFast * 0.01)
    span_slow = (Y0 - Plateau) * ((100 - PercentFast) * 0.01)
    return Plateau + span_fast * np.exp(-KFast * x) + span_slow * np.exp(-KSlow * x)

# ── 3) FITTING routine ────────────────────────────────────────────────
def fit_three(xdata, ydata, p0, bounds):
    popt, pcov = curve_fit(
        biexp3, xdata, ydata,
        p0=p0, bounds=bounds, maxfev=100000
    )
    perr = np.sqrt(np.diag(pcov))
    return popt, perr

# ── 4) INVERSION helper V → NTU ───────────────────────────────────────
def voltage_to_ntu(V, popt, x_min, x_max):
    f = lambda x: biexp3(x, *popt) - V
    sol = root_scalar(f, bracket=[x_min, x_max], method='brentq')
    if not sol.converged:
        raise RuntimeError(f"Failed to invert V={V}")
    return sol.root

# ── 5) USAGE EXAMPLE ───────────────────────────────────────────────────
if __name__ == "__main__":
    # — load your data —
    # Option A: CSV/Excel
    # df = pd.read_csv("calibration.csv")        # columns "NTU","V"
    # xdata = df["NTU"].values;  ydata = df["V"].values

    # Option B: hard-coded
    xdata = np.array([0.005, 1000, 2000, 3000, 4000])
    ydata = np.array([4600,   3350, 2600,   2100,   1650])

    # — initial guesses & bounds for [PercentFast, KFast, KSlow] —
    p0     = [3.0,    0.01,   0.0002]           # tweak as you like
    bounds = ([0.0,    0.0,     0.0],             # PercentFast≥0, rates≥0
              [100.0,  np.inf,  np.inf])          # PercentFast≤100

    popt, perr = fit_three(xdata, ydata, p0, bounds)
    names = ["PercentFast (%)", "KFast", "KSlow"]
    print("Fitted parameters:")
    for n, v, e in zip(names, popt, perr):
        print(f"  {n:16s} = {v:.6g} ± {e:.6g}")

    # — demonstrate inversion —
    print("\nConvert V→NTU:")
    for V in [4.0, 2.5, 1.8]:
        ntu = voltage_to_ntu(V, popt, xdata.min(), xdata.max())
        print(f"  V={V:.2f} → NTU ≈ {ntu:.2f}")
