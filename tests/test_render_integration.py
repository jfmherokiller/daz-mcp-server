"""Integration tests — render settings and render quality.

Tools covered (settings, non-blocking)
---------------------------------------
- daz_get_render_settings
- daz_set_render_quality
- daz_list_render_options
- daz_get_render_option
- daz_set_render_option

Slow tests (actual renders — require @pytest.mark.slow)
-------------------------------------------------------
- daz_render
- daz_render_with_camera

Run slow tests explicitly:
    uv run pytest tests/test_render_integration.py -m slow -v
"""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from vangard_daz_mcp.tools.render import (
    daz_get_render_option,
    daz_get_render_settings,
    daz_list_render_options,
    daz_render,
    daz_render_with_camera,
    daz_set_render_option,
    daz_set_render_quality,
)


# ---------------------------------------------------------------------------
# daz_get_render_settings
# ---------------------------------------------------------------------------

class TestGetRenderSettings:
    async def test_returns_dict(self, live_client):
        result = await daz_get_render_settings()
        assert isinstance(result, dict)

    async def test_has_render_engine(self, live_client):
        result = await daz_get_render_settings()
        text = str(result).lower()
        assert any(k in text for k in ["engine", "render", "iray", "3delight", "quality"])

    async def test_has_dimensions(self, live_client):
        result = await daz_get_render_settings()
        text = str(result).lower()
        assert any(k in text for k in ["width", "height", "size", "resolution"])


# ---------------------------------------------------------------------------
# daz_set_render_quality
# ---------------------------------------------------------------------------

class TestSetRenderQuality:
    @pytest.mark.parametrize("preset", ["draft", "preview", "good", "final"])
    async def test_quality_presets(self, live_client, preset):
        result = await daz_set_render_quality(preset)
        assert isinstance(result, dict)
        # Regression guard: this tool used to look up "Max Samples"/"Render Quality" on the
        # wrong holder (getOptionHelper() instead of the Iray renderer's own property holder)
        # and under the wrong label ("Render Quality" vs. the real "Rendering Quality"), so it
        # silently found nothing and returned propertiesSet=[] with a "not found" note every
        # time. Assert both properties were actually located and set.
        assert result.get("propertiesSet"), f"no properties were set: {result}"
        set_names = {p["property"] for p in result["propertiesSet"]}
        assert set_names == {"Max Samples", "Rendering Quality"}
        assert "note" not in result, f"unexpected not-found note: {result.get('note')}"

    async def test_invalid_preset_raises(self, live_client):
        with pytest.raises((ToolError, ValueError, Exception)):
            await daz_set_render_quality("nonexistent_preset_xyz")


# ---------------------------------------------------------------------------
# daz_list_render_options / daz_get_render_option / daz_set_render_option
# ---------------------------------------------------------------------------

class TestListRenderOptions:
    async def test_returns_dict_with_properties(self, live_client):
        result = await daz_list_render_options()
        assert isinstance(result, dict)
        assert result["count"] == len(result["properties"])
        assert result["count"] > 0

    async def test_covers_all_four_groups(self, live_client):
        result = await daz_list_render_options()
        groups = {p["group"] for p in result["properties"]}
        assert groups == {"iray", "iray_photoreal", "iray_interactive", "general"}

    async def test_known_properties_present(self, live_client):
        result = await daz_list_render_options()
        names = {p["name"] for p in result["properties"]}
        for expected in ("Max Samples", "Post Denoiser Enable", "Max Ray Bounces", "Render Style"):
            assert expected in names


class TestGetRenderOption:
    async def test_get_max_samples(self, live_client):
        result = await daz_get_render_option("Max Samples")
        assert result["property"] == "Max Samples"
        assert result["group"] == "iray"
        assert isinstance(result["value"], (int, float))

    async def test_get_from_interactive_subgroup(self, live_client):
        result = await daz_get_render_option("Max Ray Bounces")
        assert result["group"] == "iray_interactive"

    async def test_get_from_general_group(self, live_client):
        result = await daz_get_render_option("Render Style")
        assert result["group"] == "general"

    async def test_unknown_property_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_get_render_option("Nonexistent Property XYZ")


class TestSetRenderOption:
    async def test_set_and_readback_roundtrip(self, live_client):
        original = await daz_get_render_option("Max Samples")
        try:
            result = await daz_set_render_option("Max Samples", 250)
            assert result["old_value"] == original["value"]
            assert result["new_value"] == 250
            readback = await daz_get_render_option("Max Samples")
            assert readback["value"] == 250
        finally:
            await daz_set_render_option("Max Samples", original["value"])

    async def test_set_bool_property(self, live_client):
        original = await daz_get_render_option("Post Denoiser Enable")
        try:
            result = await daz_set_render_option("Post Denoiser Enable", True)
            assert result["new_value"]
        finally:
            await daz_set_render_option("Post Denoiser Enable", bool(original["value"]))

    async def test_color_property_rejected(self, live_client):
        with pytest.raises(ToolError):
            await daz_set_render_option("White Mode Color", 0.5)

    async def test_unknown_property_raises(self, live_client):
        with pytest.raises(ToolError):
            await daz_set_render_option("Nonexistent Property XYZ", 1)


# ---------------------------------------------------------------------------
# Slow render tests — skipped by default, run with -m slow
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.integration
class TestRender:
    async def test_render_to_temp_path(self, live_client, tmp_path):
        output = str(tmp_path / "test_render.png").replace("\\", "/")
        result = await daz_render(output_path=output)
        assert isinstance(result, dict)
        assert result.get("success") or "render" in str(result).lower()


@pytest.mark.slow
@pytest.mark.integration
class TestRenderWithCamera:
    async def test_render_from_temp_camera(self, live_client, temp_camera, tmp_path):
        output = str(tmp_path / "cam_render.png").replace("\\", "/")
        result = await daz_render_with_camera(temp_camera, output_path=output)
        assert isinstance(result, dict)
