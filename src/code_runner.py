"""Execute Python lab solutions safely and capture stdout for presentation-ready output."""

from __future__ import annotations

import ast
import io
import os
import re
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any


_MAX_OUTPUT_CHARS = 8_000


def looks_like_python(code: str) -> bool:
    c = (code or "").lstrip()
    if not c:
        return False
    if c.startswith("#include") or "int main(" in c:
        return False
    return True


def looks_like_c(code: str) -> bool:
    c = (code or "").lstrip()
    return bool(c) and (c.startswith("#include") or "int main(" in c)


def python_syntax_ok(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def ensure_house_prices_csv(work_dir: Path) -> Path:
    """Seed a tiny synthetic house_prices.csv for ML lab templates."""
    work_dir.mkdir(parents=True, exist_ok=True)
    path = work_dir / "house_prices.csv"
    if path.exists() and path.stat().st_size > 50:
        return path
    import numpy as np

    rng = np.random.default_rng(42)
    n = 300
    area = rng.uniform(800, 3200, n)
    beds = rng.integers(1, 6, n).astype(float)
    age = rng.uniform(0, 40, n)
    dist = rng.uniform(1, 25, n)
    price = (
        2.0
        + 0.004 * area
        + 0.8 * beds
        - 0.05 * age
        - 0.12 * dist
        + rng.normal(0, 0.8, n)
    )
    lines = ["area_sqft,bedrooms,age_years,distance_km,price_mpkr"]
    for i in range(n):
        lines.append(
            f"{area[i]:.1f},{beds[i]:.0f},{age[i]:.1f},{dist[i]:.1f},{price[i]:.2f}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_python_solution(
    code: str,
    work_dir: Path,
    *,
    task_number: int = 1,
) -> tuple[bool, str]:
    """Run Python code under Agg; return (ok, stdout_or_error)."""
    if not looks_like_python(code) or not python_syntax_ok(code):
        return False, "syntax_error"

    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    if re.search(r"house_prices\.csv", code):
        ensure_house_prices_csv(work_dir)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    prepared = re.sub(
        r"savefig\s*\(\s*['\"][^'\"]+['\"]",
        f"savefig('task_{task_number:02d}_fig_1.png'",
        code,
    )

    buf_out = io.StringIO()
    buf_err = io.StringIO()
    namespace: dict[str, Any] = {"__name__": "__main__"}
    prev = os.getcwd()
    try:
        os.chdir(work_dir)
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            exec(compile(prepared, f"<task_{task_number}>", "exec"), namespace, namespace)
            for num in plt.get_fignums():
                fig = plt.figure(num)
                if fig.get_axes():
                    fig.savefig(
                        work_dir / f"task_{task_number:02d}_fig_1.png",
                        dpi=150,
                        bbox_inches="tight",
                    )
            plt.close("all")
    except Exception as exc:  # noqa: BLE001
        plt.close("all")
        return False, f"{type(exc).__name__}: {exc}"
    finally:
        os.chdir(prev)
        plt.close("all")

    text = buf_out.getvalue().strip()
    if not text:
        err = buf_err.getvalue().strip()
        text = err or "Saved plot.png" if "savefig" in code else "(no stdout)"
    if len(text) > _MAX_OUTPUT_CHARS:
        text = text[: _MAX_OUTPUT_CHARS - 20] + "\n…[truncated]\n"
    return True, text + ("\n" if not text.endswith("\n") else "")


def polish_python_solution(
    code: str,
    output: str,
    work_dir: Path,
    *,
    task_number: int = 1,
) -> dict[str, str]:
    """Prefer real stdout when execution succeeds; otherwise keep provided output."""
    ok, captured = run_python_solution(code, work_dir, task_number=task_number)
    if ok:
        return {"code": code.rstrip() + "\n", "output": captured}
    return {"code": code.rstrip() + "\n", "output": (output or "").rstrip() + "\n"}
