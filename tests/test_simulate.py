"""Tests for the band face simulator (Prompt 5).

The load-bearing fact: from home position, 4F-4B shows the hole threads in
the order D, C, B, A, A, B, C, D (research section 3) - the simulator must
reproduce exactly that for a four-color card.
"""
import pytest

from inkletocard.models import Card, CardDeck, Pick, StartPosition, Turn
from inkletocard.simulate import BandPreview, ascii_render, column_summary, simulate_band
from inkletocard.turning import gen_4f4b

HOLES = ("A", "B", "C", "D")


def make_deck(hole_colors_per_card):
    cards = [
        Card(number=i + 1, hole_colors=dict(zip(HOLES, colors)))
        for i, colors in enumerate(hole_colors_per_card)
    ]
    return CardDeck(draft_name="d", mapping="A", cards=cards, start_position=StartPosition())


class TestSurfaceCycle:
    def test_4f4b_shows_dcbaa_bcd(self):
        deck = make_deck([("red", "green", "blue", "gold")])  # A,B,C,D = 4 colors
        preview = simulate_band(deck, gen_4f4b(1))
        # pick p shows the color of hole SURFACE_CYCLE[p-1]
        expect = ["gold", "blue", "green", "red", "red", "green", "blue", "gold"]
        assert [row[0] for row in preview.grid] == expect

    def test_solid_card_shows_constant_column(self):
        deck = make_deck([("navy",) * 4])
        preview = simulate_band(deck, gen_4f4b(1))
        assert all(row[0] == "navy" for row in preview.grid)

    def test_all_forward_continues_cycling(self):
        deck = make_deck([("red", "green", "blue", "gold")])
        picks = [Pick(turns=[Turn.F])] * 12
        preview = simulate_band(deck, picks)
        # picks 9-12 repeat D, C, B, A
        assert [row[0] for row in preview.grid[8:12]] == ["gold", "blue", "green", "red"]

    def test_backward_first_shows_a_b_c_d(self):
        deck = make_deck([("red", "green", "blue", "gold")])
        preview = simulate_band(deck, [Pick(turns=[Turn.B])] * 4)
        assert [row[0] for row in preview.grid] == ["red", "green", "blue", "gold"]


class TestPreviewShape:
    def test_width_equals_card_count(self):
        deck = make_deck([("navy",) * 4 for _ in range(17)])
        preview = simulate_band(deck, gen_4f4b(17))
        assert all(len(row) == 17 for row in preview.grid)
        assert preview.card_numbers == list(range(1, 18))

    def test_deck_warnings_carried_into_preview(self):
        deck = make_deck([("navy",) * 4])
        deck.warnings.append("original warning")
        preview = simulate_band(deck, gen_4f4b(1))
        assert "original warning" in preview.warnings

    def test_mapping_b_multicolor_cycling_warning(self):
        deck = make_deck([("red", "green", "blue", "gold"), ("navy",) * 4])
        deck.mapping = "B"
        preview = simulate_band(deck, gen_4f4b(2))
        assert any("cycle through the 8-pick sequence" in w for w in preview.warnings)


class TestInputValidation:
    def test_no_picks_raises(self):
        deck = make_deck([("navy",) * 4])
        with pytest.raises(ValueError, match="no picks to simulate"):
            simulate_band(deck, [])

    def test_pack_shorthand_pick_rejected(self):
        deck = make_deck([("navy",) * 4])
        with pytest.raises(ValueError, match="ambiguous"):
            simulate_band(deck, [Pick(turns=[])])

    def test_pick_length_mismatch_raises(self):
        deck = make_deck([("navy",) * 4, ("red",) * 4])
        with pytest.raises(ValueError, match="1 turn.*2 cards"):
            simulate_band(deck, [Pick(turns=[Turn.F])])


class TestRenderAndSummary:
    def test_ascii_render_has_legend_and_pick_rows(self):
        deck = make_deck([("navy",) * 4, ("cream",) * 4])
        text = ascii_render(simulate_band(deck, gen_4f4b(2)))
        assert "legend:" in text and "=navy" in text and "=cream" in text
        assert len([ln for ln in text.split("\n") if ln.strip()]) >= 10  # legend + header + 8 picks

    def test_column_summary_solid_run(self):
        deck = make_deck([("navy",) * 4])
        summary = column_summary(simulate_band(deck, gen_4f4b(1)))
        assert summary == [[("navy", 8)]]

    def test_column_summary_cycling_card(self):
        deck = make_deck([("red", "green", "blue", "gold")])
        summary = column_summary(simulate_band(deck, gen_4f4b(1)))
        # D,C,B,A,A,B,C,D -> runs: gold, blue, green, red x2, green, blue, gold
        assert summary[0][0] == ("gold", 1)
        assert ("red", 2) in summary[0]
        assert summary[0][-1] == ("gold", 1)
