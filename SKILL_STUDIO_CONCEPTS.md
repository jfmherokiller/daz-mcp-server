# Skill: Studio Concepts — Data Model & UI Reference

Source: official *DAZ Studio 4.6 User Guide* (docs.daz3d.com, `daz_studio_4_x_user_guide.pdf`, 96
pages — the "Hollywood Blvd" getting-started guide, not the full Reference Guide). Digested for
agents driving Daz Studio through `mcp__daz__*` tools / raw DazScript, not for humans clicking the
UI. Read this to understand *why* a property or tool behaves the way it does, not just its name.

**Version warning:** this guide predates Iray (added in Daz Studio 4.8). Its entire Chapter VIII
(Rendering) documents the legacy **3Delight** engine only. Everywhere it says "DAZ Studio Default"
shader it means `DzDefaultMaterial` (legacy RSL), not `DzUberIrayMaterial` — see
SKILL_DAZSCRIPT.md's "DzDefaultMaterial vs DzUberIrayMaterial" section. Sections below are flagged
`[legacy 3Delight]` where the content is renderer-specific and not applicable to a modern Iray
scene. Everything else (panes, property model, content types, parenting, joint limits, light
*types*, camera *properties*) is renderer-agnostic and still current.

---

## Property / pane model

Every UI slider is a **Property** (= a `DzProperty` node reachable via `findProperty` in
DazScript). Four panes — Surfaces, Shaping, Posing, Cameras, Lights — all share one UI pattern:

- **Editor page**: left column = Group/Region View (groups depend on current scene selection),
  right column = Property View for the selected group. A filter toggles `All` vs `Currently Used`
  (only non-default properties) — this is the UI equivalent of the `include_zero` pattern used by
  `daz_list_morphs`.
- **Presets page**: laid out like the Smart Content pane (Category View + Asset View). Applying a
  preset here goes through the same `openFile()`/preset-application codepath that
  `daz_convert_to_iray_uber` exploits (SKILL_DAZSCRIPT.md) — not raw channel-data description.

Node property groups: **General** (transforms), **Actor** (morphs = Shaping pane),
**Display** (visibility/shadow-casting toggles, viewport-only), **Pose Controls** (= Posing pane).
Axis color convention everywhere: **Red=X, Green=Y, Blue=Z**.

**Posing note:** rotate a bone and only that bone changes; translate a bone and the whole
downstream chain moves with it. Prefer rotation for posing individual joints.

**Joint rotation limits are enforced at the UI level** — loading a Pose Preset with out-of-range
values prompts to "turn limits off"; the Pose Tool gizmo shows two-toned rings (vibrant = within
limit, muted = outside). **Open question, not yet verified:** whether `prop.setValue()` /
`setDoubleValue()` in DazScript silently clamps to these limits or bypasses them. Test live before
relying on out-of-range pose values landing correctly.

**Expressions** live under the Posing pane, not a separate pane. Expression sliders only appear
when the figure's **head node** is the current selection — `Pose Controls → Head → Expressions`
(also `Brow`/`Cheeks`/`Eyes` subgroups for manual combination). Scripting implication: target the
head bone specifically (`findNodeByLabel("head")`), not the root figure node, before
`findProperty`-ing expression sliders.

---

## Content types & loading

