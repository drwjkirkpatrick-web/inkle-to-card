"""Tests for pattern import (Prompt 12 / v0.3): the TDD .tdd format.

Fixtures are written in the .tdd format itself (built with chr(92) to keep
backslashes unambiguous in this file).
"""
import json

import pytest

from inkletocard.cli import main
from inkletocard.importers import ImportedPattern, deck_to_draft, import_tdd
from inkletocard.models import DraftError, ThreadingDirection, Turn
from inkletocard.parsers import parse_inkle_json
from inkletocard.report import materials_report
from inkletocard.turning import TWIST_WARN_THRESHOLD  # noqa: F401 (import sanity)

BS = chr(92)   # backslash
FS = "/"


def tdd_text(turning=None, threading=None, sz="ZZZZSSSS", palette=None,
             comments=("# tdd v0.1", "# fixture")):
    turning = turning if turning is not None else [BS * 4 + FS * 4] * 4 + [FS * 4 + BS * 4] * 4
    threading = threading if threading is not None else ["00111100"] * 4
    palette = palette if palette is not None else ["0 - #000000", "1 - #FFFFFF"]
    return "\n".join(list(comments) + turning + [""] + threading + [sz] + [""] + palette) + "\n"


def write_tdd(tmp_path, text, name="band.tdd"):
    p = tmp_path / name
    p.write_text(text)
    return p


class TestImportTdd:
    def test_simple_import(self, tmp_path):
        imported = import_tdd(write_tdd(tmp_path, tdd_text()))
        deck, draft = imported.deck, imported.draft
        assert isinstance(imported, ImportedPattern)
        assert deck.mapping == "TDD"
        assert deck.draft_name == "band"
        assert len(deck.cards) == 8
        assert [c.threading for c in deck.cards[:4]] == [ThreadingDirection.Z] * 4
        assert [c.threading for c in deck.cards[4:]] == [ThreadingDirection.S] * 4
        # card 1 (digit 0) all holes black; card 3 (digit 1) all holes white
        assert set(deck.cards[0].hole_colors.values()) == {"black"}
        assert set(deck.cards[2].hole_colors.values()) == {"white"}
        assert deck.picks and len(deck.picks) == 8

    def test_turn_semantics_home_slash_is_forward(self, tmp_path):
        # A row of all backslashes: Z cards (home '\') turn forward, S cards turn backward.
        imported = import_tdd(write_tdd(tmp_path, tdd_text(turning=[BS * 8])))
        turns = imported.deck.picks[0].turns
        assert turns == [Turn.F] * 4 + [Turn.B] * 4

    def test_4f4b_rows(self, tmp_path):
        imported = import_tdd(write_tdd(tmp_path, tdd_text()))
        assert all(t is Turn.F for t in imported.deck.picks[0].turns)
        assert all(t is Turn.B for t in imported.deck.picks[4].turns)

    def test_hole_row_order_flag(self, tmp_path):
        threading = ["00000000", "11111111", "22222222", "33333333"]
        palette = ["0 - #000000", "1 - #FFFFFF", "2 - #FF0000", "3 - #0000FF"]
        text = tdd_text(turning=[BS * 8], threading=threading, sz="SSSSSSSS",
                        palette=palette)
        default = import_tdd(write_tdd(tmp_path, text, name="a.tdd"), hole_rows="ABCD")
        flipped = import_tdd(write_tdd(tmp_path, text, name="b.tdd"), hole_rows="DCBA")
        assert default.deck.cards[0].hole_colors["A"] == "black"
        assert flipped.deck.cards[0].hole_colors["A"] == "blue"   # row 3 is now hole A

    def test_dropped_holes_filled_with_warning(self, tmp_path):
        threading = ["01111110", "010  010", "010  010", "01111110"]
        imported = import_tdd(write_tdd(tmp_path, tdd_text(threading=threading)))
        assert any("Dropped-hole technique" in w for w in imported.deck.warnings)
        # "010  010" drops holes at cards 4-5: card 4 has B and C empty,
        # filled with its remaining color (white, from digit 1)
        card = imported.deck.cards[3]
        assert set(card.hole_colors.values()) == {"white"}

    def test_reverse_draft_counts_feed_materials(self, tmp_path):
        imported = import_tdd(write_tdd(tmp_path, tdd_text()))
        assert len(imported.draft.ends) == 32  # 8 cards x 4 holes
        assert imported.draft.validate() == []
        mats = materials_report(imported.deck, imported.draft)
        assert mats["threads_per_color"] == {"black": 16, "white": 16}

    def test_import_warnings_state_assumptions(self, tmp_path):
        imported = import_tdd(write_tdd(tmp_path, tdd_text()))
        assert any("ABCD" in w and "forward turn" in w for w in imported.deck.warnings)


