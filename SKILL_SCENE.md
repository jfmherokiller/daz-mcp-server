# Skill: Scene Architect
Tools for scene layout, hierarchy, and library management.

## Scene & Hierarchy
- `daz_scene_info`: Snapshot of the scene.
- `daz_get_node_hierarchy`: Skeleton/tree mapping.
- `daz_set_parent`: Attaching props or organizing the tree.
- `daz_get_scene_layout`: Full spatial map.

## Batch Operations (Performance)
Use these for 5-10x speedup when changing 3+ items:
- `daz_batch_set_properties`, `daz_batch_transform`, `daz_batch_visibility`, `daz_batch_select`.

## Spatial Analysis
- `daz_get_world_position`, `daz_get_bounding_box`.
- `daz_check_overlap`: Collision/penetration detection.
- `daz_find_nearby_nodes`: Find items within a radius.

## Content Library
- `daz_list_categories`, `daz_browse_category`: Navigating `.duf` files.
- `daz_search_content`: Keyword search across the library.
- `daz_load_file`, `daz_load_product`: Load by path or product name.
  - `daz_load_file`'s `replace_mode="add"` forces DzContentReplaceMgr into NeverReplace before
    loading — use this when merging a Camera(s)/Light(s) Preset that you want ADDED rather than
    silently replacing every existing camera/light in the scene (SKILL_STUDIO_CONCEPTS.md's
    Content Type Indicator colors — that's Red-type content). Live-verified: existing
    cameras/lights survived a merge with `replace_mode="add"` (counts doubled, not replaced).
- `daz_check_compatibility`: Verify an asset works with a given figure.
- `daz_set_content_metadata`: Assign Content Type / Compatibility / Category metadata to a file via
  `DzAssetMgr.setFileMetadata()` — the scriptable equivalent of the manual Content DB Editor
  workflow (SKILL_PACKAGING.md). Mutates the real Content Database — live-verified working, but the
  SDK-documented `static` call genuinely fails; only `App.getAssetMgr().setFileMetadata()` works
  (see SKILL_SDK_REFERENCE.md).
- **Reading a purchased product's `.duf`/`.dsf` without touching Daz Studio at all**: every product
  DIM has ever downloaded sits as a plain `.zip` under DIM's own Downloads folder (e.g.
  `.../DAZ 3D/InstallManager/Downloads/` — check the user's actual content-directory list, this
  varies per install) alongside its `IM<id>-<part>_<Name>.dsx` sidecar. A `.duf`/`.dsf` inside that
  zip is just JSON — plain UTF-8, or gzip-compressed (check for the `\x1f\x8b` magic header and
  `gzip.decompress()` first if so; both forms are real and common). This means a real, professionally
  authored asset's actual channel values/material recipe/morph data can be inspected directly with
  `zipfile`/`gzip`/`json` — zero Daz Studio interaction, zero risk of the live server hanging on a
  bad load, and no need to install/extract anything. Prefer this over loading unfamiliar purchased
  content into a live Daz Studio session for read-only inspection; reserve `daz_load_file` for
  content you actually intend to use in the scene. Note the material data itself typically lives in
  the file's `material_library` array's full per-channel `studio_material_channels` blocks (both
  `value` = library/shader default and `current_value` = what this asset actually authored), not
  necessarily in `scene.materials` (which is often just a `"url": "#id"` fragment reference back
  into `material_library`, with no channel data of its own).

## Materials
- `daz_list_materials`, `daz_get_material`: Inspect surfaces on a node.
- `daz_set_material_property`: Set a surface property (color, reflectivity, etc.).
- `daz_apply_material_preset`, `daz_copy_material`: Apply presets or clone surfaces.
- `daz_convert_to_iray_uber`: Fix content that lands as legacy `DzDefaultMaterial` instead of
  `DzUberIrayMaterial` (common after merging raw/hand-authored `.duf` content) — see
  SKILL_DAZSCRIPT.md's "Materials — DzDefaultMaterial vs DzUberIrayMaterial" for why this happens
  and why the fix goes through shader-preset application rather than editing channel data.
- **Iray Uber Base — real-world Subsurface Scattering/Translucency authoring values**: confirmed by
  reading three independent real assets straight out of their DIM zip files this way (two
  commercial Genesis 8 characters from different PAs, plus Daz's own official "Genesis 8 Basic
  Female" base figure) — real skin materials tune `SSS Amount`/`SSS Color`/`Scattering Measurement
  Distance` (`/Volume/Scattering`) TOGETHER with `Translucency Weight` (`/Base/Diffuse/
  Translucency`) and `Transmitted Color`/`Transmitted Measurement Distance` (`/Volume/Transmission`)
  — never SSS alone. Consistently observed across all 3 samples:
  - `Base Color Effect` = `1` ("Scatter & Transmit").
  - `SSS Mode` stays `Mono` (`0`) — not `Chromatic`, despite Chromatic sounding like the more
    "physically complete" choice for skin.
  - `Thin Walled` = `false` — required for the `/Volume/Scattering` group to have any effect at all;
    the stock Iray Uber Base preset ships with it `true` (inert), so anything that programmatically
    enables SSS must explicitly flip this too, or every other channel silently does nothing.
  - `SSS Color`/`Transmitted Color`/`SSS Reflectance Tint`/`Translucency Color` are **flat colors
    only** — none of the 3 samples had an `image_file` on any of these channels, even when `Diffuse
    Color`'s own `value` was left at plain white `[1,1,1]` with the actual skin tone coming entirely
    from an attached Base Color texture map. Don't reuse a Base Color texture reference directly for
    these channels; derive a flat representative color instead (e.g. the average pixel color of the
    texture) if the source color is itself textured.
  - `Scattering Measurement Distance` real values were `0.12`-`2` (i.e. roughly 1mm-2cm) — Daz's
    internal/DSON distance unit is centimeters, consistent with this range for a skin-plausible
    subsurface mean-free-path.
  - Exact magnitudes are genuinely per-asset tunable (not hardcoded universally) — two different
    PAs' characters had byte-identical values (suggesting a shared vendor/Daz-recommended base
    recipe most PAs don't touch beyond diffuse texture), while Daz's own base figure had a
    similar-pattern but numerically different set.

## Scene Utilities
- `daz_save_scene`, `daz_save_scene_copy`: Save current or copy scene.
- `daz_get_selected_nodes`: Query current DAZ Studio selection.
- `daz_delete_node`: Remove a node from the scene.