- **Smart Content pane**: filtered by current scene selection (shows only content known-compatible
  with what's selected). **Content Library pane**: unfiltered, browse by format/product/category.
- **Content Type Indicator colors** (top-right corner of an icon) predict what a load action will
  do — useful for reasoning about `daz_load_file`/`daz_load_product` before calling them:
  - **Green** — adds to the scene (actor, wardrobe, prop).
  - **Yellow** — modifies the *currently selected* object; requires a selection first (Pose
    Presets, Material(s) Presets).
  - **Blue** — adds or modifies depending on current selection (Character Presets).
  - **Red** — **replaces every existing instance of that content type in the scene.** A Light(s)
    Preset replaces *all* lights; a Camera(s) Preset replaces *all* cameras; a Scene file replaces
    the whole scene. **This is a real gotcha for automated scene assembly** — loading a
    Camera(s)/Light(s) Preset via the plain path wipes what's already there. The UI's Ctrl/Cmd-held
    load path exposes a `Replace All` / `Replace Selected` / `Add` choice; no DazScript-level
    equivalent has been confirmed yet (open question for future SDK/IDA investigation).
  - **Magenta** — misconfigured content type; shouldn't normally appear.
- **Parenting** (Scene pane drag-and-drop) ≠ **Fit To / conforming**. Parenting: parent moves take
  the child with it, but child moves don't affect the parent — organizational/rigid grouping only,
  no deformation. Fit To (`General → Misc → 'Fit to'` property, shows `'None...'` when unfitted) is
  what actually conforms clothing/hair to a figure's pose. `Auto-Fit` (fitting content authored for
  a *different* figure) is explicitly documented as giving "varied results" — this matches
  `SKILL_RIGGING.md`'s finding that hand-authored `conform_target` doesn't guarantee real
  deformation; use the Transfer Utility workflow there for anything beyond native same-figure fits.

---

## Surfaces / Materials

- A **Surface** is a named polygon group with shared shader properties; every polygon belongs to
  exactly one. Genesis has 26 surfaces. A **Surface Shader** is the program that determines which
  channels even appear for a surface — a **Shader Preset** *applies* a shader, it is not itself a
  shader (this distinction is why `daz_convert_to_iray_uber` goes through preset application).
- **UV Set** is a per-surface property; must match the loaded image maps or you get stretching/seams.
  A figure can carry multiple UV sets (needed because extreme morphs distort UVs).
- **Surface Selection Sets**: predefined named multi-surface groups (e.g. face+head+lips) for bulk
  editing — Genesis 2 Female ships with `Default Templates` / `Legacy Surfaces` sets.
- **`[legacy 3Delight]` channel model** described by this guide (flat sliders + optional grayscale
  map per channel):

  | Channel | Behavior |
  |---|---|
  | Diffuse Color/Strength | Base color; grayscale map on Strength multiplies per-pixel |
  | Specular Color/Strength | Highlight color/intensity (not a full mirror) |
  | Glossiness | Highlight *size* (sharp vs broad), independent of Specular Strength |
  | Ambient Color/Strength | Tints core-shadow areas per-surface; a fake-glow trick, not real light emission |
  | Opacity Strength | 0%=transparent, 100%=opaque; map convention: black=transparent, white=opaque |
  | Bump Strength (+Min/Max) | Simulated relief via grayscale map; render-only, not in viewport |
  | Displacement Strength (+Min/Max) | Same as Bump but actually deforms geometry; render-only |

  Neutral value for Bump/Displacement maps is mid-gray `RGB(128,128,128)`. 1 Daz Studio unit = 1 cm
  — relevant when setting Min/Max Displacement values.
- **`[Iray, resolved]`** the legacy table above is a strict *subset* of DzUberIrayMaterial's real
  channel set, not a different naming scheme — confirmed by extracting the actual material JSON
  from a real shipped product. The legacy names (`Diffuse Strength`, `Glossiness`, `Bump Strength`,
  `Displacement Strength`, etc.) survive into Iray Uber unchanged; Iray just adds ~100 more channels
  on top (Base/Glossy/Refraction, Dual Lobe Specular, Top Coat, Metallic Flakes, Volume/Scattering,
  Emission...). **Full 110-channel table with exact `findProperty()` strings, types, and groups is
  in `SKILL_DSON_FORMAT.md`** — use that instead of guessing or assuming 1:1 legacy parity.

---

## Cameras