class TestTddErrors:
    def test_bad_palette_line(self, tmp_path):
        with pytest.raises(DraftError, match="expected 'N - #rrggbb'"):
            import_tdd(write_tdd(tmp_path, tdd_text(palette=["black - #000000"])))

    def test_unknown_color_digit(self, tmp_path):
        with pytest.raises(DraftError, match="not in the palette"):
            import_tdd(write_tdd(tmp_path, tdd_text(threading=["99999999"] * 4)))

    def test_row_length_mismatch(self, tmp_path):
        with pytest.raises(DraftError, match="one character per card"):
            import_tdd(write_tdd(tmp_path, tdd_text(threading=["0011110"] * 4)))

    def test_bad_sz_row(self, tmp_path):
        with pytest.raises(DraftError, match="S or Z for every card"):
            import_tdd(write_tdd(tmp_path, tdd_text(sz="ZZZZXXXX")))

    def test_wrong_block_count(self, tmp_path):
        with pytest.raises(DraftError, match="3 blocks"):
            import_tdd(write_tdd(tmp_path, tdd_text().replace("\n0 - #000000\n1 - #FFFFFF\n", "")))

    def test_bad_hole_order_argument(self, tmp_path):
        with pytest.raises(ValueError, match="ABCD or DCBA"):
            import_tdd(write_tdd(tmp_path, tdd_text()), hole_rows="ABX")


class TestTddCli:
    def test_import_tdd_end_to_end(self, tmp_path, capsys):
        f = write_tdd(tmp_path, tdd_text())
        pdf = tmp_path / "band.pdf"
        saved = tmp_path / "band.json"
        assert main(["import-tdd", str(f), "-o", str(pdf), "--save-draft", str(saved)]) == 0
        out = capsys.readouterr().out
        assert "8 cards" in out and "TDD" in out
        assert pdf.read_bytes()[:4] == b"%PDF"
        assert parse_inkle_json(json.loads(saved.read_text())).name == "band"

    def test_import_tdd_no_pdf_mode(self, tmp_path, capsys):
        f = write_tdd(tmp_path, tdd_text())
        assert main(["import-tdd", str(f), "--no-pdf"]) == 0
        out = capsys.readouterr().out
        assert "Card 1: A=black" in out
        assert "legend:" in out

    def test_import_tdd_holes_flag_reaches_deck(self, tmp_path, capsys):
        threading = ["00000000", "11111111", "22222222", "33333333"]
        palette = ["0 - #000000", "1 - #FFFFFF", "2 - #FF0000", "3 - #0000FF"]
        f = write_tdd(tmp_path, tdd_text(turning=[BS * 8], threading=threading,
                                         sz="SSSSSSSS", palette=palette))
        assert main(["import-tdd", str(f), "--holes", "DCBA", "--no-pdf"]) == 0
        assert "Card 1: A=blue" in capsys.readouterr().out

    def test_import_tdd_missing_file_fails_cleanly(self, capsys):
        assert main(["import-tdd", "/no/such/band.tdd"]) == 1
        assert "error:" in capsys.readouterr().err
