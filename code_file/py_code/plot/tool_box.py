"""
econ_pub_plot.py

Publication-style plotting helpers for economics papers (grayscale, minimal).

Main components
---------------
1) Data helper:
   - make_eventstudy_df: parse Stata-like parm (D_12, D12, ...) into event_time

2) Plot style & helpers:
   - set_econ_pub_style, new_figure, format_axes
   - add_zero_line, add_vertical_line, add_legend

3) Plot primitives:
   - plot_descriptive_line
   - plot_reg_with_band / plot_reg_with_errorbar
   - plot_band_only

4) Composite:
   - plot_event_study
"""

from __future__ import annotations

import re
from typing import Sequence, Optional, Dict, Tuple, Union, Mapping

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


__all__ = [
    # data helper
    "make_eventstudy_df",
    # style & axes
    "set_econ_pub_style",
    "new_figure",
    "format_axes",
    "add_zero_line",
    "add_vertical_line",
    "add_legend",
    # primitives
    "plot_descriptive_line",
    "plot_reg_with_band",
    "plot_reg_with_errorbar",
    "plot_band_only",
    # composite
    "plot_event_study",
]


# =============================================================================
# 0. Data helpers
# =============================================================================

_EVENT_RE = re.compile(r"D_?\d+$")


def _parse_event_time(parm: object) -> Optional[int]:
    """
    Parse event-time token from strings like: D_12 (=> -12), D12 (=> +12).

    Rules
    -----
    - D_12  -> -12
    - D12   -> +12
    - no match -> None
    """
    s = str(parm)
    m = _EVENT_RE.search(s)
    if m is None:
        return None

    token = m.group(0)
    if token.startswith("D_"):
        return -int(token[2:])
    return int(token[1:])


