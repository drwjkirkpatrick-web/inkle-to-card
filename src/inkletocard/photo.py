"""photo.py - import photos: palettes from yarn, color matching, and
pattern grids from draft-chart images (v0.2).

Three jobs, one module:

1. extract_palette(photo) - the dominant colors of a yarn or fabric photo,
   each with a share of pixels and a human name, ready to paste into a draft.
   WHY: weavers photograph their stash; typing hex codes by eye is misery.
2. match_colors(swatches, palette) - map photo colors onto an existing
   draft's palette and report which palette colors the photo never shows.
   WHY: "which of MY yarns can weave this pattern?" is the real question.
3. import_grid(photo, cols) - read a 2-row draft chart from a photo (a book
   scan, another tool's screenshot) into a validated InkleDraft. The chart
   convention comes straight from the research (section 2): the top row holds
   heddled ends, the bottom row unhedled, and the warp order runs top then
   bottom per column - end 1 is top column 1, end 2 is bottom column 1...

Grid sampling samples the CENTRAL half of each cell, so grid lines and photo
margins are ignored; uniform photo borders are peeled automatically (up to
25% per side - a caveat: cells the same color as the page background at the
very edge can be peeled with the margin, so crop close to the grid).
"""
from __future__ import annotations

import math
from pathlib import Path

from .colors import suggest_name
from .models import DraftError, End, InkleDraft

try:
    from PIL import Image
    _HAS_PIL = True
except ImportError:  # pragma: no cover - exercised only without Pillow
    _HAS_PIL = False

_MAX_THUMB = 512            # analysis resolution - plenty for palette work
_AUTOCROP_LIMIT = 0.25      # peel at most 25% of each side as border
_AUTOCROP_BG_SHARE = 0.98   # a strip counts as background at >=98% match
_AUTOCROP_TOL = 30.0        # RGB distance that still counts as background
_CLOSE_MATCH = 90.0         # RGB distance under which a palette match is "close"
_MAX_PALETTE = 12           # distinct colors kept when importing a grid


def _require_pil() -> None:
    if not _HAS_PIL:
        raise ImportError(
            "photo import needs the Pillow library - run: python -m pip install pillow"
        )


def _load_rgb(path) -> "Image.Image":
    _require_pil()
    img = Image.open(Path(path))
    img = img.convert("RGB")
    if max(img.size) > _MAX_THUMB:
        img.thumbnail((_MAX_THUMB, _MAX_THUMB))
    return img


def _rgb_to_hex(rgb) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb[:3])


def _hex_to_rgb(hexv: str):
    return tuple(int(hexv[i:i + 2], 16) for i in (1, 3, 5))


def _distance(a, b) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a[:3], b[:3])))


def _unique_names(hexes) -> dict[str, str]:
    """hex -> human name: nearest common name, deduplicated with -2, -3..."""
    names: dict[str, str] = {}
    used: set[str] = set()
    for hexv in hexes:
        base = suggest_name(hexv)
        name, n = base, 2
        while name in used:
            name = f"{base}-{n}"
            n += 1
        used.add(name)
        names[hexv] = name
    return names


def extract_palette(path, n_colors: int = 6) -> list[dict]:
    """Dominant colors of a photo, share-descending.

    Returns [{'hex', 'name', 'share', 'rgb'}, ...] - the 'rgb' key feeds
    match_colors; JSON output uses only hex/name.
    """
    if not 1 <= n_colors <= 32:
        raise ValueError(f"n_colors must be 1..32, not {n_colors}")
    img = _load_rgb(path)
    quantized = img.convert("P", palette=Image.ADAPTIVE, colors=n_colors)
    # histogram() counts pixels per palette index - no deprecated getdata()
    hist = quantized.histogram()
    counts = {idx: count for idx, count in enumerate(hist) if count > 0}
    palette = quantized.getpalette()
    total = sum(counts.values())
    swatches = []
    for idx, count in counts.items():
        rgb = tuple(palette[idx * 3: idx * 3 + 3])
        swatches.append({"rgb": rgb, "hex": _rgb_to_hex(rgb), "share": count / total})
    swatches.sort(key=lambda s: -s["share"])
    names = _unique_names([s["hex"] for s in swatches])
    for s in swatches:
        s["name"] = names[s["hex"]]
    return swatches


def match_colors(swatches: list[dict], palette: dict[str, str]) -> dict:
    """Map photo swatches onto a draft palette; report unseen palette colors."""
    results = []
    covered: set[str] = set()
    for s in swatches:
        best_name = best_hex = None
        best_d = None
        for name, hexv in palette.items():
            d = _distance(s["rgb"], _hex_to_rgb(hexv))
            if best_d is None or d < best_d:
                best_name, best_hex, best_d = name, hexv, d
        close = best_d is not None and best_d <= _CLOSE_MATCH
        if close:
            covered.add(best_name)
        results.append(
            {
                "hex": s["hex"], "name": s["name"], "share": s["share"],
                "match": best_name, "match_hex": best_hex,
                "distance": round(best_d, 1) if best_d is not None else None,
                "close": close,
            }
        )
    missing = [name for name in palette if name not in covered]
    return {"matches": results, "missing": missing, "tolerance": _CLOSE_MATCH}


