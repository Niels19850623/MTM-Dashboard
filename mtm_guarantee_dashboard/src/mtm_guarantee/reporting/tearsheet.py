from __future__ import annotations

from pathlib import Path


def write_tearsheet(path: str, title: str, metrics: dict, summary_md: str) -> str:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", "", "## Key Metrics"]
    for k, v in metrics.items():
        lines.append(f"- **{k}**: {v}")
    lines += ["", "## Scenario Summary", summary_md]
    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)