def make_eventstudy_df(
    df: pd.DataFrame,
    pre_periods: int,
    post_periods: int,
    base_period: Union[int, str],
) -> pd.DataFrame:
    """
    Create a clean event-study dataframe from regression output.

    Expected columns (minimum)
    --------------------------
    - parm: strings like D_12, D0, D1, ...

    Optional numeric columns (will coerce to numeric if present)
    -----------------------------------------------------------
    - estimate, min90, max90

    Parameters
    ----------
    pre_periods : int
        Keep event_time in [-pre_periods, ...]
    post_periods : int
        Keep event_time in [..., post_periods]
    base_period : int or "nobase"
        If int, set estimate/min90/max90 at that event_time to 0.
        If "nobase" (case-insensitive), do nothing.
    """
    if "parm" not in df.columns:
        raise ValueError("make_eventstudy_df requires a 'parm' column.")

    out = df.copy()

    # ensure numeric where present
    for col in ("estimate", "min90", "max90"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    # parse event time
    out["event_time"] = out["parm"].map(_parse_event_time)
    out = out[out["event_time"].notna()].copy()
    out["event_time"] = out["event_time"].astype(int)

    # limit window
    out = out[(out["event_time"] >= -pre_periods) & (out["event_time"] <= post_periods)].copy()

    # handle base period
    if not (isinstance(base_period, str) and base_period.lower() == "nobase"):
        if not isinstance(base_period, (int, np.integer)):
            raise ValueError("base_period must be an int or 'nobase'.")
        cols = [c for c in ("estimate", "min90", "max90") if c in out.columns]
        if cols:
            out.loc[out["event_time"] == int(base_period), cols] = 0.0

    return out.sort_values("event_time").reset_index(drop=True)


# =============================================================================
# 1. Global style
# =============================================================================

def set_econ_pub_style(
    use_tex: bool = True,
    font_family: str = "serif",
    font_serif: Optional[Sequence[str]] = None,
    base_fontsize: int = 9,
) -> None:
    """Set global matplotlib style for econ publication figures."""
    rc = {
        "font.family": font_family,
        "axes.labelsize": base_fontsize,
        "xtick.labelsize": base_fontsize - 1,
        "ytick.labelsize": base_fontsize - 1,
        "legend.fontsize": base_fontsize - 1,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.0,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",
        "figure.dpi": 100,
        "savefig.dpi": 300,
    }

    if font_serif is not None:
        rc["font.serif"] = list(font_serif)

    if use_tex:
        rc["text.usetex"] = True
        rc["text.latex.preamble"] = r"\usepackage{amsmath}"

    plt.rcParams.update(rc)


# =============================================================================
# 2. Basic helpers: new figure + axis formatting
# =============================================================================

def new_figure(width: float = 6.0, height: float = 3.5) -> Tuple[plt.Figure, plt.Axes]:
    """Create a new figure and axis with default econ-paper size."""
    fig, ax = plt.subplots(figsize=(width, height))
    return fig, ax


def format_axes(
    ax: plt.Axes,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    xlim: Optional[Tuple[float, float]] = None,
    ylim: Optional[Tuple[float, float]] = None,
    inward_ticks: bool = True,
) -> None:
    """Apply econ-publication axis formatting (left/bottom spines only)."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.tick_params(
        axis="both",
        direction="in" if inward_ticks else "out",
        length=3,
        width=0.8,
        top=False,
        right=False,
    )

    if x_label is not None:
        ax.set_xlabel(x_label)
    if y_label is not None:
        ax.set_ylabel(y_label)
    if xlim is not None:
        ax.set_xlim(*xlim)
    if ylim is not None:
        ax.set_ylim(*ylim)


def add_zero_line(ax: plt.Axes, linewidth: float = 0.8) -> None:
    """Add horizontal zero line (y=0)."""
    ax.axhline(0.0, color="0.4", linestyle="--", linewidth=linewidth)


def add_vertical_line(
    ax: plt.Axes,
    x: float,
    linewidth: float = 0.8,
    color: str = "0.4",
    linestyle: str = "--",
) -> None:
    """Add vertical reference line at x."""
    ax.axvline(x, color=color, linestyle=linestyle, linewidth=linewidth)


# =============================================================================
# 3. Descriptive line plots
# =============================================================================

def plot_descriptive_line(
    ax: plt.Axes,
    x: Sequence[float],
    series: Mapping[str, Sequence[float]],
    styles: Optional[Mapping[str, Dict]] = None,
) -> None:
    """
    Plot one or multiple descriptive lines.

    series: {label -> y-values}
    styles: {label -> matplotlib kwargs}
    """
    x_arr = np.asarray(x)

    for label, y in series.items():
        y_arr = np.asarray(y)
        kw = {"label": label, "color": "0.0", "linewidth": 1.0}
        if styles is not None and label in styles:
            kw.update(styles[label])
        ax.plot(x_arr, y_arr, **kw)


# =============================================================================
# 4. Regression plots with confidence intervals
# =============================================================================

def plot_reg_with_band(
    ax: plt.Axes,
    x: Sequence[float],
    beta: Sequence[float],
    ci_low: Sequence[float],
    ci_high: Sequence[float],
    label: Optional[str] = None,
) -> None:
    """Plot regression coefficients with shaded CI band + line."""
    x = np.asarray(x)
    beta = np.asarray(beta)
    ci_low = np.asarray(ci_low)
    ci_high = np.asarray(ci_high)

    ax.fill_between(x, ci_low, ci_high, color="0.8", alpha=0.5, linewidth=0.0)
    ax.plot(x, beta, color="0.0", marker="o", markersize=3, linewidth=1.0, label=label)


def plot_reg_with_errorbar(
    ax: plt.Axes,
    x: Sequence[float],
    beta: Sequence[float],
    ci_low: Sequence[float],
    ci_high: Sequence[float],
    label: Optional[str] = None,
    marker: str = "s",
) -> None:
    """Plot regression coefficients with CI error bars."""
    x = np.asarray(x)
    beta = np.asarray(beta)
    ci_low = np.asarray(ci_low)
    ci_high = np.asarray(ci_high)

    yerr = np.vstack([beta - ci_low, ci_high - beta])

    ax.errorbar(
        x,
        beta,
        yerr=yerr,
        fmt=f"{marker}-",
        color="0.0",
        markersize=3,
        linewidth=1.0,
        capsize=2,
        label=label,
        zorder=2,
    )


def plot_band_only(
    ax: plt.Axes,
    x: Sequence[float],
    ci_low: Sequence[float],
    ci_high: Sequence[float],
    label: Optional[str] = None,
    color: str = "0.8",
    alpha: float = 0.5,
    zorder: int = 1,
) -> None:
    """Plot only a shaded CI band (no point estimate line)."""
    x = np.asarray(x)
    ci_low = np.asarray(ci_low)
    ci_high = np.asarray(ci_high)

    ax.fill_between(
        x,
        ci_low,
        ci_high,
        color=color,
        alpha=alpha,
        linewidth=0.0,
        zorder=zorder,
        label=label,
    )


# =============================================================================
# 5. Event-study / parallel-trend plots
# =============================================================================

def _looks_integer_like(x: np.ndarray, tol: float = 1e-9) -> bool:
    """True if x values are (almost) all integers."""
    if x.size == 0:
        return False
    if x.dtype.kind in "iu":
        return True
    return np.all(np.isfinite(x)) and np.all(np.abs(x - np.round(x)) <= tol)


def plot_event_study(
    ax: plt.Axes,
    x: Sequence[float],
    beta: Sequence[float],
    ci_low: Sequence[float],
    ci_high: Sequence[float],
    treat_time: float = -1.0,
    use_errorbar: bool = True,
    marker: str = "s",
    label: Optional[str] = None,
    add_ref_lines: bool = True,
    xtick_step: int = 2,
    xpad: float = 0.5,
) -> None:
    """
    Event-study plot: coefficients + CI + (optional) 0-line and treat-time line.
    """
    x = np.asarray(x, dtype=float)
    beta = np.asarray(beta, dtype=float)
    ci_low = np.asarray(ci_low, dtype=float)
    ci_high = np.asarray(ci_high, dtype=float)

    if use_errorbar:
        plot_reg_with_errorbar(ax, x, beta, ci_low, ci_high, label=label, marker=marker)
    else:
        plot_reg_with_band(ax, x, beta, ci_low, ci_high, label=label)

    if add_ref_lines:
        add_zero_line(ax)
        add_vertical_line(ax, treat_time)

    # nicer x-limits
    ax.set_xlim(float(np.min(x)) - xpad, float(np.max(x)) + xpad)

    # integer-like ticks
    if _looks_integer_like(x) and xtick_step > 0:
        xmin = int(np.round(np.min(x)))
        xmax = int(np.round(np.max(x)))
        ax.set_xticks(np.arange(xmin, xmax + 1, xtick_step))


# =============================================================================
# 6. Legend helper
# =============================================================================

def add_legend(
    ax: plt.Axes,
    loc: str = "upper center",
    ncol: int = 2,
    outside: bool = False,
) -> None:
    """Add a minimal, frame-less legend."""
    if outside:
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.15),
            ncol=ncol,
            frameon=False,
            handlelength=2,
        )
    else:
        ax.legend(
            loc=loc,
            frameon=False,
            ncol=ncol,
            handlelength=2,
        )