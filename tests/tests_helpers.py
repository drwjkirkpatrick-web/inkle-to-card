"""Shared test fixtures for the inkletocard suite."""
from inkletocard.models import End, InkleDraft

PALETTE = {"navy": "#1B2A4A", "cream": "#F5F0E6", "blue": "#3B6EA5", "gold": "#C9A227"}


def small_draft(n_ends=17, colors=None):
    colors = colors or ["navy", "cream", "blue", "gold"]
    ends = [
        End(index=i, color_name=colors[i % len(colors)], heddled=(i % 2 == 0))
        for i in range(n_ends)
    ]
    return InkleDraft(name="quiet-harbor-17", palette=PALETTE, ends=ends)
