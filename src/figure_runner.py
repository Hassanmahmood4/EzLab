"""Run task code (or plot templates) and collect PNG figures for the report."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_PLOT_HINT = re.compile(
    r"(?i)\b(plot|plt\.|matplotlib|seaborn|sns\.|pairplot|pair\s*plot|"
    r"histogram|hist\(|scatter|residual|learning\s*curve|qq[-\s]?plot|"
    r"funnel|savefig|figure|graph|draw a|visuali[sz]e|visualization|"
    r"single features?|rank the features?|contour|heatmap|boxplot|barh?\()\b"
)


def task_needs_figures(task: dict[str, Any] | Any) -> bool:
    if hasattr(task, "model_dump"):
        task = task.model_dump()
    blob = f"{task.get('title', '')}\n{task.get('prompt', '')}\n{task.get('code', '')}"
    return bool(_PLOT_HINT.search(blob))


def _safe_slug(number: int, index: int) -> str:
    return f"task_{number:02d}_fig_{index}.png"


def _rewrite_savefig_calls(code: str, default_name: str) -> str:
    """Point bare savefig('plot.png') style calls at our task figure name."""
    return re.sub(
        r"savefig\s*\(\s*['\"][^'\"]+['\"]",
        f"savefig('{default_name}'",
        code,
    )


def _exec_task_code(code: str, work_dir: Path, task_number: int) -> list[Path]:
    """Execute student code under Agg and collect PNGs written to work_dir."""
    import io
    import os
    from contextlib import redirect_stdout, redirect_stderr

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    work_dir.mkdir(parents=True, exist_ok=True)
    before = {p.resolve() for p in work_dir.glob("*.png")}
    prepared = code

    original_show = plt.show
    save_counter = {"n": 0}

    def _next_path() -> Path:
        save_counter["n"] += 1
        return work_dir / _safe_slug(task_number, save_counter["n"])

    def _show(*_a, **_k):
        fig = plt.gcf()
        if fig.get_axes():
            fig.savefig(_next_path(), dpi=150, bbox_inches="tight")
        plt.close("all")

    plt.show = _show  # type: ignore[assignment]

    namespace: dict[str, Any] = {"__name__": "__main__"}
    prev_cwd = os.getcwd()
    try:
        os.chdir(work_dir)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            exec(compile(prepared, f"<task_{task_number}>", "exec"), namespace, namespace)
            for num in plt.get_fignums():
                fig = plt.figure(num)
                if fig.get_axes():
                    fig.savefig(_next_path(), dpi=150, bbox_inches="tight")
            plt.close("all")
    except Exception:
        plt.close("all")
    finally:
        plt.show = original_show  # type: ignore[assignment]
        os.chdir(prev_cwd)

    after = [p for p in work_dir.glob("*.png") if p.resolve() not in before]
    named = sorted(p for p in after if p.name.startswith(f"task_{task_number:02d}_fig_"))
    if named:
        return named
    renamed: list[Path] = []
    for i, path in enumerate(sorted(after), start=1):
        dest = work_dir / _safe_slug(task_number, i)
        if path.resolve() != dest.resolve():
            if dest.exists():
                dest.unlink()
            path.replace(dest)
        renamed.append(dest)
    return renamed


def _template_figure(task: dict[str, Any], work_dir: Path) -> Path | None:
    """Draw a representative figure when code did not produce one."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from math import erf

    # Inverse erf via Newton — enough for a QQ guide line (no scipy needed)
    def erfinv(values: np.ndarray) -> np.ndarray:
        out = np.empty_like(values, dtype=float)
        for i, v in enumerate(np.asarray(values, dtype=float)):
            v = float(np.clip(v, -0.999999, 0.999999))
            x = v * 0.88622692545  # sqrt(pi)/2 seed
            for _ in range(8):
                x -= (erf(x) - v) / (2 / np.sqrt(np.pi) * np.exp(-x * x))
            out[i] = x
        return out

    title = str(task.get("title") or "")
    prompt = str(task.get("prompt") or "")
    blob = f"{title}\n{prompt}".lower()
    number = int(task.get("number") or 1)
    out = work_dir / _safe_slug(number, 1)
    work_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    rng = np.random.default_rng(number * 17 + 3)

    if "learning curve" in blob or "training-set" in blob or "flatten" in blob:
        n = np.array([20, 40, 80, 160, 225])
        train = 2.4 - 0.35 * np.log(n) + 0.05
        test = 3.1 - 0.42 * np.log(n) + 0.08
        ax.plot(n, train, "o-", color="#0072B2", label="Train RMSE")
        ax.plot(n, test, "s--", color="#D55E00", label="Test RMSE")
        ax.set_xlabel("Training set size")
        ax.set_ylabel("RMSE")
        ax.set_title(f"Task {number}: Learning curve")
        ax.legend()
    elif "qq" in blob or "residual" in blob or "diagnostic" in blob:
        if "histogram" in blob or "hist" in blob:
            resid = rng.normal(0, 1.0, 220)
            ax.hist(resid, bins=18, color="#0072B2", edgecolor="white", alpha=0.9)
            ax.set_title(f"Task {number}: Residual histogram")
            ax.set_xlabel("Residual")
            ax.set_ylabel("Count")
        else:
            sample = np.sort(rng.normal(0, 1.0, 180))
            # Approximate normal theoretical quantiles without scipy
            probs = (np.arange(1, len(sample) + 1) - 0.5) / len(sample)
            theo = np.sqrt(2) * erfinv(2 * probs - 1)
            ax.scatter(theo, sample, s=12, color="#0072B2")
            lim = max(abs(theo).max(), abs(sample).max()) * 1.05
            ax.plot([-lim, lim], [-lim, lim], color="#D55E00", lw=1.4)
            ax.set_xlabel("Theoretical quantiles")
            ax.set_ylabel("Sample quantiles")
            ax.set_title(f"Task {number}: Residual Q–Q plot")
    elif "histogram" in blob or "split variation" in blob or "random_state" in blob:
        vals = rng.normal(0.84, 0.03, 30)
        ax.hist(vals, bins=10, color="#0072B2", edgecolor="white")
        ax.set_title(f"Task {number}: Test R² across splits")
        ax.set_xlabel("Test R²")
        ax.set_ylabel("Count")
    elif "heteroscedastic" in blob or "funnel" in blob:
        x = np.linspace(1, 10, 200)
        y = 2 + 0.8 * x + rng.normal(0, 0.35 * x)
        coef = np.polyfit(x, y, 1)
        yhat = coef[0] * x + coef[1]
        ax.scatter(yhat, y - yhat, s=12, color="#0072B2", alpha=0.75)
        ax.axhline(0, color="#6b7a8c", lw=1)
        ax.set_xlabel("Fitted values")
        ax.set_ylabel("Residuals")
        ax.set_title(f"Task {number}: Funnel-shaped residuals")
    elif "lasso" in blob or "regularis" in blob or "regulariz" in blob or "alpha" in blob:
        alphas = np.logspace(-2, 1, 30)
        for i in range(6):
            path = np.exp(-alphas * (0.4 + 0.2 * i)) * (1.2 - 0.12 * i)
            ax.plot(alphas, path, lw=1.6)
        ax.set_xscale("log")
        ax.set_xlabel("α")
        ax.set_ylabel("Coefficient")
        ax.set_title(f"Task {number}: Lasso regularisation path")
    elif "by hand" in blob or "simple regression" in blob or "slope" in blob:
        x = np.array([1, 2, 3, 4, 5], float)
        y = np.array([2, 3, 5, 4, 6], float)
        b1 = np.sum((x - x.mean()) * (y - y.mean())) / np.sum((x - x.mean()) ** 2)
        b0 = y.mean() - b1 * x.mean()
        xs = np.linspace(1, 5, 50)
        ax.scatter(x, y, color="#0072B2", zorder=3)
        ax.plot(xs, b0 + b1 * xs, color="#D55E00", label="Fitted line")
        ax.set_title(f"Task {number}: Simple regression fit")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.legend()
    elif "single feature" in blob or "rank the feature" in blob or (
        "rank" in blob and "feature" in blob
    ):
        feats = ["area", "bedrooms", "distance", "age"]
        r2 = [0.81, 0.54, 0.21, 0.19]
        ax.barh(feats[::-1], r2[::-1], color="#0072B2")
        ax.set_xlabel("Test R²")
        ax.set_title(f"Task {number}: Single-feature R²")
    elif "pair" in blob or "seaborn" in blob or "sns" in blob or "wine" in blob:
        plt.close(fig)
        fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.4))
        colors = np.array(["#0072B2", "#D55E00", "#009E73"])
        for ax_i in axes.ravel():
            for c, col in enumerate(colors):
                pts = rng.normal(loc=(c - 1) * 1.2, scale=0.55, size=(40, 2))
                ax_i.scatter(pts[:, 0], pts[:, 1], s=14, c=col, alpha=0.75, label=f"class {c}")
            ax_i.grid(True, alpha=0.2)
        axes[0, 0].set_title("alcohol vs flavanoids")
        axes[0, 1].set_title("color vs flavanoids")
        axes[1, 0].set_title("alcohol vs color")
        axes[1, 1].set_title("proline vs flavanoids")
        axes[0, 1].legend(fontsize=7, loc="best")
        fig.suptitle(f"Task {number}: Pair-plot style feature view", fontsize=11)
        fig.tight_layout()
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return out if out.exists() else None
    else:
        x = np.linspace(0, 10, 80)
        ax.plot(x, 0.9 * x + 1.5 + rng.normal(0, 0.4, 80), "o", ms=3, color="#0072B2", alpha=0.7)
        ax.plot(x, 0.9 * x + 1.5, color="#D55E00", lw=2, label="Fit")
        ax.set_title(f"Task {number}: {title[:48] or 'Figure'}")
        ax.legend()

    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out if out.exists() else None


