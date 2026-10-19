"""Tests for the inkle draft parsers (Prompt 2).

Each test names the weaving-facing behavior it pins, including the exact
error wording a weaver would read.
"""
import json
from pathlib import Path

import pytest

from inkletocard.models import DraftError, End
from inkletocard.parsers import parse_draft, parse_inkle_json, parse_inkle_text

PALETTE = {"navy": "#1B2A4A", "cream": "#F5F0E6", "blue": "#3B6EA5", "gold": "#C9A227"}

TEXT_DRAFT = """# a comment line is allowed
name: Quiet Harbor 17

palette: navy #1B2A4A, cream #F5F0E6, blue #3B6EA5, gold #C9A227
ends: navy H | cream U | cream H | blue U | gold H | blue U | cream H | navy U
"""


def make_json_ends(n=8):
    colors = ["navy", "cream", "blue", "gold"]
    return [
        {"color": colors[i % len(colors)], "heddled": (i % 2 == 0)} for i in range(n)
    ]


class TestJsonShapeA:
    def test_ends_list_parses(self):
        draft = parse_inkle_json({"name": "d", "palette": PALETTE, "ends": make_json_ends(8)})
        assert draft.name == "d"
        assert len(draft.ends) == 8
        assert draft.ends[0] == End(index=0, color_name="navy", heddled=True)
        assert draft.ends[7].heddled is False

    def test_from_json_string(self):
        payload = json.dumps({"name": "d", "palette": PALETTE, "ends": make_json_ends(8)})
        draft = parse_inkle_json(payload)
        assert len(draft.ends) == 8

    def test_from_path(self, tmp_path):
        p = tmp_path / "draft.json"
        p.write_text(json.dumps({"name": "d", "palette": PALETTE, "ends": make_json_ends(8)}))
        assert len(parse_inkle_json(p).ends) == 8

    def test_from_path_string(self, tmp_path):
        p = tmp_path / "draft.json"
        p.write_text(json.dumps({"name": "d", "palette": PALETTE, "ends": make_json_ends(8)}))
        assert len(parse_inkle_json(str(p)).ends) == 8


class TestJsonShapeB:
    def test_order_with_explicit_heddles(self):
        draft = parse_inkle_json({
            "name": "d", "palette": PALETTE,
            "order": "navy cream cream blue gold cream navy cream",
            "heddles": "U H U H U H U H",
        })
        assert [e.color_name for e in draft.ends] == [
            "navy", "cream", "cream", "blue", "gold", "cream", "navy", "cream",
        ]
        # NOTE: a U-first warp is just as valid as H-first; explicit heddles win.
        assert [e.heddled for e in draft.ends] == [False, True, False, True, False, True, False, True]

    def test_order_without_heddles_alternates_from_heddled(self):
        draft = parse_inkle_json({
            "name": "d", "palette": PALETTE,
            "order": "navy cream blue gold cream navy cream gold",
        })
        assert [e.heddled for e in draft.ends] == [True, False] * 4

    def test_length_mismatch_reports_both_counts(self):
        with pytest.raises(DraftError, match="4 colors but 'heddles' has 3"):
            parse_inkle_json({"name": "d", "palette": PALETTE,
                              "order": "navy cream cream blue", "heddles": "H U U"})

    def test_ends_and_order_rejected_together(self):
        with pytest.raises(DraftError, match="not both"):
            parse_inkle_json({"name": "d", "palette": PALETTE,
                              "ends": make_json_ends(8), "order": "navy cream"})


class TestJsonErrors:
    def test_invalid_json_reports_line_and_column(self):
        with pytest.raises(DraftError, match="invalid JSON at line 1, column 2"):
            parse_inkle_json("{not json")

    def test_missing_name(self):
        with pytest.raises(DraftError, match="missing the 'name'"):
            parse_inkle_json({"palette": PALETTE, "ends": make_json_ends(8)})

    def test_missing_palette(self):
        with pytest.raises(DraftError, match="missing the 'palette'"):
            parse_inkle_json({"name": "d", "ends": make_json_ends(8)})

    def test_missing_warp(self):
        with pytest.raises(DraftError, match="use 'ends' .list. or 'order'"):
            parse_inkle_json({"name": "d", "palette": PALETTE})

    def test_neither_json_nor_file(self):
        with pytest.raises(DraftError, match="neither JSON text"):
            parse_inkle_json("no-such-file.json")


