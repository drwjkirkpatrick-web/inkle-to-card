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


# ---------------------------------------------------------------------------
# Prompt 8: R5-R9
# ---------------------------------------------------------------------------
from inkletocard.models import Card, CardDeck, Pick, StartPosition, Turn
from inkletocard.report import (
    legend_text,
    materials_report,
    turning_chart_data,
    warnings_list,
)
from inkletocard.simulate import simulate_band


class TestTurningChartData:
    def test_4f4b_is_uniform_with_shorthand(self):
        deck, _ = make_deck()
        data = turning_chart_data(deck)
        assert data["uniform"] is True
        assert data["shorthand"] == "4F 4B"
        assert data["picks"] == 8
        assert all(cell == "F" for cell in data["rows"][0])
        assert all(cell == "B" for cell in data["rows"][7])

    def test_per_card_overrides_drop_the_shorthand(self):
        deck, draft = make_deck(n=4)
        deck.picks = [Pick(turns=[Turn.F, Turn.B, Turn.F, Turn.F]),
                      Pick(turns=[Turn.B, Turn.B, Turn.F, Turn.F])]
        data = turning_chart_data(deck)
        assert data["uniform"] is False
        assert data["shorthand"] is None
        assert data["rows"][0] == ["F", "B", "F", "F"]

    def test_no_picks_raises(self):
        deck, _ = make_deck()
        deck.picks = []
        import pytest as _pytest
        with _pytest.raises(ValueError, match="no picks attached"):
            turning_chart_data(deck)


class TestMaterials:
    def test_mapping_a_math(self):
        deck, draft = make_deck(mapping="A", n=40)
        m = materials_report(deck, draft, finished_cm=200)
        assert m["warp_length_cm"] == 290.0
        # small_draft(40) cycles 4 colors, so 10 ends per color; Mapping A threads = 10 x 4
        assert m["threads_per_color"] == {"navy": 10 * 4, "cream": 10 * 4, "blue": 10 * 4, "gold": 10 * 4}
        assert m["per_color_meters"]["navy"] == 116.0  # 40 threads x 2.9 m

    def test_mapping_b_math(self):
        deck, draft = make_deck(mapping="B", n=40)
        m = materials_report(deck, draft, finished_cm=200)
        # Under B each end appears exactly once, in one hole of one card.
        assert m["threads_per_color"]["navy"] == 10
        assert m["per_color_meters"]["navy"] == 29.0  # 10 threads x 2.9 m

    def test_formula_string_mentions_allowances(self):
        deck, draft = make_deck()
        m = materials_report(deck, draft, finished_cm=150)
        assert "warp length" in m["formula"]
        assert m["card_count"] == 17


class TestLegendAndWarnings:
    def test_legend_notation(self):
        text = legend_text()
        assert '"/" = Z-threading' in text
        assert "bicycle wheel" in text
        assert "clockwise" in text

    def test_warnings_aggregate_and_dedupe(self):
        deck, draft = make_deck(n=8, mapping="A")
        deck.warnings.append("deck-level warning")
        preview = simulate_band(deck)
        # small_draft(8) alternates colors per end -> single-end features everywhere
        items = warnings_list(deck, draft, preview=preview)
        assert any("deck-level warning" in w for w in items)
        assert any("blend in the eye" in w for w in items)
        assert len(items) == len(set(items))  # no duplicates

    def test_low_contrast_draft_warns(self):
        from inkletocard.models import End, InkleDraft
        palette = {"gray": "#404040", "slate": "#484848"}
        ends = [End(index=i, color_name=("gray", "slate")[i % 2], heddled=(i % 2 == 0))
                for i in range(8)]
        draft = InkleDraft(name="d", palette=palette, ends=ends)
        deck = convert_draft(draft, mapping="A")
        attach_turning(deck, gen_4f4b(8))
        items = warnings_list(deck, draft, preview=simulate_band(deck))
        assert any("gray meets slate" in w for w in items)


class TestFullBuild:
    def test_full_report_nine_pages(self, tmp_path):
        deck, draft = make_deck()
        out = tmp_path / "full.pdf"
        result = build_pdf(deck, draft, out)
        assert result["pages"] == 9
        data = out.read_bytes()
        assert data[:4] == b"%PDF"
        assert len(data) > 5000

    def test_preview_computed_when_omitted(self, tmp_path):
        deck, draft = make_deck()
        out = tmp_path / "auto.pdf"
        result = build_pdf(deck, draft, out)  # preview=None -> computed internally
        assert result["pages"] == 9
        assert out.read_bytes()[:4] == b"%PDF"
