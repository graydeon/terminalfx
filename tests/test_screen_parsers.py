from terminalfx.sources.screen import parse_wmctrl_titles, parse_xrandr_monitors


def test_parse_xrandr_monitors() -> None:
    output = "Monitors: 1\n 0: +*HDMI-1 1920/530x1080/300+0+0  HDMI-1\n"

    monitors = parse_xrandr_monitors(output)

    assert len(monitors) == 1
    assert monitors[0].name == "HDMI-1"
    assert monitors[0].width == 1920


def test_parse_wmctrl_titles() -> None:
    output = "0x01200007  0 host Terminal\n0x01200008  0 host Browser\n"

    assert parse_wmctrl_titles(output) == ["Terminal", "Browser"]
