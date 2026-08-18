"""Portable Matplotlib style helpers for CUMCM paper figures."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap

PALETTE_SETS = {
    "SET-A": {
        "primary": "#2B495D",
        "contrast": "#B3A14B",
        "auxiliary": "#D0BADC",
        "neutral": "#818181",
        "accent": "#B6303B",
        "basis": "深海蓝主色—红色重点—金黄对比—淡紫辅助；与其他组同角色色相距均≥88.2°，CIELAB L*≈29.59–78.28，相邻最小 ΔL*=12.09。",
    },
    "SET-B": {
        "primary": "#692E6F",
        "contrast": "#53B474",
        "auxiliary": "#D7BCB7",
        "neutral": "#818181",
        "accent": "#4C6C20",
        "basis": "深茄紫主色—黄绿重点—绿色对比—淡橙红辅助；与其他组同角色色相距均≥88.2°，CIELAB L*≈29.68–78.36，相邻最小 ΔL*=12.04。",
    },
    "SET-C": {
        "primary": "#5C402B",
        "contrast": "#939ED7",
        "auxiliary": "#AFCAA2",
        "neutral": "#818181",
        "accent": "#1E6E67",
        "basis": "深橙棕主色—青色重点—蓝紫对比—淡绿辅助；与其他组同角色色相距均≥88.2°，CIELAB L*≈29.71–78.44，相邻最小 ΔL*=12.12。",
    },
    "SET-D": {
        "primary": "#2A4E26",
        "contrast": "#D38ABA",
        "auxiliary": "#A7C8CF",
        "neutral": "#818181",
        "accent": "#7B41CD",
        "basis": "深墨绿主色—靛紫重点—品红对比—淡青蓝辅助；与其他组同角色色相距均≥88.2°，CIELAB L*≈29.62–78.48，相邻最小 ΔL*=12.13。",
    },
}

_SERIES_ROLES = ("primary", "contrast", "auxiliary", "neutral", "accent")
_CHROME_COLORS = {
    "light": "#F5F5F2",
    "text": "#4F555A",
    "grid": "#D1D5DB",
}


def get_palette_set(palette_set: str) -> dict[str, object]:
    """Return one explicitly selected, internally consistent palette set."""
    if not palette_set or not palette_set.strip():
        raise ValueError(
            "palette_set is required; explicitly choose SET-A, SET-B, SET-C, or SET-D"
        )
    normalized = palette_set.strip().upper()
    if normalized not in PALETTE_SETS:
        choices = ", ".join(PALETTE_SETS)
        raise ValueError(f"unknown palette_set {palette_set!r}; choose one of: {choices}")

    definition = PALETTE_SETS[normalized]
    colors = {role: definition[role] for role in _SERIES_ROLES}
    palette = [colors[role] for role in _SERIES_ROLES]
    sequential = LinearSegmentedColormap.from_list(
        f"cumcm_{normalized.lower()}_sequential",
        [
            _CHROME_COLORS["light"],
            colors["auxiliary"],
            colors["contrast"],
            colors["neutral"],
            colors["accent"],
            colors["primary"],
        ],
        N=256,
    )
    diverging = LinearSegmentedColormap.from_list(
        f"cumcm_{normalized.lower()}_diverging",
        [colors["primary"], "#DCE4E8", _CHROME_COLORS["light"], "#E8DAD7", colors["accent"]],
        N=256,
    )
    return {
        "palette_set": normalized,
        "colors": colors,
        "palette": palette,
        "sequential": sequential,
        "diverging": diverging,
        "basis": definition["basis"],
    }

_CJK_CANDIDATES = [
    "Heiti TC",
    "Heiti SC",
    "Hiragino Sans GB",
    "Noto Sans CJK SC",
    "Source Han Sans SC",
    "Microsoft YaHei",
    "PingFang SC",
    "SimHei",
    "WenQuanYi Micro Hei",
]

_CJK_FONT_FILES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]


def choose_cjk_font(candidates: Sequence[str] = _CJK_CANDIDATES) -> str:
    """Return the first installed CJK font, or Matplotlib's fallback."""
    for font_path in map(Path, _CJK_FONT_FILES):
        if not font_path.exists():
            continue
        try:
            font_manager.fontManager.addfont(font_path)
        except (OSError, RuntimeError):
            continue
    installed = {item.name for item in font_manager.fontManager.ttflist}
    return next((name for name in candidates if name in installed), "DejaVu Sans")


def apply_cumcm_style(palette_set: str, font_name: str | None = None) -> str:
    """Apply one explicitly selected paper palette without changing plotted data."""
    selected_palette = get_palette_set(palette_set)
    selected = font_name or choose_cjk_font()
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [selected, "DejaVu Sans"],
            "axes.unicode_minus": False,
            "axes.prop_cycle": mpl.cycler(color=selected_palette["palette"]),
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "legend.fontsize": 8,
            "legend.edgecolor": _CHROME_COLORS["grid"],
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.5,
            "lines.markersize": 4.5,
            "text.color": _CHROME_COLORS["text"],
            "axes.labelcolor": _CHROME_COLORS["text"],
            "axes.edgecolor": _CHROME_COLORS["text"],
            "xtick.color": _CHROME_COLORS["text"],
            "ytick.color": _CHROME_COLORS["text"],
            "grid.color": _CHROME_COLORS["grid"],
            "grid.linewidth": 0.6,
            "grid.alpha": 0.65,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    return selected


def style_axes(ax, *, grid: bool = True) -> None:
    """Apply consistent axes treatment without changing plotted data."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(True, axis="both")
        ax.set_axisbelow(True)


def label_panels(axes: Iterable, labels: Sequence[str] | None = None) -> None:
    """Add (a), (b), ... labels to a flat or nested axes collection."""
    flat = list(getattr(axes, "flat", axes))
    panel_labels = labels or [f"({chr(97 + i)})" for i in range(len(flat))]
    if len(panel_labels) < len(flat):
        raise ValueError("not enough panel labels")
    for ax, label in zip(flat, panel_labels):
        ax.text(
            0.01,
            0.99,
            label,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontfamily="DejaVu Sans",
            fontweight="bold",
        )


def export_figure(
    fig,
    output_stem: str | Path,
    *,
    formats: Sequence[str] = ("pdf", "png"),
    dpi: int = 320,
    close: bool = True,
) -> list[Path]:
    """Export vector and raster copies from one frozen figure object."""
    stem = Path(output_stem)
    if stem.suffix:
        raise ValueError("output_stem must not include a suffix")
    stem.parent.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for fmt in formats:
        normalized = fmt.lower().lstrip(".")
        if normalized not in {"pdf", "svg", "png"}:
            raise ValueError(f"unsupported format: {fmt}")
        path = stem.with_suffix(f".{normalized}")
        kwargs = {"bbox_inches": "tight", "facecolor": "white"}
        if normalized == "png":
            kwargs["dpi"] = dpi
        fig.savefig(path, **kwargs)
        written.append(path)
    if close:
        plt.close(fig)
    return written
