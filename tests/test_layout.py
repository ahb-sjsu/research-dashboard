"""Tests for research_dashboard.layout."""

from __future__ import annotations

from unittest.mock import patch

from research_dashboard.layout import (
    ALL_TOOL_NAMES,
    build_layout,
    detect_tools,
)

# ---------------------------------------------------------------------------
# detect_tools
# ---------------------------------------------------------------------------


class TestDetectTools:
    """Tests for detect_tools()."""

    def test_returns_dict_with_all_tool_names(self):
        with patch("research_dashboard.layout.shutil.which", return_value=None):
            result = detect_tools()
        assert isinstance(result, dict)
        for name in ALL_TOOL_NAMES:
            assert name in result

    def test_all_tools_available(self):
        with patch(
            "research_dashboard.layout.shutil.which", return_value="/usr/bin/fake"
        ):
            result = detect_tools()
        assert all(result.values())

    def test_no_tools_available(self):
        with patch("research_dashboard.layout.shutil.which", return_value=None):
            result = detect_tools()
        assert not any(result.values())

    def test_partial_availability(self):
        available = {"htop", "tmux", "watch"}

        def fake_which(name: str) -> str | None:
            return f"/usr/bin/{name}" if name in available else None

        with patch("research_dashboard.layout.shutil.which", side_effect=fake_which):
            result = detect_tools()

        assert result["htop"] is True
        assert result["tmux"] is True
        assert result["nvtop"] is False
        assert result["iotop"] is False


# ---------------------------------------------------------------------------
# build_layout
# ---------------------------------------------------------------------------


def _all_tools_present() -> dict[str, bool]:
    """Return a tools dict where everything is available."""
    return {name: True for name in ALL_TOOL_NAMES}


def _no_tools() -> dict[str, bool]:
    """Return a tools dict where nothing is available."""
    return {name: False for name in ALL_TOOL_NAMES}


class TestBuildLayout:
    """Tests for build_layout()."""

    def test_returns_list_of_strings(self):
        cmds = build_layout(_all_tools_present(), session_name="test-sess")
        assert isinstance(cmds, list)
        assert all(isinstance(c, str) for c in cmds)

    def test_session_name_appears_in_commands(self):
        cmds = build_layout(_all_tools_present(), session_name="my-dash")
        for cmd in cmds:
            if cmd.startswith("tmux"):
                assert "my-dash" in cmd

    def test_kill_session_is_first(self):
        cmds = build_layout(_all_tools_present())
        assert "kill-session" in cmds[0]

    def test_attach_is_last(self):
        cmds = build_layout(_all_tools_present())
        assert "attach" in cmds[-1]

    def test_new_session_creates_session(self):
        cmds = build_layout(_all_tools_present())
        assert any("new-session" in c for c in cmds)

    def test_nvtop_used_when_available(self):
        cmds = build_layout(_all_tools_present())
        new_session_cmd = [c for c in cmds if "new-session" in c][0]
        assert "nvtop" in new_session_cmd

    def test_nvidia_smi_fallback(self):
        tools = _all_tools_present()
        tools["nvtop"] = False
        cmds = build_layout(tools)
        new_session_cmd = [c for c in cmds if "new-session" in c][0]
        assert "nvidia-smi" in new_session_cmd

    def test_no_gpu_flag_skips_gpu(self):
        cmds = build_layout(_all_tools_present(), no_gpu=True)
        new_session_cmd = [c for c in cmds if "new-session" in c][0]
        # Should use htop (CPU) instead of nvtop.
        assert "nvtop" not in new_session_cmd

    def test_no_disk_flag_skips_iotop(self):
        cmds = build_layout(_all_tools_present(), no_disk=True)
        joined = " ".join(cmds)
        assert "iotop" not in joined

    def test_no_net_flag_skips_nethogs(self):
        cmds = build_layout(_all_tools_present(), no_net=True)
        joined = " ".join(cmds)
        assert "nethogs" not in joined

    def test_style_commands_present(self):
        cmds = build_layout(_all_tools_present())
        styles = [c for c in cmds if "pane-border-style" in c or "status-style" in c]
        assert len(styles) >= 2

    def test_sensors_command_included(self):
        cmds = build_layout(_all_tools_present())
        joined = " ".join(cmds)
        assert "TEMPERATURES" in joined

    def test_logs_pane_included(self):
        cmds = build_layout(_all_tools_present())
        joined = " ".join(cmds)
        assert "LIVE LOGS" in joined

    def test_graceful_with_no_tools(self):
        """Even with zero tools available, build_layout should not error."""
        cmds = build_layout(_no_tools())
        assert isinstance(cmds, list)
        assert len(cmds) > 0

    def test_htop_fallback_to_btop(self):
        tools = _all_tools_present()
        tools["htop"] = False
        cmds = build_layout(tools)
        joined = " ".join(cmds)
        assert "btop" in joined

    def test_htop_fallback_to_top(self):
        tools = _all_tools_present()
        tools["htop"] = False
        tools["btop"] = False
        cmds = build_layout(tools)
        joined = " ".join(cmds)
        # Should contain bare 'top' as a command.
        assert "top'" in joined or 'top"' in joined

    def test_nethogs_fallback_to_nload(self):
        tools = _all_tools_present()
        tools["nethogs"] = False
        cmds = build_layout(tools)
        joined = " ".join(cmds)
        assert "nload" in joined

    def test_all_flags_combined(self):
        cmds = build_layout(
            _all_tools_present(),
            no_gpu=True,
            no_net=True,
            no_disk=True,
        )
        # Should still produce a valid list.
        assert any("new-session" in c for c in cmds)
        assert any("attach" in c for c in cmds)