def _autocrop(img: "Image.Image") -> "Image.Image":
    """Peel uniform photo margins so grid sampling lands on the chart."""
    w, h = img.size
    px = img.load()
    bg = px[0, 0]

    def is_bg(p) -> bool:
        return _distance(p, bg) <= _AUTOCROP_TOL

    def strip_is_bg(coords) -> bool:
        samples = list(coords)
        if not samples:
            return False
        hit = sum(1 for p in samples if is_bg(p))
        return hit / len(samples) >= _AUTOCROP_BG_SHARE

    step = max(1, w // 96), max(1, h // 96)
    left = right = top = bottom = 0
    while top < int(h * _AUTOCROP_LIMIT) and strip_is_bg(
        px[x, top] for x in range(0, w, step[0])
    ):
        top += 1
    while bottom < int(h * _AUTOCROP_LIMIT) and strip_is_bg(
        px[x, h - 1 - bottom] for x in range(0, w, step[0])
    ):
        bottom += 1
    while left < int(w * _AUTOCROP_LIMIT) and strip_is_bg(
        px[left, y] for y in range(0, h, step[1])
    ):
        left += 1
    while right < int(w * _AUTOCROP_LIMIT) and strip_is_bg(
        px[w - 1 - right, y] for y in range(0, h, step[1])
    ):
        right += 1
    if top or left or bottom or right:
        img = img.crop((left, top, w - right, h - bottom))
    if img.size[0] < 8 or img.size[1] < 8:
        raise DraftError("photo appears to be blank (uniform background) - nothing to import")
    return img


def import_grid(path, cols: int, name: str | None = None) -> InkleDraft:
    """Import an inkle draft from a photo of its 2-row chart.

    Chart convention (research section 2): top row = heddled ends, bottom row
    = unhedled ends; warp order runs top/bottom per column, so end 1 is top
    column 1, end 2 is bottom column 1, and so on - 2 x cols ends in total.
    """
    _require_pil()
    if cols < 4:
        raise DraftError(
            f"a chart needs at least 4 columns (8 ends) - got {cols}"
        )
    img = _autocrop(_load_rgb(path))
    w, h = img.size
    rows = 2
    cell_w, cell_h = w / cols, h / rows
    margin_x, margin_y = cell_w * 0.25, cell_h * 0.25

    top_row: list[tuple] = []
    bottom_row: list[tuple] = []
    for r in range(rows):
        for c in range(cols):
            box = (
                int(c * cell_w + margin_x), int(r * cell_h + margin_y),
                int((c + 1) * cell_w - margin_x), int((r + 1) * cell_h - margin_y),
            )
            # 1x1 bilinear resize = area-weighted mean of the central region
            rgb = img.crop(box).resize((1, 1), Image.BILINEAR).getpixel((0, 0))
            (top_row if r == 0 else bottom_row).append(rgb)

    # distinct colors: bucket to 16-step channels, keep the most common ones
    buckets: dict[tuple, list[tuple]] = {}
    for rgb in list(top_row) + list(bottom_row):
        buckets.setdefault(tuple(v // 16 for v in rgb), []).append(rgb)
    ordered = sorted(buckets.values(), key=len, reverse=True)
    reps = [
        tuple(sum(ch) // len(group) for ch in zip(*group))
        for group in ordered[:_MAX_PALETTE]
    ]

    def snap(rgb):
        best, best_d = None, None
        for rep in reps:
            d = _distance(rgb, rep)
            if best_d is None or d < best_d:
                best, best_d = rep, d
        return best

    hexes: list[str] = []
    for rep in reps:
        hexv = _rgb_to_hex(rep)
        if hexv not in hexes:
            hexes.append(hexv)
    names = _unique_names(hexes)
    palette = {names[hexv]: hexv for hexv in hexes}

    ends: list[End] = []
    index = 0
    for c in range(cols):
        ends.append(End(index=index, color_name=names[_rgb_to_hex(snap(top_row[c]))],
                        heddled=True))
        index += 1
        ends.append(End(index=index, color_name=names[_rgb_to_hex(snap(bottom_row[c]))],
                        heddled=False))
        index += 1

    draft = InkleDraft(name=name or Path(path).stem, palette=palette, ends=ends)
    problems = draft.validate()
    if problems:
        raise DraftError(
            "photo grid does not yield a valid draft:\n- " + "\n- ".join(problems)
        )
    return draft