Every camera has exactly 3 property groups:
- **General** — transform (position/rotation), same as any node.
- **Display** — viewport-only gizmo appearance; **does not affect the render**.
- **Camera** — `Perspective` (bool; off = orthographic render from that camera), `Focal Length`
  (mm), `Depth of Field` (bool), `Focal Distance`, `F/Stop`. These map directly to
  `getFocalLengthControl()` / `getDepthOfFieldControl()` / `getFocalDistanceControl()` /
  `getFStopControl()` in SKILL_DAZSCRIPT.md — always use those accessors, never `findProperty` on a
  camera.

**Views vs Cameras**: the 1 Perspective + 6 Orthographic views (Front/Left/Right/Back/Top/Bottom)
are not scene objects — `Scene.getNumCameras()` doesn't count them, they can't be scripted/selected
as nodes. Only `new DzBasicCamera()` / loaded `.duf` cameras are real, selectable, animatable nodes.

**Gotcha:** loading a Camera(s) Preset replaces **all** cameras in the scene by default (see
Content Type Indicator colors above — this is Red-type content).

---

## Lights

Four types, each with different translation/rotation relevance:

| Type | Position matters? | Rotation matters? | Falloff | Notes |
|---|---|---|---|---|
| Distant | No | Yes (direction only) | None (infinite source) | No perspective when viewed through; good for sun/large-area fill |
| Spotlight | Yes | Yes | Cone (`Spread Angle` = FOV) | Has perspective when viewed through; controllable cone |
| Point | Yes | No | Physically-correct 1/d² | Weak per-light; good for accents (candles, bulbs), not scene-filling |
| Linear Point | Yes | No | Manual `Falloff Start`/`Falloff End` spheres, linear between them | Lets you push usable intensity higher than a physical Point light without inverse-square falloff |

Only Distant lights and Spotlights can become the active viewport view (Point/Linear Point cannot).

Property groups: **General** (transform) / **Display** (viewport visibility) / **Shadow** /
**Light**. Named properties and their **confirmed internal DazScript names** (verified against this
server's own `_registry.py`, not just the guide's UI labels — the guide's UI label and the
DazScript property string are **not always the same string**):

- Guide UI label "**Intensity**" → internal property is **`Flux`**, not `"Intensity"`. Confirmed by
  grep across `_registry.py` (every light-property script uses `findProperty("Flux")`).
- `Shadow Softness`, `Spread Angle` (Spotlight only) — internal names match the UI label directly,
  confirmed in `_registry.py` (`LIGHT_PROPS = ["Flux", "Shadow Softness", "Spread Angle", ...]`).
- `Photometric Mode` — appears in `_registry.py`'s light property list but is **not mentioned
  anywhere in this legacy guide** — almost certainly an Iray-era addition (photometric vs. raw
  local-intensity light unit). Needs its own investigation (SDK headers or live probe).
- `Shadow Type` (guide UI enum: `None` / `Deep Shadow Map` / `Raytraced (Software Only)`) and
  `Illumination` (guide UI enum: `On` / `Diffuse Only` / `Specular Only` / `Off`) — internal names
  not yet confirmed against live code; the `(Software Only)` qualifier on Raytraced strongly
  suggests this enum is 3Delight-era and Iray's shadow model differs. Verify before use.
- `Color` — almost certainly a `DzFloatColorProperty`; use `setFloatColorValue`/`getFloatColorValue`
  per SKILL_DAZSCRIPT.md's linear-color guidance, not `setColorValue`.

