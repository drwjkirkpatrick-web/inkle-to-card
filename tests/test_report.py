"""Tests for the PDF report, part 1 (Prompt 7).

Reportlab is a hard dependency of the project, but the suite still skips
cleanly if someone runs it in an environment without it.
"""
import pytest

pytest.importorskip("reportlab")

from inkletocard.engine import convert_draft
from inkletocard.report import (
    build_pdf,
    deck_summary_rows,
    start_position_text,
    threading_table_data,
    title_block_data,
)
from inkletocard.turning import gen_4f4b, attach_turning
from tests_helpers import small_draft


def make_deck(mapping="A", n=17):
    draft = small_draft(n)
    deck = convert_draft(draft, mapping=mapping)
    attach_turning(deck, gen_4f4b(len(deck.cards)))
    return deck, draft


class TestBuilders:
    def test_title_block_counts(self):
        deck, draft = make_deck()
        data = title_block_data(deck, draft)
        assert data["draft_name"] == "quiet-harbor-17"
        assert data["mapping"] == "A"
        assert data["cards"] == 17
        assert data["ends"] == 17
        assert data["hole_labels"] == ["A", "B", "C", "D"]
        assert data["picks"] == 8

    def test_threading_table_data(self):
        deck, draft = make_deck()
        data = threading_table_data(deck, draft)
        assert data["holes"] == ["A", "B", "C", "D"]
        assert len(data["cards"]) == 17
        first = data["cards"][0]
        assert first["number"] == 1
        assert first["direction"] == "Z"
        # Mapping A: every hole of card 1 carries end 1's color, as a hex
        assert set(first["hexes"].values()) == {draft.palette[draft.ends[0].color_name]}

    def test_deck_summary_rows(self):
        deck, _ = make_deck()
        rows = deck_summary_rows(deck)
        assert len(rows) == 17
        assert rows[0].startswith("Card 1:")
        assert "Z-threaded" in rows[0]

    def test_start_position_text_states_the_convention(self):
        deck, _ = make_deck()
        text = start_position_text(deck)
        assert "A and D" in text
        assert "printed sides facing right" in text
        assert "clockwise" in text


class TestBuildPdf:
    def test_smoke_build(self, tmp_path):
        deck, draft = make_deck()
        out = tmp_path / "deck.pdf"
        result = build_pdf(deck, draft, out)
        assert result["pages"] >= 4
        assert out.exists()
        data = out.read_bytes()
        assert data[:4] == b"%PDF"
        assert len(data) > 2000

    def test_wide_40_card_deck_builds(self, tmp_path):
        deck, draft = make_deck(mapping="B", n=40)
        out = tmp_path / "wide.pdf"
        result = build_pdf(deck, draft, out)
        assert result["pages"] >= 4
        assert out.read_bytes()[:4] == b"%PDF"

    def test_default_filename_is_draft_name(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        deck, draft = make_deck()
        build_pdf(deck, draft)
        assert (tmp_path / "quiet-harbor-17.pdf").exists()