class TestTextFormat:
    def test_happy_path_with_comments_and_blanks(self):
        draft = parse_inkle_text(TEXT_DRAFT)
        assert draft.name == "Quiet Harbor 17"
        assert draft.palette == PALETTE
        assert len(draft.ends) == 8
        assert draft.ends[2] == End(index=2, color_name="cream", heddled=True)

    def test_lowercase_flags_accepted(self):
        text = ("name: d\npalette: navy #1B2A4A, cream #F5F0E6\n"
                "ends: navy h | cream u | navy h | cream u | navy h | cream u | navy h | cream u")
        assert len(parse_inkle_text(text).ends) == 8

    def test_unknown_directive_reports_line_number(self):
        with pytest.raises(DraftError, match="line 2.*unknown directive 'width'"):
            parse_inkle_text("name: d\nwidth: 3 inches\npalette: navy #1B2A4A\nends: navy H")

    def test_missing_ends_line(self):
        with pytest.raises(DraftError, match="missing the 'ends:' line"):
            parse_inkle_text("name: d\npalette: navy #1B2A4A")

    def test_bad_flag_token_reports_entry_and_valid_flags(self):
        with pytest.raises(DraftError, match="flag 'X' must be H .heddled. or U .open"):
            parse_inkle_text(
                "name: d\npalette: navy #1B2A4A, cream #F5F0E6\n"
                "ends: navy H | cream X | navy H | cream U | navy H | cream U | navy H | cream U"
            )

    def test_duplicate_name_directive(self):
        with pytest.raises(DraftError, match="duplicate 'name:'"):
            parse_inkle_text("name: d\nname: d2\npalette: navy #1B2A4A\nends: navy H")

    def test_palette_entry_needs_two_tokens(self):
        with pytest.raises(DraftError, match="must be '<color> <#hex>'"):
            parse_inkle_text(
                "name: d\npalette: navy#1B2A4A, cream #F5F0E6\nends: navy H | cream U"
            )


class TestValidationIntegration:
    """Both parsers must run validate() and surface its problems."""

    def test_unknown_color_lists_palette_keys(self):
        with pytest.raises(DraftError, match="chartreuse.*gold.*navy"):
            parse_inkle_json({"name": "d", "palette": PALETTE,
                              "order": "navy chartreuse", "heddles": "H U"})

    def test_bad_hex_reported(self):
        bad = dict(PALETTE, cream="F5F0E6")
        with pytest.raises(DraftError, match="invalid hex"):
            parse_inkle_json({"name": "d", "palette": bad, "ends": make_json_ends(8)})

    def test_non_alternating_heddles_reported(self):
        ends = make_json_ends(8)
        ends[1]["heddled"] = True  # two heddled ends in a row
        with pytest.raises(DraftError, match="alternate"):
            parse_inkle_json({"name": "d", "palette": PALETTE, "ends": ends})

    def test_empty_ends_reported(self):
        with pytest.raises(DraftError, match="at least 8"):
            parse_inkle_json({"name": "d", "palette": PALETTE, "ends": []})


class TestParseDraftSniffing:
    def test_sniffs_json_string(self):
        payload = json.dumps({"name": "d", "palette": PALETTE, "ends": make_json_ends(8)})
        assert len(parse_draft(payload).ends) == 8

    def test_sniffs_text_string(self):
        assert parse_draft(TEXT_DRAFT).name == "Quiet Harbor 17"

    def test_sniffs_json_and_text_files(self, tmp_path):
        j = tmp_path / "a.json"
        j.write_text(json.dumps({"name": "d", "palette": PALETTE, "ends": make_json_ends(8)}))
        tfile = tmp_path / "b.inkle"
        tfile.write_text(TEXT_DRAFT)
        assert len(parse_draft(j).ends) == 8
        assert parse_draft(tfile).name == "Quiet Harbor 17"

    def test_unrecognizable_input(self):
        with pytest.raises(DraftError, match="could not detect draft format"):
            parse_draft("just some words with no directives")
