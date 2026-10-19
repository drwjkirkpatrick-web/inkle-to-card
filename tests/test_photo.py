"""Tests for photo import: palette extraction, color matching, grid import,
and the palette / import-grid CLI commands (v0.2).

Skips cleanly when Pillow is not installed (house importorskip pattern).
"""
import json

import pytest

pytest.importorskip("PIL")
from PIL import Image, ImageDraw  # noqa: E402

from inkletocard.cli import main  # noqa: E402
from inkletocard.models import DraftError  # noqa: E402
from inkletocard.parsers import parse_inkle_json  # noqa: E402
from inkletocard.photo import extract_palette, import_grid, match_colors  # noqa: E402

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GOLD = (201, 162, 39)
BG = (250, 250, 250)  # near-white photo background, deliberately not pure white


def make_stripes(path, colors, stripe_w=30, height=60):
    img = Image.new("RGB", (stripe_w * len(colors), height), colors[0])
    draw = ImageDraw.Draw(img)
    for i, color in enumerate(colors):
        draw.rectangle([i * stripe_w, 0, (i + 1) * stripe_w - 1, height - 1], fill=color)
    img.save(str(path))


def make_grid(path, cols, top, bottom, cell=24, border=0, bg=BG):
    img = Image.new("RGB", (cols * cell + 2 * border, 2 * cell + 2 * border), bg)
    draw = ImageDraw.Draw(img)
    for c in range(cols):
        draw.rectangle([border + c * cell, border,
                        border + (c + 1) * cell - 1, border + cell - 1], fill=top[c])
        draw.rectangle([border + c * cell, border + cell,
                        border + (c + 1) * cell - 1, border + 2 * cell - 1], fill=bottom[c])
    img.save(str(path))


class TestExtractPalette:
    def test_three_stripes(self, tmp_path):
        photo = tmp_path / "yarn.png"
        make_stripes(photo, [BLACK, WHITE, GOLD])
        swatches = extract_palette(photo, n_colors=3)
        assert len(swatches) == 3
        by_hex = {s["hex"]: s for s in swatches}
        assert "#000000" in by_hex and "#FFFFFF" in by_hex and "#C9A227" in by_hex
        # #C9A227 sits nearest CSS "orange" (255,165,0), not "gold" (255,215,0)
        assert {by_hex["#000000"]["name"], by_hex["#FFFFFF"]["name"],
                by_hex["#C9A227"]["name"]} == {"black", "white", "orange"}
        for s in swatches:
            assert 0.25 < s["share"] < 0.40

    def test_n_colors_bounds(self, tmp_path):
        photo = tmp_path / "yarn.png"
        make_stripes(photo, [BLACK, WHITE])
        with pytest.raises(ValueError, match="1..32"):
            extract_palette(photo, n_colors=0)
        with pytest.raises(ValueError, match="1..32"):
            extract_palette(photo, n_colors=40)


class TestMatchColors:
    def test_exact_close_and_missing(self):
        swatches = [
            {"hex": "#1B2A4A", "rgb": (27, 42, 74), "name": "a", "share": 0.4},
            {"hex": "#1E3250", "rgb": (30, 50, 80), "name": "b", "share": 0.3},
            {"hex": "#FF0000", "rgb": RED, "name": "c", "share": 0.3},
        ]
        palette = {"navy": "#1B2A4A", "cream": "#F5F0E6"}
        report = match_colors(swatches, palette)
        assert report["matches"][0]["match"] == "navy"
        assert report["matches"][0]["distance"] == 0.0
        assert report["matches"][0]["close"] is True
        assert report["matches"][1]["close"] is True   # near-navy, still close
        assert report["matches"][2]["close"] is False  # red is far from everything
        assert report["missing"] == ["cream"]         # cream never appears


