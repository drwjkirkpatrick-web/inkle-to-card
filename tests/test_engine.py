"""Tests for the conversion engine (Prompt 3).

Pinned weaving facts (research sec 7): Mapping A preserves width one card per
end; Mapping B compresses four ends per card with hole D carrying the group's
first end; a 40-end draft is exactly 10 cards under B (the Mullarkey case).
"""
import pytest

from inkletocard.engine import convert_draft
from inkletocard.models import Card, CardDeck, End, InkleDraft, ThreadingDirection

PALETTE = {"navy": "#1B2A4A", "cream": "#F5F0E6", "blue": "#3B6EA5", "gold": "#C9A227"}


def make_draft(n_ends=17, colors=None):
    colors = colors or ["navy", "cream", "blue", "gold"]
    ends = [
        End(index=i, color_name=colors[i % len(colors)], heddled=(i % 2 == 0))
        for i in range(n_ends)
    ]
    return InkleDraft(name="quiet-harbor-17", palette=PALETTE, ends=ends)


class TestMappingA:
    def test_one_card_per_end_width_preserved(self):
        deck = convert_draft(make_draft(17), mapping="A")
        assert len(deck.cards) == 17
        assert deck.mapping == "A"

    def test_card_k_carries_end_k_color_in_every_hole(self):
        deck = convert_draft(make_draft(17), mapping="A")
        for k, card in enumerate(deck.cards):
            assert card.number == k + 1
            assert set(card.hole_colors.values()) == {deck and card.hole_colors["A"]}
            assert all(c == make_draft(17).ends[k].color_name for c in card.hole_colors.values())

    def test_order_preserved_left_to_right(self):
        draft = make_draft(17)
        deck = convert_draft(draft, mapping="A")
        assert [c.hole_colors["A"] for c in deck.cards] == [e.color_name for e in draft.ends]

    def test_threading_all_z(self):
        deck = convert_draft(make_draft(8), mapping="A")
        assert all(c.threading is ThreadingDirection.Z for c in deck.cards)

    def test_thread_consumption_warning(self):
        deck = convert_draft(make_draft(8), mapping="A")
        assert any("4x the thread" in w for w in deck.warnings)

    def test_never_pads_any_width(self):
        deck = convert_draft(make_draft(13), mapping="A")
        assert len(deck.cards) == 13
        assert not any("padded" in w for w in deck.warnings)


class TestMappingB:
    def test_four_ends_per_card(self):
        deck = convert_draft(make_draft(40), mapping="B")
        assert len(deck.cards) == 10

    def test_hole_d_carries_first_end_of_group(self):
        draft = make_draft(40)
        deck = convert_draft(draft, mapping="B")
        first = deck.cards[0].hole_colors
        # Surface order: pick 1 shows hole D -> the group's first end.
        assert first["D"] == draft.ends[0].color_name
        assert first["C"] == draft.ends[1].color_name
        assert first["B"] == draft.ends[2].color_name
        assert first["A"] == draft.ends[3].color_name

    def test_17_ends_pad_last_card_with_edge_color(self):
        draft = make_draft(17)
        deck = convert_draft(draft, mapping="B")
        assert len(deck.cards) == 5
        assert any("padded with 3 extra end" in w for w in deck.warnings)
        # edge color = first end's color fills the pad holes
        last = deck.cards[-1].hole_colors
        assert last["D"] == draft.ends[16].color_name
        assert last["C"] == draft.ends[0].color_name  # padded hole

    def test_narrow_feature_warning(self):
        colors = ["navy", "cream", "blue", "gold"]
        deck = convert_draft(make_draft(17), mapping="B")
        assert any("narrower than 4 ends" in w for w in deck.warnings)

    def test_compression_warning(self):
        deck = convert_draft(make_draft(40), mapping="B")
        assert any("one-quarter as wide" in w for w in deck.warnings)


class TestDeckShape:
    def test_start_position_is_explicit(self):
        deck = convert_draft(make_draft(8), mapping="A")
        sp = deck.start_position
        assert sp.top_holes == ("A", "D")
        assert "A and D" in sp.description
        assert sp.face == "right"
        assert sp.tablet_one == "left"

    def test_draft_name_carried(self):
        deck = convert_draft(make_draft(8), mapping="B")
        assert deck.draft_name == "quiet-harbor-17"

    def test_bad_mapping_rejected(self):
        with pytest.raises(ValueError, match="must be 'A' or 'B'"):
            convert_draft(make_draft(8), mapping="C")

    def test_deck_round_trip(self):
        deck = convert_draft(make_draft(17), mapping="B")
        rebuilt = CardDeck.from_dict(deck.to_dict())
        assert rebuilt == deck
        assert rebuilt.cards[0].hole_colors == deck.cards[0].hole_colors
