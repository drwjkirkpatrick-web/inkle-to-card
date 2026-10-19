"""Tests for color utilities (Prompt 6)."""
import pytest

from inkletocard.colors import (
    CSS_NAMES,
    check_draft_contrast,
    contrast_ratio,
    mixing_note,
    relative_luminance,
    suggest_name,
    value_ladder,
)
from tests_helpers import small_draft


class TestLuminance:
    def test_white_is_one(self):
        assert relative_luminance("#FFFFFF") == pytest.approx(1.0)

    def test_black_is_zero(self):
        assert relative_luminance("#000000") == pytest.approx(0.0)

    def test_bad_hex_rejected(self):
        with pytest.raises(ValueError, match="#rrggbb"):
            relative_luminance("navy")


class TestContrastRatio:
    def test_black_vs_white_is_21(self):
        assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0, rel=0.01)

    def test_identical_colors_are_one(self):
        assert contrast_ratio("#1B2A4A", "#1B2A4A") == 1.0

    def test_ratio_is_symmetric(self):
        assert contrast_ratio("#FFFFFF", "#808080") == pytest.approx(
            contrast_ratio("#808080", "#FFFFFF")
        )


class TestValueLadder:
    def test_sorted_dark_to_light(self):
        palette = {"white": "#FFFFFF", "navy": "#1B2A4A", "gray": "#808080"}
        ladder = value_ladder(palette)
        assert [name for name, _hexv, _lum in ladder] == ["navy", "gray", "white"]
        lum = [entry[2] for entry in ladder]
        assert lum == sorted(lum)


class TestDraftContrast:
    def test_clear_draft_has_no_warnings(self):
        draft = small_draft(8, colors=["navy", "cream"])
        assert check_draft_contrast(draft) == []

    def test_close_values_warn_with_counts(self):
        from inkletocard.models import End, InkleDraft
        palette = {"gray": "#404040", "slate": "#484848"}
        ends = [
            End(index=i, color_name=("gray", "slate")[i % 2], heddled=(i % 2 == 0))
            for i in range(8)
        ]
        warnings = check_draft_contrast(InkleDraft(name="d", palette=palette, ends=ends))
        assert len(warnings) >= 7  # every boundary is low contrast
        assert "gray meets slate" in warnings[0]
        assert "1.1:1" in warnings[0]
        assert "black-and-white-photo" in warnings[0]

    def test_threshold_is_a_parameter(self):
        from inkletocard.models import End, InkleDraft
        palette = {"navy": "#1B2A4A", "cream": "#F5F0E6"}
        ends = [
            End(index=i, color_name=("navy", "cream")[i % 2], heddled=(i % 2 == 0))
            for i in range(8)
        ]
        draft = InkleDraft(name="d", palette=palette, ends=ends)
        assert check_draft_contrast(draft, threshold=1.8) == []
        assert check_draft_contrast(draft, threshold=15.0) != []


class TestSuggestionsAndNotes:
    def test_suggest_black(self):
        assert suggest_name("#000000") == "black"

    def test_suggest_midnightblue_for_project_navy(self):
        assert suggest_name("#1B2A4A") == "midnightblue"

    def test_css_table_has_cream(self):
        assert CSS_NAMES["cream"] == "#F5F0E6"

    def test_mixing_note_for_single_end(self):
        from inkletocard.models import End, InkleDraft
        palette = {"navy": "#1B2A4A", "gold": "#C9A227"}
        order = ["navy", "gold", "navy", "navy", "navy", "gold", "navy", "navy"]
        ends = [
            End(index=i, color_name=order[i], heddled=(i % 2 == 0)) for i in range(8)
        ]
        notes = mixing_note(InkleDraft(name="d", palette=palette, ends=ends))
        # ends 1 (navy), 2 (gold) and 5 (gold) are all width-1 blocks
        assert len(notes) == 3
        assert any("single gold thread" in n for n in notes)
        assert any("single navy thread" in n for n in notes)
        assert "blend in the eye" in notes[0]

    def test_no_mixing_note_for_wide_stripes(self):
        from inkletocard.models import End, InkleDraft
        palette = {"navy": "#1B2A4A", "cream": "#F5F0E6"}
        order = ["navy"] * 4 + ["cream"] * 4  # two wide stripes, no single ends
        ends = [End(index=i, color_name=order[i], heddled=(i % 2 == 0)) for i in range(8)]
        assert mixing_note(InkleDraft(name="d", palette=palette, ends=ends)) == []