class TestImportGrid:
    def make_photo(self, tmp_path, border=0, name="chart.png", bg=BG):
        photo = tmp_path / name
        make_grid(photo, cols=8, top=[BLACK, WHITE] * 4, bottom=[RED, WHITE] * 4,
                  border=border, bg=bg)
        return photo

    def test_two_row_chart_reads_draft(self, tmp_path):
        draft = import_grid(self.make_photo(tmp_path), cols=8)
        assert draft.name == "chart"
        assert len(draft.ends) == 16
        assert [e.heddled for e in draft.ends] == [True, False] * 8
        assert draft.palette == {"black": "#000000", "white": "#FFFFFF", "red": "#FF0000"}
        # warp order: end 1 = top col 1 (heddled), end 2 = bottom col 1 (open)
        assert draft.ends[0].color_name == "black"
        assert draft.ends[1].color_name == "red"
        assert draft.ends[2].color_name == "white"
        assert draft.ends[3].color_name == "white"
        assert draft.validate() == []

    def test_round_trips_through_json(self, tmp_path):
        draft = import_grid(self.make_photo(tmp_path), cols=8)
        rebuilt = parse_inkle_json(draft.to_dict())
        assert rebuilt == draft

    def test_autocrop_peels_photo_margins(self, tmp_path):
        # green "paper" - unlike any cell color, so the white edge column is
        # not mistaken for background (the documented edge-cell caveat)
        paper = (60, 180, 90)
        bordered = import_grid(
            self.make_photo(tmp_path, border=16, name="bordered.png", bg=paper), cols=8)
        tight = import_grid(
            self.make_photo(tmp_path, border=0, name="tight.png", bg=paper), cols=8)
        assert bordered.palette == tight.palette
        assert [e.color_name for e in bordered.ends] == [e.color_name for e in tight.ends]

    def test_too_few_columns(self, tmp_path):
        with pytest.raises(DraftError, match="at least 4 columns"):
            import_grid(self.make_photo(tmp_path), cols=2)

    def test_name_override(self, tmp_path):
        draft = import_grid(self.make_photo(tmp_path), cols=8, name="my-chart")
        assert draft.name == "my-chart"


class TestPhotoCli:
    def test_palette_command_writes_json(self, tmp_path, capsys):
        photo = tmp_path / "yarn.png"
        make_stripes(photo, [BLACK, WHITE])
        out = tmp_path / "palette.json"
        assert main(["palette", str(photo), "--colors", "2", "-o", str(out)]) == 0
        captured = capsys.readouterr().out
        assert "photo palette (2 colors)" in captured
        assert "paste into a text draft" in captured
        assert json.loads(out.read_text()) == {"black": "#000000", "white": "#FFFFFF"}

    def test_palette_match_reports_missing(self, tmp_path, capsys):
        photo = tmp_path / "yarn.png"
        make_stripes(photo, [RED, WHITE])
        draft = tmp_path / "belt.json"
        draft.write_text(json.dumps({
            "name": "belt", "palette": {"navy": "#1B2A4A", "cream": "#F5F0E6"},
            "order": "navy cream navy cream navy cream navy cream",
        }))
        assert main(["palette", str(photo), "--colors", "2", "--match", str(draft)]) == 0
        out = capsys.readouterr().out
        assert "matched against" in out
        assert "not seen in photo" in out and "navy" in out

    def test_import_grid_command_end_to_end(self, tmp_path, capsys):
        photo = tmp_path / "chart.png"
        make_grid(photo, cols=8, top=[BLACK, WHITE] * 4, bottom=[RED, WHITE] * 4)
        pdf = tmp_path / "chart.pdf"
        saved = tmp_path / "chart.json"
        assert main(["import-grid", str(photo), "--cols", "8",
                     "-o", str(pdf), "--save-draft", str(saved)]) == 0
        captured = capsys.readouterr().out
        assert "16 cards" in captured
        assert pdf.read_bytes()[:4] == b"%PDF"
        assert "draft saved" in captured
        assert parse_inkle_json(json.loads(saved.read_text())).name == "chart"

    def test_import_grid_no_pdf_mode(self, tmp_path, capsys):
        photo = tmp_path / "chart.png"
        make_grid(photo, cols=8, top=[BLACK, WHITE] * 4, bottom=[RED, WHITE] * 4)
        assert main(["import-grid", str(photo), "--cols", "8", "--no-pdf"]) == 0
        out = capsys.readouterr().out
        assert "16 cards" in out
        assert "legend:" in out
