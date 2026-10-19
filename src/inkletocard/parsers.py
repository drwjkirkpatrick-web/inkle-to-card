"""parsers.py - read inkle drafts from JSON or the plain "ends:" text format.

WHY two formats: JSON is what programs (and the bundled pattern files) use;
the text format is what a weaver can type at the loom table without learning
JSON syntax. Both produce the same validated InkleDraft from models.py.

THE TEXT FORMAT - one directive per line; whole-line comments start with #:

    name: Quiet Harbor 17
    palette: navy #1B2A4A, cream #F5F0E6, blue #3B6EA5, gold #C9A227
    ends: navy H | cream U | cream U | blue H | gold U

Each end token is `<color> <H|U>`: H = heddled (top row of the draft grid,
threaded on a string heddle), U = unhedled/open (bottom row). Heddled and open
ends must alternate - that alternation is the inkle structure itself.

THE JSON FORMAT accepts two shapes for the warp:

    {"name": ..., "palette": {...},
     "ends": [{"color": "navy", "heddled": true}, ...]}

or the compact form (heddles optional - when omitted, ends alternate starting
with a heddled end):

    {"name": ..., "palette": {...},
     "order": "navy cream cream", "heddles": "H U U"}

Every failure raises DraftError with the offending context - a line number
for text drafts, a key name for JSON - so a weaver can fix the draft in one
pass instead of one exception per run.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from .models import DraftError, End, InkleDraft

# A directive line looks like "name: ..." / "palette: ..." / "ends: ...".
_DIRECTIVE_RE = re.compile(r"^([A-Za-z][A-Za-z _-]*):\s*(.*)$")

# H = heddled (on a string heddle), U = unheddled / open.
_HU = {"H": True, "U": False}


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------

def _validate_or_raise(draft: InkleDraft) -> InkleDraft:
    """Run the draft's full validation and turn problems into one DraftError.

    WHY one error with all problems: loom-side mistakes are fixed faster when
    the weaver sees every issue at once (see models.InkleDraft.validate).
    """
    problems = draft.validate()
    if problems:
        raise DraftError(f"invalid draft {draft.name!r}:\n- " + "\n- ".join(problems))
    return draft


def _read_file(path: Path) -> str:
    try:
        return path.read_text()
    except OSError as exc:
        raise DraftError(f"cannot read {path}: {exc}") from None


def _load_json_text(source: Any) -> str:
    """Accept JSON text, a Path, or a string path to a JSON file."""
    if isinstance(source, Path):
        return _read_file(source)
    if isinstance(source, str):
        if source.lstrip().startswith("{"):
            return source
        if os.path.isfile(source):
            return _read_file(Path(source))
        raise DraftError(
            "source is neither JSON text (must start with '{') nor an existing file path"
        )
    raise DraftError(f"cannot load a JSON draft from {type(source).__name__}")


# ---------------------------------------------------------------------------
# JSON parser
# ---------------------------------------------------------------------------

def _ends_from_json(data: dict) -> list[End]:
    """Build the ordered end list from either JSON warp shape."""
    if "ends" in data and "order" in data:
        raise DraftError("use either 'ends' or 'order', not both")

    if "ends" in data:
        raw = data["ends"]
        if not isinstance(raw, list):
            raise DraftError("'ends' must be a list of {color, heddled} objects")
        ends: list[End] = []
        for i, item in enumerate(raw):
            if not isinstance(item, dict):
                raise DraftError(f"ends[{i}] must be an object with 'color' and 'heddled'")
            color = item.get("color") or item.get("color_name")
            if not isinstance(color, str) or not color.strip():
                raise DraftError(
                    f"ends[{i}] is missing 'color' (or 'color_name', as saved by --save-draft)"
                )
            heddled = item.get("heddled")
            if not isinstance(heddled, bool):
                raise DraftError(f"ends[{i}].heddled must be true or false")
            ends.append(End(index=i, color_name=color.strip(), heddled=heddled))
        return ends

    if "order" in data:
        colors = str(data["order"]).split()
        if not colors:
            raise DraftError("'order' has no color names")
        raw_heddles = data.get("heddles")
        if raw_heddles is None:
            # NOTE: default warp = alternating, first end heddled. A 17-end
            # starter woven this way gives 9 H / 8 U - the classic inkle shape.
            flags = [i % 2 == 0 for i in range(len(colors))]
        else:
            tokens = str(raw_heddles).split()
            if len(tokens) != len(colors):
                raise DraftError(
                    f"'order' has {len(colors)} colors but 'heddles' has {len(tokens)} flags"
                )
            flags = []
            for i, tok in enumerate(tokens):
                key = tok.strip().upper()
                if key not in _HU:
                    raise DraftError(
                        f"heddles[{i}] is {tok!r}; expected H (heddled) or U (open)"
                    )
                flags.append(_HU[key])
        return [End(index=i, color_name=c, heddled=flags[i]) for i, c in enumerate(colors)]

    raise DraftError("JSON draft needs warp threads: use 'ends' (list) or 'order' (string)")


def parse_inkle_json(source: Any) -> InkleDraft:
    """Parse a JSON inkle draft from JSON text, a file path, a Path, or a dict."""
    if isinstance(source, dict):
        data = source
    else:
        try:
            data = json.loads(_load_json_text(source))
        except json.JSONDecodeError as exc:
            raise DraftError(
                f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
            ) from None
    if not isinstance(data, dict):
        raise DraftError("JSON draft must be an object with 'name', 'palette' and warp keys")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise DraftError("JSON draft is missing the 'name' key")
    palette = data.get("palette")
    if not isinstance(palette, dict) or not palette:
        raise DraftError("JSON draft is missing the 'palette' object (color name -> #hex)")
    palette = {str(k): str(v) for k, v in palette.items()}
    ends = _ends_from_json(data)
    return _validate_or_raise(InkleDraft(name=name.strip(), palette=palette, ends=ends))


# ---------------------------------------------------------------------------
# text parser
# ---------------------------------------------------------------------------

def parse_inkle_text(text: Any) -> InkleDraft:
    """Parse the plain 'name:/palette:/ends:' text format into an InkleDraft."""
    if isinstance(text, Path):
        text = _read_file(text)

    name: str | None = None
    palette: dict[str, str] | None = None
    ends_value: str | None = None
    ends_line = 0

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue  # blank line or whole-line comment
        match = _DIRECTIVE_RE.match(line)
        if not match:
            raise DraftError(
                f"line {lineno}: expected 'name:', 'palette:' or 'ends:' - got {line[:40]!r}"
            )
        key = match.group(1).strip().lower()
        value = match.group(2).strip()

        if key == "name":
            if name is not None:
                raise DraftError(f"line {lineno}: duplicate 'name:' directive")
            if not value:
                raise DraftError(f"line {lineno}: 'name:' has no value")
            name = value

        elif key == "palette":
            if palette is not None:
                raise DraftError(f"line {lineno}: duplicate 'palette:' directive")
            palette = {}
            entries = [e.strip() for e in value.split(",") if e.strip()]
            if not entries:
                raise DraftError(f"line {lineno}: 'palette:' has no entries")
            for entry in entries:
                parts = entry.split()
                if len(parts) != 2:
                    raise DraftError(
                        f"line {lineno}: palette entry {entry[:30]!r} must be "
                        "'<color> <#hex>' (no spaces inside color names)"
                    )
                if parts[0] in palette:
                    raise DraftError(f"line {lineno}: duplicate palette color {parts[0]!r}")
                palette[parts[0]] = parts[1]

        elif key == "ends":
            if ends_value is not None:
                raise DraftError(f"line {lineno}: duplicate 'ends:' directive")
            ends_value = value
            ends_line = lineno

        else:
            raise DraftError(
                f"line {lineno}: unknown directive {key!r} (expected name, palette, or ends)"
            )

    if name is None:
        raise DraftError("text draft is missing the 'name:' line")
    if palette is None:
        raise DraftError("text draft is missing the 'palette:' line")
    if ends_value is None:
        raise DraftError("text draft is missing the 'ends:' line")

    ends: list[End] = []
    tokens = [t.strip() for t in ends_value.split("|") if t.strip()]
    for i, token in enumerate(tokens):
        parts = token.split()
        if len(parts) != 2:
            raise DraftError(
                f"ends entry {i + 1} (line {ends_line}): {token[:30]!r} must be '<color> <H|U>'"
            )
        color, flag = parts
        key = flag.upper()
        if key not in _HU:
            raise DraftError(
                f"ends entry {i + 1} (line {ends_line}): flag {flag!r} "
                "must be H (heddled) or U (open)"
            )
        ends.append(End(index=i, color_name=color, heddled=_HU[key]))

    return _validate_or_raise(InkleDraft(name=name, palette=palette, ends=ends))


# ---------------------------------------------------------------------------
# format sniffing (used by the CLI)
# ---------------------------------------------------------------------------

def parse_draft(source: Any) -> InkleDraft:
    """Parse a draft from any supported input, sniffing the format.

    Rules of thumb: dicts and anything starting with '{' are JSON; a file
    path ending in .json is JSON; everything else with an 'ends:' line is
    the text format.
    """
    if isinstance(source, dict):
        return parse_inkle_json(source)
    if isinstance(source, Path):
        if source.suffix.lower() == ".json":
            return parse_inkle_json(source)
        return parse_inkle_text(_read_file(source))
    if isinstance(source, str):
        if source.lstrip().startswith("{"):
            return parse_inkle_json(source)
        if os.path.isfile(source):
            path = Path(source)
            if path.suffix.lower() == ".json":
                return parse_inkle_json(path)
            return parse_inkle_text(_read_file(path))
        if "ends:" in source:
            return parse_inkle_text(source)
        raise DraftError(
            "could not detect draft format: not JSON, not an existing file, "
            "and no 'ends:' directive"
        )
    raise DraftError(f"cannot parse a draft from {type(source).__name__}")
