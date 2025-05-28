# biexp_calibrator.py
import numpy as np
from scipy.optimize import curve_fit, root_scalar
from PyQt5.QtCore import QObject

class BiExpCalibrator(QObject):
    """
    Bi-exponential calibrator where you supply Y0 and Plateau at fit time.
    
    Model:
        V(x) = Plateau
             + (Y0 - Plateau)*(PF/100)*exp(-KF*x)
             + (Y0 - Plateau)*((100-PF)/100)*exp(-KS*x)
    
    Only PF (PercentFast), KF (KFast), KS (KSlow) are fitted.
    """
    def __init__(self, win=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.win        = win
        self.Y0         = None
        self.Plateau    = None
        self.params_    = None
        self.errors_    = None
        self.v_min      = None
        self.v_max      = None

    def _model(self, x, PF, KF, KS):
        span = (self.Y0 - self.Plateau)
        span_fast = span * (PF * 0.01)
        span_slow = span * ((100 - PF) * 0.01)
        return (
            self.Plateau
            + span_fast * np.exp(-KF * np.asarray(x))
            + span_slow * np.exp(-KS * np.asarray(x))
        )

    def fit(
        self,
        xdata,
        ydata,
        Y0,
        Plateau,
        p0=(50.0, 0.001, 0.0001),
        bounds=([0.0, 0.0, 0.0], [100.0, np.inf, np.inf]),
    ):
        """
        Fit PercentFast, KFast, KSlow given fixed Y0 and Plateau.

        Parameters:
        - xdata, ydata: array-like calibration points
        - Y0: float, fixed intercept value
        - Plateau: float, fixed asymptote value
        - p0: initial guess tuple (PercentFast, KFast, KSlow)
        - bounds: ([PF_min,KF_min,KS_min], [PF_max,KF_max,KS_max])
        """
        self.Y0 = Y0
        self.Plateau = Plateau

        popt, pcov = curve_fit(
            self._model,
            xdata,
            ydata,
            p0=p0,
            bounds=bounds,
            maxfev=100000,
        )
        perr = np.sqrt(np.diag(pcov))
        self.params_ = {
            "PercentFast": popt[0],
            "KFast":       popt[1],
            "KSlow":       popt[2],
        }
        self.errors_ = {
            "PercentFast": perr[0],
            "KFast":       perr[1],
            "KSlow":       perr[2],
        }

        # Cache model output range for the fit interval
        x_min, x_max = np.min(xdata), np.max(xdata)
        v0 = self._model(x_min, *popt)
        v1 = self._model(x_max, *popt)
        self.v_min = min(v0, v1)
        self.v_max = max(v0, v1)

        return self.params_, self.errors_

    def predict(self, x):
        """
        Compute V for given NTU x (scalar or array).
        """
        if self.params_ is None:
            raise RuntimeError("Fit model first via .fit()")
        PF = self.params_["PercentFast"]
        KF = self.params_["KFast"]
        KS = self.params_["KSlow"]
        return self._model(x, PF, KF, KS)

    def inverse(self, V, x_min, x_max):
        """
        Solve for NTU x given voltage V, within [x_min, x_max].
        """
        if self.params_ is None:
            raise RuntimeError("Fit model first via .fit()")
        if not (self.v_min <= V <= self.v_max):
            raise ValueError(f"Requested voltage {V} is outside the model's output range [{self.v_min}, {self.v_max}]")
        PF = self.params_["PercentFast"]
        KF = self.params_["KFast"]
        KS = self.params_["KSlow"]
        f = lambda x: self._model(x, PF, KF, KS) - V
        sol = root_scalar(f, bracket=[x_min, x_max], method="brentq")
        if not sol.converged:
            raise RuntimeError(f"Root-finding failed for V={V}")
        return sol.root
    
    def get_settings(self):
        """
        Return a dict of the current fit settings (params, Y0, Plateau).
        """
        return {
            "params": self.params_,
            "errors": self.errors_,
            "Y0": self.Y0,
            "Plateau": self.Plateau,
        }

    def set_settings(self, settings):
        """
        Restore fit settings from a dict (as returned by get_settings).
        """
        self.params_ = settings.get("params")
        self.errors_ = settings.get("errors")
        self.Y0 = self.v_max = settings.get("Y0")
        self.Plateau = self.v_min = settings.get("Plateau")