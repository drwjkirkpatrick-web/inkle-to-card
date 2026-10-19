"""Tests for the domain model (Prompt 1).

Every test names the weaving fact it pins, so the suite doubles as a
readable spec for a non-coder following along.
"""
import pytest

from inkletocard.models import (
    HOLE_ORDER,
    SURFACE_CYCLE,
    Card,
    CardDeck,
    DraftError,
    End,
    InkleDraft,
    Pick,
    StartPosition,
    ThreadingDirection,
    Turn,
)


def make_draft(n_ends=17, colors=None):
    """A small helper: alternating H/U ends cycling through the palette."""
    palette = {"navy": "#1B2A4A", "cream": "#F5F0E6", "blue": "#3B6EA5", "gold": "#C9A227"}
    colors = colors or ["navy", "cream", "blue", "gold"]
    ends = [
        End(index=i, color_name=colors[i % len(colors)], heddled=(i % 2 == 0))
        for i in range(n_ends)
    ]
    return InkleDraft(name="quiet-harbor-17", palette=palette, ends=ends)


class TestConstants:
    def test_hole_order_is_abcd(self):
        assert HOLE_ORDER == ("A", "B", "C", "D")

    def test_surface_cycle_matches_research(self):
        # Research sec 3: from standard position, 4F-4B shows rows
        # D, C, B, A, A, B, C, D.
        assert SURFACE_CYCLE == ("D", "C", "B", "A", "A", "B", "C", "D")

    def test_surface_cycle_mirrors_in_second_half(self):
        assert list(SURFACE_CYCLE[:4]) == list(reversed(SURFACE_CYCLE[4:]))


class TestValidation:
    def test_valid_draft_has_no_problems(self):
        assert make_draft().validate() == []

    def test_bad_hex_is_reported(self):
        draft = make_draft()
        draft.palette["navy"] = "navy-blue"
        problems = draft.validate()
        assert any("invalid hex" in p for p in problems)

    def test_unknown_color_is_reported_with_palette_keys(self):
        draft = make_draft()
        draft.ends[3] = End(index=3, color_name="chartreuse", heddled=False)
        problems = draft.validate()
        assert any("chartreuse" in p and "gold" in p for p in problems)

    def test_non_alternating_heddles_reported(self):
        draft = make_draft()
        draft.ends[1] = End(index=1, color_name="cream", heddled=True)  # two H in a row
        problems = draft.validate()
        assert any("alternate" in p for p in problems)

    def test_too_few_ends_reported(self):
        draft = make_draft(n_ends=6)
        problems = draft.validate()
        assert any("at least 8" in p for p in problems)


class TestComputedHelpers:
    def test_color_counts(self):
        draft = make_draft(n_ends=8, colors=["navy", "cream"])
        assert draft.color_counts() == {"navy": 4, "cream": 4}

    def test_stripe_blocks_runs(self):
        draft = make_draft(n_ends=8, colors=["navy", "navy", "cream", "blue"])
        assert draft.stripe_blocks() == [("navy", 2), ("cream", 1), ("blue", 1), ("navy", 2), ("cream", 1), ("blue", 1)]


class TestRoundTrips:
    def test_end_round_trip(self):
        e = End(index=4, color_name="gold", heddled=False)
        assert End.from_dict(e.to_dict()) == e

    def test_draft_round_trip(self):
        draft = make_draft()
        rebuilt = InkleDraft.from_dict(draft.to_dict())
        assert rebuilt == draft
        assert rebuilt.ends[0].heddled is True

    def test_draft_from_dict_ignores_extra_keys(self):
        # Computed properties must never break from_dict (past-project pitfall).
        data = make_draft().to_dict()
        data["color_counts"] = {"navy": 1}
        assert InkleDraft.from_dict(data) == make_draft()

    def test_card_round_trip_with_threading(self):
        card = Card(number=1, hole_colors={"A": "navy", "B": "navy", "C": "navy", "D": "navy"},
                    threading=ThreadingDirection.S)
        rebuilt = Card.from_dict(card.to_dict())
        assert rebuilt == card
        assert rebuilt.threading is ThreadingDirection.S

    def test_deck_round_trip(self):
        deck = CardDeck(
            draft_name="d", mapping="A",
            cards=[Card(1, {h: "navy" for h in HOLE_ORDER})],
            start_position=StartPosition(),
            picks=[Pick(turns=[Turn.F]), Pick()],
            warnings=["low contrast"],
        )
        rebuilt = CardDeck.from_dict(deck.to_dict())
        assert rebuilt == deck
        assert rebuilt.picks[0].turns[0] is Turn.F
        assert rebuilt.picks[1].turns == []


class TestCardBehavior:
    def test_card_reports_all_four_holes(self):
        card = Card(1, {h: "navy" for h in HOLE_ORDER})
        assert card.holes_complete()
        assert set(card.hole_colors) == {"A", "B", "C", "D"}

    def test_start_position_default_names_holes_a_d(self):
        sp = StartPosition()
        assert sp.top_holes == ("A", "D")
        assert "A and D" in sp.description


def test_draft_error_is_a_value_error():
    # Parsers raise DraftError; callers may catch plain ValueError.
    assert issubclass(DraftError, ValueError)