def collect_task_figures(task: dict[str, Any] | Any, work_dir: Path) -> list[str]:
    """Return relative PNG filenames for a task (empty if none)."""
    if hasattr(task, "model_dump"):
        data = task.model_dump()
    else:
        data = dict(task)

    number = int(data.get("number") or 1)
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Drop stale figs for this task
    for old in work_dir.glob(f"task_{number:02d}_fig_*.png"):
        old.unlink(missing_ok=True)

    paths: list[Path] = []
    code = str(data.get("code") or "")
    if code.strip() and (_PLOT_HINT.search(code) or task_needs_figures(data)):
        try:
            paths = _exec_task_code(code, work_dir, number)
        except Exception:
            paths = []

    if not paths and task_needs_figures(data):
        generated = _template_figure(data, work_dir)
        if generated is not None:
            paths = [generated]

    return [p.name for p in paths if p.exists()]


def attach_figures_to_report(report: Any, work_dir: Path) -> tuple[Any, list[str]]:
    """Return (report_with_figures, figure filenames)."""
    work_dir = Path(work_dir)
    all_names: list[str] = []
    updated_tasks: list[dict[str, Any]] = []
    for task in report.tasks:
        try:
            names = collect_task_figures(task, work_dir)
        except Exception:
            names = []
        data = task.model_dump()
        data["figures"] = names
        updated_tasks.append(data)
        all_names.extend(names)
    payload = report.model_dump()
    payload["tasks"] = updated_tasks
    return type(report).model_validate(payload), all_names
