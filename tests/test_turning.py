"""Tests for turning sequences and twist accounting (Prompt 4)."""
import pytest

from inkletocard.engine import convert_draft
from inkletocard.models import Card, CardDeck, Pick, StartPosition, Turn
from inkletocard.turning import (
    TWIST_WARN_THRESHOLD,
    attach_turning,
    build_picks,
    gen_4f4b,
    net_quarter_turns,
    twist_warnings,
)
from tests_helpers import *  # noqa - (placeholder removed below if unused)


def make_deck(n_cards=4):
    return CardDeck(
        draft_name="d", mapping="A",
        cards=[Card(i + 1, {h: "navy" for h in ("A", "B", "C", "D")}) for i in range(n_cards)],
        start_position=StartPosition(),
    )


class TestGen4f4b:
    def test_shape_is_four_forward_then_four_backward(self):
        picks = gen_4f4b(3)
        assert len(picks) == 8
        assert all(p.turns == [Turn.F] * 3 for p in picks[:4])
        assert all(p.turns == [Turn.B] * 3 for p in picks[4:])

    def test_repeats_extend_the_cycle(self):
        picks = gen_4f4b(2, repeats=2)
        assert len(picks) == 16
        assert picks[8].turns == [Turn.F, Turn.F]
        assert picks[15].turns == [Turn.B, Turn.B]

    def test_rejects_bad_counts(self):
        with pytest.raises(ValueError, match="n_cards"):
            gen_4f4b(0)
        with pytest.raises(ValueError, match="repeats"):
            gen_4f4b(4, repeats=0)


class TestBuildPicks:
    def test_rows_to_picks(self):
        picks = build_picks(["F F B B", "B B F F"])
        assert picks[0].turns == [Turn.F, Turn.F, Turn.B, Turn.B]
        assert picks[1].turns == [Turn.B, Turn.B, Turn.F, Turn.F]

    def test_length_mismatch_reports_counts(self):
        with pytest.raises(ValueError, match="3 turns but row 1 has 4"):
            build_picks(["F F B B", "F F B"])

    def test_bad_token_reports_row_and_card(self):
        with pytest.raises(ValueError, match="row 1, card 2.*must be F"):
            build_picks(["F X B B"])

    def test_accepts_mixed_case_and_turn_values(self):
        picks = build_picks([["f", "b"], "B F"])
        assert picks[0].turns == [Turn.F, Turn.B]
        assert picks[1].turns == [Turn.B, Turn.F]


class TestTwistAccounting:
    def test_4f4b_is_twist_neutral(self):
        deck = make_deck(4)
        deck.picks = gen_4f4b(4)
        assert net_quarter_turns(deck) == {1: 0, 2: 0, 3: 0, 4: 0}
        assert twist_warnings(deck) == []

    def test_all_forward_accumulates(self):
        deck = make_deck(2)
        deck.picks = [Pick(turns=[Turn.F, Turn.F]) for _ in range(8)]
        assert net_quarter_turns(deck) == {1: 8, 2: 8}
        warnings = twist_warnings(deck)
        assert len(warnings) == 2
        assert "8 quarter-turns of forward twist" in warnings[0]

    def test_warning_threshold_is_one_full_turn(self):
        assert TWIST_WARN_THRESHOLD == 4

    def test_mismatched_pick_length_raises(self):
        deck = make_deck(4)
        deck.picks = [Pick(turns=[Turn.F, Turn.F])]
        with pytest.raises(ValueError, match="2 turns but the deck has 4"):
            net_quarter_turns(deck)

    def test_empty_picks_gives_zero_net(self):
        deck = make_deck(2)
        assert net_quarter_turns(deck) == {1: 0, 2: 0}


class TestAttachTurning:
    def test_attach_merges_twist_warnings(self):
        deck = make_deck(2)
        attach_turning(deck, [Pick(turns=[Turn.F, Turn.F]) for _ in range(8)])
        assert any("twist" in w for w in deck.warnings)

    def test_attach_rejects_empty(self):
        from inkletocard.models import DraftError
        with pytest.raises(DraftError, match="no picks"):
            attach_turning(make_deck(2), [])

    def test_end_to_end_engine_deck_gets_neutral_sequence(self):
        from tests_helpers import small_draft
        deck = convert_draft(small_draft(), mapping="A")
        attach_turning(deck, gen_4f4b(len(deck.cards)))
        assert net_quarter_turns(deck) == {c.number: 0 for c in deck.cards}
