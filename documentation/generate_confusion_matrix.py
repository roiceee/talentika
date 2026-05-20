"""
Generate the confusion matrix figure used in the validation section of the
paper. Compares manual (human) labels against the AI's classifications on the
30 résumé validation sample, with rows representing the human judgment and
columns representing the AI judgment.

Edit the MATRIX constant below if the real tallies differ from the seeded
sample, then re-run.

Usage:
    python documentation/generate_confusion_matrix.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

LABELS = ["Suitable", "Potentially\nSuitable", "Unsuitable"]

# Rows: human (manual) judgment.   Columns: AI judgment.
# MATRIX[i][j] = number of résumés the human labeled as LABELS[i]
# and the AI labeled as LABELS[j].
MATRIX = np.array([
    [9, 1, 0],   # Human: Suitable
    [0, 9, 1],   # Human: Potentially Suitable
    [0, 1, 9],   # Human: Unsuitable
])

HUMAN_COLOR = "#C0392B"   # red for the human axis
AI_COLOR    = "#1F4E79"   # navy for the AI axis
DIAG_EDGE   = "#27AE60"   # green outline for agreement (diagonal)
OUTPUT_FILE = Path(__file__).parent / "confusion_matrix.png"


def main() -> None:
    n = len(LABELS)
    totals_per_row = MATRIX.sum(axis=1)
    accuracy = np.trace(MATRIX) / MATRIX.sum()

    fig, ax = plt.subplots(figsize=(8, 6.5))
    im = ax.imshow(MATRIX, cmap="Blues", vmin=0, vmax=MATRIX.max() + 1)

    # Axis ticks + labels
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(LABELS, fontsize=10)
    ax.set_yticklabels(LABELS, fontsize=10)

    ax.set_xlabel("AI Judgment", fontsize=13, fontweight="bold",
                  color=AI_COLOR, labelpad=10)
    ax.set_ylabel("Human Judgment", fontsize=13, fontweight="bold",
                  color=HUMAN_COLOR, labelpad=10)

    # Color the tick labels to match the axis they belong to
    for label in ax.get_xticklabels():
        label.set_color(AI_COLOR)
    for label in ax.get_yticklabels():
        label.set_color(HUMAN_COLOR)

    # Number annotation in each cell
    threshold = MATRIX.max() / 2
    for i in range(n):
        for j in range(n):
            count = MATRIX[i, j]
            pct = (count / totals_per_row[i] * 100) if totals_per_row[i] else 0
            color = "white" if count > threshold else "#222222"
            ax.text(j, i - 0.08, str(count), ha="center", va="center",
                    color=color, fontsize=22, fontweight="bold")
            ax.text(j, i + 0.28, f"{pct:.0f}%", ha="center", va="center",
                    color=color, fontsize=9)

    # Outline the diagonal (cells where AI agrees with the human)
    for i in range(n):
        ax.add_patch(Rectangle((i - 0.5, i - 0.5), 1, 1,
                               fill=False, edgecolor=DIAG_EDGE,
                               linewidth=3, zorder=5))

    # Title + accuracy line
    ax.set_title(
        f"Human vs AI Classification (n = {MATRIX.sum()})\n"
        f"Overall accuracy: {accuracy:.1%}",
        fontsize=13, fontweight="bold", pad=14,
    )

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Count", fontsize=10)

    # Cosmetic: hide spines, add light grid between cells
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)

    # Legend explaining the green outline
    legend_handles = [
        Rectangle((0, 0), 1, 1, fill=False, edgecolor=DIAG_EDGE, linewidth=2,
                  label="Agreement (diagonal)"),
    ]
    ax.legend(handles=legend_handles, loc="lower right",
              bbox_to_anchor=(1.0, -0.18), frameon=False, fontsize=9)

    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=220, bbox_inches="tight")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
