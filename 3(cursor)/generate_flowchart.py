#!/usr/bin/env python3
"""Generate process flowchart (JPG + PDF) from P&ID extraction data."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def load_entities(json_path: Path) -> list[dict]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return data["pages"][0]["entities"]


def draw_flowchart(entities: list[dict], out_jpg: Path, out_pdf: Path) -> None:
    """Draw schematic lube oil system flowchart based on extracted equipment."""
    fig, ax = plt.subplots(figsize=(16, 11), dpi=150)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)
    ax.axis("off")
    fig.patch.set_facecolor("#f8f9fa")

    # Title
    ax.text(
        8, 10.4, "Lube Oil System — Process Flowchart",
        ha="center", va="center", fontsize=18, fontweight="bold", color="#1a1a2e",
    )
    ax.text(
        8, 9.95, "Compressor K-01  |  Source: 123.pdf P&ID extraction",
        ha="center", va="center", fontsize=10, color="#555",
    )
    ax.text(
        8, 9.55,
        "Schematic flow — equipment tags from extraction; connections inferred from typical lube oil topology",
        ha="center", va="center", fontsize=8, color="#888", style="italic",
    )

    def box(x, y, w, h, text, color="#dbeafe", edge="#2563eb", fontsize=9):
        patch = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.15",
            facecolor=color, edgecolor=edge, linewidth=1.8,
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color="#1e293b", wrap=True)

    def valve(x, y, tag, label=""):
        """Diamond-ish valve symbol."""
        diamond = plt.Polygon(
            [(x, y + 0.25), (x + 0.35, y), (x, y - 0.25), (x - 0.35, y)],
            closed=True, facecolor="#fef3c7", edgecolor="#d97706", linewidth=1.5,
        )
        ax.add_patch(diamond)
        txt = f"{tag}\n{label}" if label else tag
        ax.text(x, y - 0.55, txt, ha="center", va="top", fontsize=7, color="#92400e")

    def instrument(x, y, tag):
        circle = plt.Circle((x, y), 0.22, facecolor="#ede9fe", edgecolor="#7c3aed", linewidth=1.2)
        ax.add_patch(circle)
        ax.text(x, y, tag, ha="center", va="center", fontsize=6.5, fontweight="bold", color="#5b21b6")

    def arrow(x1, y1, x2, y2, label="", color="#334155"):
        arr = FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle="-|>", mutation_scale=14,
            linewidth=2, color=color, connectionstyle="arc3,rad=0.0",
        )
        ax.add_patch(arr)
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + 0.15
            ax.text(mx, my, label, ha="center", fontsize=7, color="#64748b",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#e2e8f0", alpha=0.9))

    # --- Main equipment layout ---
    # Tank (bottom center)
    box(5.5, 1.0, 5.0, 1.2, "LUBE AND SEAL OIL TANK\nLG  LS  |  MANWAY 004/005  |  DIP STICK 004",
        color="#dcfce7", edge="#16a34a", fontsize=8.5)

    # Pumps (parallel)
    box(2.0, 3.0, 2.8, 1.0, "LUBE OIL PUMP\nP-01", color="#dbeafe", edge="#2563eb")
    box(11.2, 3.0, 2.8, 1.0, "LUBE OIL PUMP\nP-02 (Standby)", color="#dbeafe", edge="#2563eb")

    # Filter
    box(6.5, 3.0, 3.0, 1.0, "OIL FILTER\n007  |  PS", color="#e0f2fe", edge="#0284c7")

    # Heaters
    box(2.5, 5.2, 2.6, 1.0, "HEATER 001\nTS  XL-001  HS-001", color="#ffedd5", edge="#ea580c")
    box(11.0, 5.2, 2.6, 1.0, "HEATER 002\nTS  XL-002  HS", color="#ffedd5", edge="#ea580c")

    # Cooler
    box(6.0, 5.2, 4.0, 1.0, "AIR COOLER H-004\nTG  PDS-003", color="#cffafe", edge="#0891b2")

    # Compressor (top)
    box(5.5, 7.5, 5.0, 1.2, "COMPRESSOR K-01\nLube Oil System", color="#fee2e2", edge="#dc2626", fontsize=10)

    # --- Valves on flow lines ---
    valve(4.0, 2.3, "PCV-001", "Pressure Ctrl")
    valve(8.0, 2.3, "PCV-002", "Pressure Ctrl")
    valve(8.0, 4.2, "TCV-005", "Temp Ctrl")
    valve(3.5, 4.5, "PZV-001", "Relief")
    valve(12.5, 4.5, "PZV-002", "Relief")
    valve(8.0, 6.5, "PZV-005", "Relief")

    # --- Instruments ---
    instrument(13.5, 7.8, "TIC\n004")
    instrument(13.5, 6.2, "PDT\n004")
    instrument(13.5, 4.8, "PDI")
    instrument(2.0, 7.8, "PG\n001")
    instrument(2.0, 6.2, "PD\n005")

    # --- Flow arrows ---
    # Tank to pumps
    arrow(6.0, 2.2, 3.4, 3.0, "Suction")
    arrow(10.0, 2.2, 12.6, 3.0, "Suction")

    # Pumps to filter
    arrow(4.8, 3.5, 6.5, 3.5, "Discharge")
    arrow(11.2, 3.5, 9.5, 3.5)

    # Filter to heaters/cooler
    arrow(8.0, 4.0, 8.0, 5.2, "Supply")
    arrow(7.0, 4.0, 3.8, 5.2)
    arrow(9.0, 4.0, 12.3, 5.2)

    # To compressor
    arrow(8.0, 6.2, 8.0, 7.5, "To K-01")
    arrow(3.8, 6.2, 6.0, 7.5)
    arrow(12.3, 6.2, 10.0, 7.5)

    # Return to tank
    arrow(6.5, 8.1, 4.0, 2.2, "Return", color="#16a34a")
    arrow(9.5, 8.1, 12.0, 2.2, "TO TANK", color="#16a34a")

    # Control dashed lines
    ax.plot([13.28, 8.35], [7.8, 6.5], "--", color="#7c3aed", linewidth=1, alpha=0.7)
    ax.text(11.2, 7.3, "TIC-004 → TCV-005", fontsize=7, color="#7c3aed", style="italic")

    # Legend
    legend_items = [
        mpatches.Patch(facecolor="#dbeafe", edgecolor="#2563eb", label="Equipment"),
        mpatches.Patch(facecolor="#fef3c7", edgecolor="#d97706", label="Valve"),
        mpatches.Patch(facecolor="#ede9fe", edgecolor="#7c3aed", label="Instrument"),
        mpatches.FancyArrow(0, 0, 0.3, 0, width=0.08, color="#334155", label="Process flow"),
        mpatches.FancyArrow(0, 0, 0.3, 0, width=0.08, color="#16a34a", label="Return to tank"),
    ]
    ax.legend(handles=legend_items, loc="lower left", fontsize=8, framealpha=0.95,
              title="Legend", title_fontsize=9)

    # Equipment inventory panel
    tags = [e.get("tag") for e in entities if e.get("tag")]
    equip = [e for e in entities if e["type"] == "equipment"]
    inst = [e for e in entities if e["type"] == "instrument"]
    valves = [e for e in entities if e["type"] == "valve"]

    panel = (
        f"Extracted: {len(equip)} equipment  |  {len(inst)} instruments  |  {len(valves)} valves\n"
        f"Tags: {', '.join(sorted(set(tags))[:18])}{'...' if len(tags) > 18 else ''}"
    )
    ax.text(8, 0.35, panel, ha="center", va="center", fontsize=7.5, color="#475569",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#cbd5e1"))

    out_jpg.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_jpg, format="jpeg", bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=150)
    fig.savefig(out_pdf, format="pdf", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved: {out_jpg}")
    print(f"Saved: {out_pdf}")


def main() -> None:
    base = Path(__file__).parent
    json_path = base / "output" / "123_structured.json"
    out_jpg = base / "output" / "123_flowchart.jpg"
    out_pdf = base / "output" / "123_flowchart.pdf"

    entities = load_entities(json_path)
    draw_flowchart(entities, out_jpg, out_pdf)


if __name__ == "__main__":
    main()