**3-point rig ratios** (the reasoning behind the tuned values already in `SKILL_DAZ_STUDIO.md` /
`daz-portrait-render`'s Key≈1200/Fill≈500/Rim≈600 flux):
- **Key Light** — main illumination, ~45° off the subject's midline, starting intensity ~100%
  (baseline for the ratio).
- **Fill Light** — fills Key's shadows, offset ~90° from Key, starting intensity ~40% of Key —
  should never overpower it.
- **Rim Light** — behind the subject biased toward the Fill side (avoids combining with Key and
  washing out the subject), brightest of the three, starting intensity ~120% of Key. Daz Studio
  supports overdriving lights above 100%.

**Default viewport lighting**: Daz Studio uses a camera-attached "Headlamp" light when no real
lights are loaded; loading any light disables it. Toggle preview mode via the `Use Scene Lights`
toolbar action. GPU-limited to ~8 real-time preview lights on most cards.

---

## Rendering `[legacy 3Delight — historical reference only]`

Everything in this section is the pre-Iray render-settings model. **Do not use these property
names/values when scripting against a modern Iray scene** — Iray's actual settings surface (via
`App.getRenderMgr().getRenderOptions()` for Iray-specific properties: progressive/photoreal mode,
max samples, max time, denoiser toggle) is not documented by this guide and needs direct
SDK-header/live-probe investigation.

- Render Quality: `0` = OpenGL viewport snapshot (no shadows, instant) up to `4` = full software
  raytrace render (CPU-bound, highest fidelity); `1`–`3` are GPU-accelerated compromises.
- Render Style: `Default` vs `Cartoon` (toon-shades any surface using `DzDefaultMaterial` only).
- Advanced settings (only exposed at Quality 4): `Max Ray Trace Depth` (default 2, raise only for
  multiple reflective surfaces), `Shadow Samples` (default 16, raise to de-grain soft shadows),
  `Shading Rate` (default 1.00, lower = more detail/slower — useful for close-ups).
- Still-image save formats: `.jpg`, `.png`, `.tiff`, `.bmp`.

---

## Open questions flagged for future SDK/IDA investigation

The user has granted access to the DAZ Studio 4.5+ SDK and 6.25+ BETA SDK (headers) plus IDA Pro
for further exploration — for documentation purposes, not license circumvention. Candidates for
that pass, in priority order:

1. **`[resolved 2026-08-11]`** Iray's actual `RenderOptions`/render-settings property surface —
   confirmed via SDK docs that `App.getRenderMgr().getRenderOptions()` (`DzRenderOptions`) is a
   **dead end**, legacy-scanline-only, no Iray fields at all. The real Iray settings live on
   `DzIrayRenderer.getPropertyHolder()` / `DzRenderMgr.getOptionHelper()` (both generic
   `DzElement*` property containers) — full detail and example code in `SKILL_SDK_REFERENCE.md`.
   Not yet live-verified against a running instance, but the mechanism is located.
2. ~~`DzUberIrayMaterial`'s real channel/property names~~ — **resolved 2026-08-11** by decompiling a
   real shipped product; full 110-channel table now in `SKILL_DSON_FORMAT.md`.
3. **`[resolved, nuanced, 2026-08-11]`** Whether pose/rotation property setters clamp to joint
   limits — no documented guarantee either way; clamping is a separate, per-property
   `isClamped()`/`doesClampChangeValue()` flag, and `setValue()`'s own docs never mention limits at
   all. Full detail in `SKILL_SDK_REFERENCE.md`. Treat as "don't assume clamped" until live-probed.
4. Confirm internal names for `Shadow Type`, `Illumination`, and what `Photometric Mode` actually
   controls on a light. **Not covered by this SDK pass** — still open.
5. ~~Whether a DazScript-level equivalent exists for the UI's Camera/Light preset load-options~~ —
   **resolved 2026-08-11**: `DzContentReplaceMgr` (`App.getContentMgr().getContentReplaceMgr()`),
   full detail in `SKILL_SDK_REFERENCE.md`.
6. ~~What other methods `DzAssetMgr` exposes~~ — **resolved 2026-08-11**, extensively — see
   `SKILL_SDK_REFERENCE.md`. Headline: `DzAssetMgr.setFileMetadata()` makes the entire manual
   Content DB Editor workflow (Compatibility Base/Category/ContentType assignment) scriptable.
7. Whether `daz_apply_material_preset`/`daz_set_material_property` internally use the same
   `name://@selection#materials:?extra/.../value` DSON path scheme documented in
   `SKILL_DSON_FORMAT.md`, or a different internal mechanism.
