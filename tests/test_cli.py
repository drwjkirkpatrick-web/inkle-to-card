"""End-to-end tests for the CLI (Prompt 9).

These exercise the whole pipeline the way a user does: file in, PDF out,
and readable text on stdout for the --no-pdf mode.
"""
import pytest

from inkletocard.cli import main


def test_demo_list(capsys):
    assert main(["demo", "--list"]) == 0
    out = capsys.readouterr().out
    for name in ("first-band", "quiet-harbor-17", "belt-stripes-40"):
        assert name in out


def test_demo_builds_pdf(tmp_path, capsys):
    out = tmp_path / "first.pdf"
    assert main(["demo", "first-band", "-o", str(out)]) == 0
    assert out.read_bytes()[:4] == b"%PDF"
    assert "PDF report" in capsys.readouterr().out


def test_demo_default_writes_draft_name_pdf(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["demo", "quiet-harbor-17"]) == 0
    assert (tmp_path / "quiet-harbor-17.pdf").exists()
    assert "17 cards" in capsys.readouterr().out


def test_convert_no_pdf_prints_deck_and_preview(tmp_path, capsys):
    draft = tmp_path / "d.inkle"
    draft.write_text(
        "name: tiny band\n"
        "palette: navy #1B2A4A, cream #F5F0E6\n"
        "ends: navy H | cream U | navy H | cream U | navy H | cream U | navy H | cream U\n"
    )
    assert main(["convert", str(draft), "--no-pdf"]) == 0
    out = capsys.readouterr().out
    assert "8 cards" in out
    assert "Card 1: A=navy" in out
    assert "legend:" in out  # ascii preview present
    assert "home position" in out


def test_convert_mapping_b_counts_cards(tmp_path, capsys):
    draft = tmp_path / "d.json"
    draft.write_text(
        '{"name": "b-band", "palette": {"navy": "#1B2A4A", "cream": "#F5F0E6"}, '
        '"order": "navy navy cream cream navy navy cream cream", "heddles": "H U H U H U H U"}'
    )
    out = tmp_path / "b.pdf"
    assert main(["convert", str(draft), "--mapping", "B", "-o", str(out)]) == 0
    assert "2 cards" in capsys.readouterr().out
    assert out.read_bytes()[:4] == b"%PDF"


def test_convert_missing_file_fails_cleanly(capsys):
    assert main(["convert", "/no/such/draft.json"]) == 1
    assert "error:" in capsys.readouterr().err


def test_convert_invalid_draft_fails_cleanly(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text('{"name": "d", "palette": {"navy": "blue"}, "order": "navy cream"}')
    assert main(["convert", str(bad)]) == 1
    assert "invalid hex" in capsys.readouterr().err


def test_version_flag():
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0


class TestImperialUnits:
    def test_finished_in_runs_end_to_end(self, tmp_path, capsys):
        draft = tmp_path / "d.json"
        draft.write_text(
            '{"name": "belt", "palette": {"navy": "#1B2A4A", "cream": "#F5F0E6"}, '
            '"order": "navy cream navy cream navy cream navy cream"}'
        )
        assert main(["convert", str(draft), "--finished-in", "78", "-o", str(tmp_path / "b.pdf")]) == 0
        assert (tmp_path / "b.pdf").exists()

    def test_finished_flags_mutually_exclusive(self, tmp_path, capsys):
        draft = tmp_path / "d.json"
        draft.write_text(
            '{"name": "belt", "palette": {"navy": "#1B2A4A", "cream": "#F5F0E6"}, '
            '"order": "navy cream navy cream navy cream navy cream"}'
        )
        assert main(["convert", str(draft), "--finished-cm", "200", "--finished-in", "78"]) == 1
        assert "not both" in capsys.readouterr().err

    def test_negative_finished_rejected(self, tmp_path, capsys):
        draft = tmp_path / "d.json"
        draft.write_text(
            '{"name": "belt", "palette": {"navy": "#1B2A4A", "cream": "#F5F0E6"}, '
            '"order": "navy cream navy cream navy cream navy cream"}'
        )
        assert main(["convert", str(draft), "--finished-in", "-5"]) == 1
        assert "positive" in capsys.readouterr().err
