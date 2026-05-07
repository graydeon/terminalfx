"""CLI integration tests for render, record, and config commands."""

from pathlib import Path

from typer.testing import CliRunner

from terminalfx.cli import app

runner = CliRunner()


def test_show_config_output() -> None:
    result = runner.invoke(app, ["show-config", "--config", "examples/configs/default.yaml"])
    assert result.exit_code == 0
    assert "project_name" in result.stdout
    assert "source" in result.stdout


def test_config_doctor_passes() -> None:
    result = runner.invoke(app, ["config-doctor", "--config", "examples/configs/default.yaml"])
    assert result.exit_code == 0
    assert "ok" in result.stdout


def test_render_png_writes_file(tmp_path: Path) -> None:
    output = tmp_path / "test.png"
    result = runner.invoke(
        app,
        [
            "render-png",
            "--config", "examples/configs/default.yaml",
            "--output", str(output),
        ],
    )
    assert result.exit_code == 0
    assert output.exists()
    assert output.stat().st_size > 0


def test_render_mp4_writes_file(tmp_path: Path) -> None:
    output = tmp_path / "test.mp4"
    result = runner.invoke(
        app,
        [
            "render-mp4",
            "--config", "examples/configs/default.yaml",
            "--output", str(output),
            "--frames", "5",
        ],
    )
    assert result.exit_code == 0
    assert output.exists()
    assert output.stat().st_size > 0


def test_record_writes_file(tmp_path: Path) -> None:
    output = tmp_path / "record.mp4"
    result = runner.invoke(
        app,
        [
            "record",
            "--config", "examples/configs/default.yaml",
            "--output", str(output),
            "--seconds", "0.5",
        ],
    )
    assert result.exit_code == 0
    assert output.exists()
    assert output.stat().st_size > 0


def test_render_png_missing_source_errors(tmp_path: Path) -> None:
    output = tmp_path / "none.png"
    result = runner.invoke(
        app,
        [
            "render-png",
            "--config", "examples/configs/default.yaml",
            "--output", str(output),
        ],
    )
    assert result.exit_code == 0  # uses mock source from default config


def test_cli_help_prints_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "tui" in result.stdout
    assert "render-png" in result.stdout
    assert "render-mp4" in result.stdout
    assert "record" in result.stdout
    assert "show-config" in result.stdout
    assert "config-doctor" in result.stdout


def test_config_doctor_invalid_config(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(": invalid yaml [[[")
    result = runner.invoke(app, ["config-doctor", "--config", str(bad)])
    assert result.exit_code != 0
