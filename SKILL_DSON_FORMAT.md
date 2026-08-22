# Skill: DSON File Format — Reading & Writing .duf/.dsx/.dsa Directly

Ground truth from decompiling a real DIM store package, `IM00088988-01_SlimeShaders.zip` (Marshian's
"Slime Shaders" shader-preset product, store product #88988), analyzed 2026-08-11. This is what Daz
Install Manager actually ships and processes — more concrete than the UI-workflow descriptions in
SKILL_PACKAGING.md. Use this when an agent needs to inspect, validate, or generate Daz content
files directly at the filesystem/JSON level, not through the Daz Studio UI or DazScript.

## Compression & container

`.duf` files (and by extension `.dsf`) are **gzip-compressed JSON** — magic bytes `1f 8b 08 00`.
This is the "DSON" format (Daz Scene Object Notation). The Save dialog's "Compress File" checkbox
(seen throughout SKILL_PACKAGING.md's save workflows) toggles exactly this — an uncompressed file
is plain JSON text, directly editable. This is what the UV-replace troubleshooting workaround in
SKILL_PACKAGING.md relies on: text-editing a `.dsf` requires either saving it uncompressed to begin
with, or gunzipping it first.

```python
import gzip, json
data = json.loads(gzip.decompress(open("some.duf", "rb").read()))
```

**Not every `.duf` is compressed** — confirmed from Daz's own bundled "Default Resources" package:
several of Daz's first-party scene/preset files ship as **plain uncompressed JSON** (starts with
`{` directly, no gzip magic bytes). Don't assume compression; detect it (check for `1f 8b` magic)
and fall back to a plain `json.loads()` if it's not there:
```python
raw = open("some.duf", "rb").read()
data = json.loads(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw)
```

## Top-level .duf structure (Material/Shader Preset example)

```json
{
  "file_version": "0.6.1.0",
  "asset_info": {
    "id": "/My%20Presets/<Vendor>/<Product>/<Item>.duf",
    "type": "preset_shader",
    "contributor": {"author": "...", "email": "", "website": "..."},
    "revision": "1.0",
    "modified": "<ISO 8601 timestamp>"
  },
  "image_library": [ /* referenced texture maps */ ],
  "material_library": [ /* material channel definitions */ ],
  "scene": { /* what gets APPLIED when the preset loads */ }
}
```

**Confirmed gotcha:** `asset_info.id` is a free-text virtual path the author's local install had
when the file was originally saved (a `/My Presets/...` style path) — it does **not** have to match
the product this file actually ships in, and nothing validates it. One utility preset inspected in
the Slime Shaders package still carries an `asset_info.id` referencing an unrelated older product
("Underwater Relics Iray"), evidently copy-pasted forward from a prior release. **Don't treat
`asset_info.id` as a reliable product identifier** for validation purposes — use the
Manifest/Supplement/ContentDBInstall metadata below instead, which is what DIM and the CMS actually
key off of.

## `image_library` — texture references

Each entry: `id` (local reference key), `name`, `map_gamma` (`1` = linear/data map like bump or
spec, `0` = gamma-decoded sRGB color map, e.g. a spectrum/color-ramp lookup), `map: [{url, label}]`
— `url` is **content-root-relative** (`/Runtime/Textures/<Vendor>/<Folder>/<file>.jpg`), not a
filesystem path.

## `material_library` — channel definitions

One entry per material (`id: "default"` when the preset targets whatever's currently selected).
Contains:
- A handful of **top-level named channels** (e.g. `"diffuse"`) — a legacy/base-compatible subset,
  kept for readers that don't understand the Iray-specific extra data.
- `extra: [{type: "studio/material/uber_iray", version: "1.1.0.0"}, {type:
  "studio_material_channels", channels: [...]}]` — **this is where DzUberIrayMaterial's real,
  full channel set lives.** Each `channels[]` entry is `{channel: {id, type, label, value, min,
  max, ...}, group: "/Category/Subcategory"}`. **`channel.id` is the exact string
  `findProperty()` needs in DazScript.**

A **narrow utility preset** (e.g. a "Bump High" preset that only touches one or two channels) omits
the top-level `diffuse` key entirely and lists only the channels it actually sets under
`studio_material_channels.channels` — confirms Material(s) Presets modify only the channels they
explicitly declare, leaving everything else on the target untouched.

### Full DzUberIrayMaterial channel table (110 channels, extracted from a live shipped product)

| Channel ID (`findProperty` string) | Type | Label | Group |
|---|---|---|---|
| `Tags` | string | Tags | /General |
| `Line Preview Color` | color | Line Preview Color | /Geometry/Lines |
| `Line Start Width` | float | Line Start Width (mm) | /Geometry/Lines |
| `Line End Width` | float | Line End Width (mm) | /Geometry/Lines |
| `Line UV Width` | float | Line UV Width | /Geometry/Lines |
| `Base Mixing` | enum | Base Mixing | /Base/Mixing |
| `Metallic Weight` | float | Metallicity | /Base/Diffuse/Reflection |
| `Diffuse Weight` | float | Diffuse Weight | /Base/Diffuse/Reflection |
| `Diffuse Strength` | float | Diffuse Strength | /Base/Diffuse/Reflection |
| `Diffuse Roughness` | float | Diffuse Roughness | /Base/Diffuse/Reflection |
| `Diffuse Overlay Weight` | float | Diffuse Overlay Weight | /Base/Diffuse/Overlay |
| `Diffuse Overlay Weight Squared` | bool | Diffuse Overlay Weight Squared | /Base/Diffuse/Overlay |
| `Diffuse Overlay Color` | float_color | Diffuse Overlay Color | /Base/Diffuse/Overlay |
| `Diffuse Overlay Color Effect` | enum | Diffuse Overlay Color Effect | /Base/Diffuse/Overlay |
| `Diffuse Overlay Roughness` | float | Diffuse Overlay Roughness | /Base/Diffuse/Overlay |
| `Translucency Weight` | float | Translucency Weight | /Base/Diffuse/Translucency |
| `Base Color Effect` | enum | Base Color Effect | /Base/Diffuse/Translucency |
| `Translucency Color` | float_color | Translucency Color | /Base/Diffuse/Translucency |
| `Invert Transmission Normal` | bool | Invert Transmission Normal | /Base/Diffuse/Translucency |
| `SSS Reflectance Tint` | float_color | SSS Reflectance Tint | /Base/Diffuse/Translucency |
| `Dual Lobe Specular Weight` | float | Dual Lobe Specular Weight | /Base/Dual Lobe Specular |
| `Dual Lobe Specular Reflectivity` | float | Dual Lobe Specular Reflectivity | /Base/Dual Lobe Specular |
| `Specular Lobe 1 Roughness` | float | Specular Lobe 1 Roughness | /Base/Dual Lobe Specular |
| `Specular Lobe 2 Roughness` | float | Specular Lobe 2 Roughness | /Base/Dual Lobe Specular |
| `Specular Lobe 1 Glossiness` | float | Specular Lobe 1 Glossiness | /Base/Dual Lobe Specular |
| `Specular Lobe 2 Glossiness` | float | Specular Lobe 2 Glossiness | /Base/Dual Lobe Specular |
| `Dual Lobe Specular Ratio` | float | Dual Lobe Specular Ratio | /Base/Dual Lobe Specular |
| `Glossy Weight` | float | Glossy Weight | /Base/Glossy/Reflection |
| `Glossy Layered Weight` | float | Glossy Layered Weight | /Base/Glossy/Reflection |
| `Share Glossy Inputs` | bool | Share Glossy Inputs | /Base/Glossy/Reflection |
| `Glossy Color` | float_color | Glossy Color | /Base/Glossy/Reflection |
| `Glossy Color Effect` | enum | Glossy Color Effect | /Base/Glossy/Reflection |
| `Glossy Reflectivity` | float | Glossy Reflectivity | /Base/Glossy/Reflection |
| `Glossy Specular` | float_color | Glossy Specular | /Base/Glossy/Reflection |
| `Glossy Roughness` | float | Glossy Roughness | /Base/Glossy/Reflection |
| `Glossiness` | float | Glossiness | /Base/Glossy/Reflection |
| `Glossy Anisotropy` | float | Glossy Anisotropy | /Base/Glossy/Reflection |
| `Backscattering Weight` | float | Backscattering Weight | /Base/Glossy/Backscattering |
| `Backscattering Color` | float_color | Backscattering Color | /Base/Glossy/Backscattering |
| `Backscattering Roughness` | float | Backscattering Roughness | /Base/Glossy/Backscattering |
| `Backscattering Glossiness` | float | Backscattering Glossiness | /Base/Glossy/Backscattering |
| `Backscattering Anisotropy` | float | Backscattering Anisotropy | /Base/Glossy/Backscattering |
| `Refraction Index` | float | Refraction Index | /Base/Glossy/Refraction |
| `Refraction Weight` | float | Refraction Weight | /Base/Glossy/Refraction |
| `Refraction Color` | float_color | Refraction Color | /Base/Glossy/Refraction |
| `Refraction Roughness` | float | Refraction Roughness | /Base/Glossy/Refraction |
| `Refraction Glossiness` | float | Refraction Glossiness | /Base/Glossy/Refraction |
| `Abbe` | float | Abbe | /Base/Glossy/Refraction |
| `Glossy Anisotropy Rotations` | float | Glossy Anisotropy Rotations | /Base/Glossy/Anisotropy |
| `Base Thin Film` | float | Base Thin Film | /Base/Thin Film |
| `Base Thin Film IOR` | float | Base Thin Film IOR | /Base/Thin Film |
| `Bump Strength` | float | Base Bump | /Base/Bump |
| `Normal Map` | float | Normal Map | /Base/Bump |
| `Metallic Flakes Weight` | float | Metallic Flakes Weight | /Metallic Flakes/Flakes |
| `Metallic Flakes Color` | float_color | Metallic Flakes Color | /Metallic Flakes/Flakes |
| `Metallic Flakes Color Effect` | enum | Metallic Flakes Color Effect | /Metallic Flakes/Flakes |
| `Metallic Flakes Roughness` | float | Metallic Flakes Roughness | /Metallic Flakes/Flakes |
| `Metallic Flakes Glossiness` | float | Metallic Flakes Glossiness | /Metallic Flakes/Flakes |
| `Metallic Flakes Size` | float | Metallic Flakes Size | /Metallic Flakes/Flakes |
| `Metallic Flakes Strength` | float | Metallic Flakes Strength | /Metallic Flakes/Flakes |
| `Metallic Flakes Density` | float | Metallic Flakes Density | /Metallic Flakes/Flakes |
| `Metallic Flakes Thin Film` | float | Metallic Flakes Thin Film | /Metallic Flakes/Thin Film |
| `Metallic Flakes Thin Film IOR` | float | Metallic Flakes Thin Film IOR | /Metallic Flakes/Thin Film |
| `Top Coat Weight` | float | Top Coat Weight | /Top Coat/General |
| `Top Coat Color` | float_color | Top Coat Color | /Top Coat/General |
| `Top Coat Color Effect` | enum | Top Coat Color Effect | /Top Coat/General |
| `Top Coat Roughness` | float | Top Coat Roughness | /Top Coat/General |
| `Top Coat Glossiness` | float | Top Coat Glossiness | /Top Coat/General |
| `Top Coat Layering Mode` | enum | Top Coat Layering Mode | /Top Coat/General |
| `Reflectivity` | float | Reflectivity | /Top Coat/General |
| `Top Coat IOR` | float | Top Coat IOR | /Top Coat/General |
| `Top Coat Curve Normal` | float | Top Coat Curve 0 | /Top Coat/General |
| `Top Coat Curve Grazing` | float | Top Coat Curve 90 | /Top Coat/General |
| `Top Coat Curve Exponent` | float | Top Coat Curve Exponent | /Top Coat/General |
| `Top Coat Anisotropy` | float | Top Coat Anisotropy | /Top Coat/Anisotropy |
| `Top Coat Rotations` | float | Top Coat Rotations | /Top Coat/Anisotropy |
| `Top Coat Thin Film` | float | Top Coat Thin Film | /Top Coat/Thin Film |
| `Top Coat Thin Film IOR` | float | Top Coat Thin Film IOR | /Top Coat/Thin Film |
| `Top Coat Bump Mode` | enum | Top Coat Bump Mode | /Top Coat/Bump |
| `Top Coat Bump` | float | Top Coat Bump | /Top Coat/Bump |
| `Thin Walled` | bool | Thin Walled | /Volume/General |
| `Transmitted Measurement Distance` | float | Transmitted Measurement Distance | /Volume/Transmission |
| `Transmitted Color` | float_color | Transmitted Color | /Volume/Transmission |
| `SSS Mode` | enum | SSS Mode | /Volume/Scattering |
| `Scattering Measurement Distance` | float | Scattering Measurement Distance | /Volume/Scattering |
| `SSS Amount` | float | SSS Amount | /Volume/Scattering |
| `SSS Color` | float_color | SSS Color | /Volume/Scattering |
| `SSS Direction` | float | SSS Direction | /Volume/Scattering |
| `Emission Color` | float_color | Emission Color | /Emission |
| `Emission Temperature` | float | Emission Temperature (K) | /Emission |
| `Two Sided Light` | bool | Two Sided Light | /Emission |
| `Emission Profile` | file | Emission Profile | /Emission |
| `Luminance` | float | Luminance | /Emission |
| `Luminance Units` | enum | Luminance Units | /Emission |
| `Luminous Efficacy` | float | Luminous Efficacy (lm/W) | /Emission |
| `Cutout Opacity` | float | Cutout Opacity | /Geometry/Cutout |
| `Displacement Strength` | float | Displacement Strength | /Geometry/Displacement |
| `Minimum Displacement` | float | Minimum Displacement | /Geometry/Displacement |
| `Maximum Displacement` | float | Maximum Displacement | /Geometry/Displacement |
| `Horizontal Tiles` | float | Horizontal Tiles | /Geometry/Tiling |
| `Horizontal Offset` | float | Horizontal Offset | /Geometry/Tiling |
| `Vertical Tiles` | float | Vertical Tiles | /Geometry/Tiling |
| `Vertical Offset` | float | Vertical Offset | /Geometry/Tiling |
| `Round Corners Roundness` | float | Round Corners Roundness | /Geometry/Smoothing |
| `Roughness Squared` | bool | Roughness Squared | /Settings |
| `Glossiness Squared` | bool | Glossiness Squared | /Settings |
| `BSDF Type` | enum | BSDF Type | /Settings |
| `OutlineColorID` | color | Material ID | /General |
| `Exclude From White Mode` | bool | Exclude From White Mode | /General |
| `OutlineDepth` | bool | Outline Depth | /General |

This resolves the open question left in `SKILL_STUDIO_CONCEPTS.md`'s Surfaces/Materials section
("Iray exposes a different PBR-oriented channel set... this guide does not cover it") — the table
above **is** that channel set, extracted from a real shipped Iray Uber material. Note the legacy
guide's simple channel names (Diffuse Strength, Glossiness, Bump Strength, Displacement Strength)
*do* survive into Iray Uber essentially unchanged in name — it's additive (110 channels vs. the
legacy ~8), not a wholesale rename. `float_color` channels should use `setFloatColorValue`/
`getFloatColorValue` per SKILL_DAZSCRIPT.md's linear-color guidance, not `setColorValue`.

## `scene` — what actually gets applied on load

This is the part that matters for **hand-authoring or generating** a preset programmatically. A
material preset's `scene` block does not set channel values directly — it uses an
**animation-track addressing scheme** with a single keyframe at frame 0, even for a non-animated,
single-value preset:

```json
"scene": {
  "materials": [
    {"url": "#Default", "extra": [{"type": "studio/material/uber_iray", "version": "1.1.0.0"}]}
  ],
  "animations": [
    {
      "url": "name://@selection#materials:?extra/studio_material_channels/channels/Bump%20Strength/value",
      "keys": [[0, 20]]
    },
    {
      "url": "name://@selection#materials:?extra/studio_material_channels/channels/Normal%20Map/value",
      "keys": [[0, 0.01]]
    }
  ]
}
```

- `materials[].url = "#Default"` binds to the material named `"default"` in `material_library`.
- Each `animations[]` entry targets one channel via a **DSON property-path URL**:
  `name://@selection#materials:?extra/studio_material_channels/channels/<URL-encoded Channel
  Name>/value`. `@selection` means "whatever's currently selected when the preset applies" — the
  file-format-level mechanism behind the UI fact (SKILL_STUDIO_CONCEPTS.md) that Material(s)
  Presets are Yellow-type content requiring a prior selection.
- `keys: [[frame, value]]` — a single `[0, value]` pair is how a static (non-animated) value
  assignment is expressed, reusing the animation-keyframe mechanism.
- The channel name in the URL path is **URL-encoded from the label/id with spaces as `%20`**
  (`Bump%20Strength`), while the JSON key inside `material_library`'s channel list is the plain
  unencoded `id` string (`"Bump Strength"`) — don't confuse the two representations when generating
  or parsing these paths.

This addressing scheme is very likely what `daz_apply_material_preset` and
`daz_set_material_property` ultimately drive through internally (or an SDK-level equivalent) — it
explains why preset application and direct property-by-name scripting
(`findProperty("Bump Strength")`, SKILL_DAZSCRIPT.md) land on the exact same channel identifier
space. Worth confirming against the SDK/live behavior rather than assumed.

## Material presets: real encoding styles, and a critical precedence gotcha (ground truth from a real installed product)

Confirmed 2026-08-22 by decompiling **all 18** sibling `.duf` files in a real installed
creature-morph addon's `Materials/` folder (`Oso3D/Reynard Addon` for Genesis 8 Male — eight
`preset_hierarchical_material` recolor variants, five `preset_material` eye-effect variants, two
`preset_material` fur-length variants, and two `preset_material` "wet" variants). The first pass at
this analysis (an 8-file subset) reached two conclusions that a full sweep proved **wrong** — see
the correction callout below before trusting anything about `scene.materials[]` in isolation.

**⚠️ Correction to an earlier version of this section — `scene.materials[]` alone can be
misleading; `scene.animations[]` is the one that wins.** The first pass concluded from
`scene.materials[].extra[].channels[]` alone that `... Tail Fur Wet.duf`/`... Fur Wet.duf` set
nothing meaningful, and that `... Eyes Fire.duf`'s two declared textures were unused/orphaned. Both
conclusions were wrong, for the same root cause: **a file can declare a channel's value in BOTH
`scene.materials[]` (inline) AND `scene.animations[]` (keyframe-0) at once, and when they disagree,
the `scene.animations[]` value is the one that reflects the preset's real, intended effect** — the
`scene.materials[]` value can be stale/vestigial boilerplate left over from however the Save dialog
constructed the file. Concretely:
- `Tail Fur Wet.duf` really does do something: `scene.animations[]` sets
  `Highlight Weight = 0.2` and `highlight_roughness = 0.1` (sharper/brighter specular — the literal
  "wet sheen" look) *and* drives six dForce hair-generation **Clumping** channels
  (`PreSim`/`PreRender Clumping 1/2 Curves Density = 1` with a `White.png` density map,
  `Clumpiness = 1`, `Clumping Bias = 0.3`) to make the fur visually clump into wet-looking strand
  bundles — a genuinely well-designed, physically-motivated effect. None of this is visible from
  `scene.materials[]` alone, which for this file has every channel declared `null`.
- `Eyes Fire.duf`'s two textures are **not** orphaned: `scene.animations[]` wires
  `ReynardAdd 1007 Glow Splotchy.png` to `Emission Color`'s `image_file` sub-path on `Cornea` and
  `EyeMoisture`, and `Noise.png` to `Luminance`'s `image_file` sub-path on `Irises`/`Pupils`/
  `Sclera` — a real emissive-glow effect. The original orphan-check bug was a substring search for
  the literal filename (with real spaces) that missed every occurrence inside a `scene.animations[]`
  URL, which stores the same path **percent-encoded** (`Glow%20Splotchy`). **Any orphan/unused-asset
  check must search both the literal name form and its percent-encoded form, and must include
  `scene.animations[]`, or it will produce false "unused" positives like this one did.**

**Practical rule going forward**: never characterize what a preset "does" from `scene.materials[]`
alone. Always also dump `scene.animations[]`, and if the same logical channel (same group + channel
id) is set in both places with different values, trust the `scene.animations[]` one.

### The addressing schemes actually used in `scene.animations[]` (broader than previously documented)

Every entry is `{"url": "<target>#<path>:?<property-path>", "keys": [[0, <value>]]}`. Two
meaningfully different `<target>` forms were confirmed, and they are **not** interchangeable:

- **`name://@selection#materials/<Group>:?...`** — resolves against whatever node is selected when
  the preset is applied. Portable; this is what the five-file first pass saw everywhere (`Eyes
  Fire`/`Tail Fur Wet`/`Fur Wet`/`Fur Length Fluffy`) and what SKILL_PACKAGING.md's "Yellow content,
  requires a prior selection" behavior maps to.
- **A literal, scene-specific internal node name** — e.g. `Genesis8Male#materials/Face:?...` or
  `dForce%20Hair-1#materials/Face:?...`, with no `name://@selection` prefix at all. **Confirmed only
  in the eight `preset_hierarchical_material` "Color" recolor files**, each of which contains
  **20,000–28,000** such entries — a full property-tree restatement of every channel on every
  material zone, addressed by the *exact node names present in the original vendor's scene at save
  time*, not a portable selection-relative reference. Two consequences:
  1. This is almost certainly why applying one of these files via `daz_load_file` or
     `App.getContentMgr().openFile()` produced no visible change in live testing (see below) — the
     fur-color entries target nodes literally named `dForce Hair`, `dForce Hair-1`, etc. (separate
     strand-based hair prop nodes conformed to the figure, not surface groups on Genesis 8 Male
     itself), which simply don't exist unless the full addon's fur-hair-prop setup is loaded. The
     skin-material entries target a literal `Genesis8Male` — which *would* match a freshly-loaded
     base figure by Daz's default naming, but turned out to just restate the figure's own unchanged
     Iray Uber defaults (see below), so no visible difference was expected there either way.
  2. **A preset built this way is not safely reusable on a differently-named scene graph.** If the
     user has renamed the figure, or has more than one Genesis 8 Male loaded (`Genesis8Male-1`,
     `Genesis8Male-2`, ...), these hardcoded-name entries silently target nothing. Don't assume
     every Material Preset uses `@selection` addressing — check for hardcoded node names before
     assuming a preset is portable.
  Given this, `daz_apply_material_preset`/`App.getContentMgr().openFile()` remains **confirmed
  working** for whole-shader promotion and (presumably) for genuinely `@selection`-addressed
  presets — the negative live-testing result below is best explained by missing target nodes and
  hardcoded naming, not a broken apply mechanism in general. Retesting against a file that uses only
  `name://@selection` addressing, with the correctly-named target actually present, is the natural
  follow-up and is **not yet done**.

### What the eight "Color" recolor variants actually change (corrected)

All eight share **byte-identical** `scene.materials[]`-inline `Hair Tip Color` values
(`[0.7297401, 0.5325205, 0.3511192]`, a plain tan) — this looked like a copy-paste bug in the first
pass, but per the precedence rule above it's vestigial: the `scene.animations[]` entries that
actually apply reset `Hair Tip Color` to pure white `[1, 1, 1]` on every real target node (`dForce
Hair`, `dForce Hair-1`, ...) instead. **The real per-variant differentiation is an
`<image_file>` texture wired to `Root/Tip Transmission Color` and `Hair Root/Tip Color`** — a
uniquely-named `ReynardAdd <VariantName> FurColor.png` per file (confirmed distinct filenames:
`GingerFox`, `BatEaredFox`, `MarbleFox`, `RedBlackFox`, `RedTippedBlackFox`, `SilverFox`,
`SpiritFox`, `TanFox`) — with the flat tip-color tint kept neutral white specifically so it doesn't
recolor the pattern texture. **`Snow Fox` is a genuine, deliberate outlier, not a broken file**: it
skips the fur-texture mechanism entirely (no `Hair Tip Color` override, no per-variant `FurColor`
texture — relying on the shader's own pale/white default for its "snow" look) and instead retints
the **eyes**: `Pupils`/`Irises`/`Sclera`'s `diffuse` channel gets a `Reynard 1006 Blue BaseColor.png`
`image_file` — a believable "snow fox has pale blue eyes" design choice with a completely different
mechanism than the other seven variants.

### Reference-and-patch and full-bake styles (still real, now correctly scoped)

Two more styles genuinely exist in `scene.materials[]`/`material_library`, but per the correction
above, only trust them for a file where no `scene.animations[]` entry contradicts them:

- **Reference-and-patch** (`scene.materials[]` entries only, `"url": "#<ExistingGroupName>"` or a
  shared external shader-brick path): declares a channel list where only genuinely-changed channels
  carry non-null `value`/`image`, everything else stays `null` (metadata: "exists on the target,
  don't touch it"). Confirmed as the base layer the hierarchical Color/Wet/Eyes files build on top
  of with `scene.animations[]`.
- **Full-bake self-reference** (`material_library[]` holds complete material definitions;
  `scene.materials[].url = "#<id>"` self-references a same-file `material_library[].id`): every one
  of the ~115 Iray Uber channels populated explicitly. Confirmed on the same product: the skin
  (`Face`/`Torso`/`Arms`/etc.) `material_library` entries in every "Color" file are a full bake of
  Genesis 8 Male's **unchanged default** Iray Uber material (`diffuse` = stock `0.7529412` grey) —
  these recolor presets never touch skin tone, only fur; the Save dialog captured and restated the
  unchanged skin material anyway.

**Practical implication for hand-authoring your own preset**: prefer `name://@selection`-addressed
`scene.animations[]` entries (`.../channels/<Name>/value` and, for textures, `.../<Name>/image_file`)
over a bare `scene.materials[]` patch — it's the form confirmed to carry the actually-applied value
in every file where both exist, and it's portable across differently-named scenes. Reserve a
full-bake `material_library` entry for when you need to guarantee an exact from-scratch state
regardless of the target's prior values.

### Minimal hand-authored template — write format AND scripted apply both confirmed live

The first attempt at this template used a bare `scene.materials[]` patch (Style 2/3 above) and
**failed to apply** via both `daz_load_file` and `App.getContentMgr().openFile()` — even the real,
unmodified `ReynardAdd Color Ginger Fox.duf` produced no visible change applied that way. Following
the precedence rule discovered above (`scene.animations[]` is what actually applies), the fix was to
address the channel through `scene.animations[]` instead of a bare `scene.materials[]` patch —
**confirmed live 2026-08-22, this works:**

```python
import gzip, json

duf = {
    "file_version": "0.6.0.0",
    "asset_info": {
        "id": "/My%20Presets/VangardTest/TorsoRecolor.duf",
        "type": "preset_material",
        "contributor": {"author": "Vangard", "email": "", "website": ""},
        "revision": "1.0",
        "modified": "2026-08-22T00:00:00Z",
    },
    "scene": {
        "animations": [
            {
                "url": "name://@selection#materials/Torso:?diffuse/value",
                "keys": [[0, [0.6, 0.1, 0.1]]],
            }
        ]
    },
}

with open("TorsoRecolor.duf", "wb") as f:
    f.write(gzip.compress(json.dumps(duf).encode("utf-8")))
```

Applied via the same script-level codepath `daz_apply_material_preset` uses
(`Scene.selectAllNodes(false); node.select(true);` then
`App.getContentMgr().openFile(path, new DzFileIOSettings(), false)`), against a freshly-loaded real
Genesis 8 Male: `Torso`'s `getBaseColor()` read back `{red: 0.325, green: 0.0063, blue: 0.0063}`
afterward — the exact gamma-decoded (2.2) form of the linear `[0.6, 0.1, 0.1]` written, confirming
both that the value round-trips correctly and that **`App.getContentMgr().openFile()` genuinely
does apply a hand-authored `scene.animations[]`-addressed preset** — the earlier negative result was
caused by using the wrong addressing style (a bare `scene.materials[]` patch), not by the apply
mechanism itself.

For a **texture** instead of a flat value, use the same `<target>#materials/<Group>:?...`
path with `/image_file` in place of `/value` (confirmed above from `Eyes Fire.duf`'s glow-texture
wiring and the Color-variant fur-pattern wiring): e.g.
`"name://@selection#materials/<Group>:?extra/studio_material_channels/channels/<Channel%20Name>/image_file"`
with `"keys": [[0, "<content-root-relative path, %20-encoded>"]]`. For the `diffuse` shortcut
specifically, drop the `extra/studio_material_channels/channels/<Name>/` segment entirely — it's
`?diffuse/image_file` directly, as seen above.

`name://@selection#materials/<Group>:?...` requires the group to already exist on whatever node is
selected when applied (check via `daz_list_materials`) — it does not create a new group. Avoid the
literal-node-name form (`<NodeName>#materials/<Group>:?...`) for anything meant to be reusable —
it only matches a scene with a node of that exact internal name (see the addressing-schemes section
above). Save uncompressed (skip `gzip.compress`, write raw `json.dumps(...)` bytes) if you want to
hand-edit the file afterward — Daz Studio reads both forms transparently (see "Compression &
container" above).

### Real-world gotchas confirmed from the same product (useful for a packaging-review pass)

- **A `Materials/` folder file is not necessarily a material preset at all.** A sibling file in the
  same folder, same vendor naming convention (`... Fur Length Fluffy.duf`), has an **empty**
  `scene.materials` array and is entirely `scene.modifiers[]` — six dForce hair-generation-channel
  adjustments (`asset_info.type` is still `preset_material`, which doesn't disambiguate this
  either). **Check `scene.materials` vs. `scene.modifiers` directly — don't infer preset content
  from folder location, filename, or `asset_info.type`.**
- **Applying a hair-shader-group preset silently bundles a full dForce Simulation Settings reset.**
  Every hair-group material entry (Style 2, external-brick URL) in this product ships alongside a
  `scene.modifiers[]` entry `{"url": "#DZ__SPS_<Group>", "parent": "name://@selection:"}`
  referencing a `modifier_library` entry with **135** Simulation-tab channels (Friction, Collision
  Layer, Density, every Hair Generation/Pre-Sim/Pre-Render tweak) — Daz's Save Material(s) Preset
  dialog scoops up a strand-based hair surface's entire simulation-settings modifier along with its
  material, whether intended or not. **Applying one of these presets overwrites whatever dForce
  simulation tuning was already dialed in on that surface.** Worth flagging to a user before
  applying, and worth deliberately stripping this modifier back out if hand-authoring a
  material-only preset from a UI-driven Save.
- **`asset_info.id` can reference the wrong file — confirmed real, not hypothetical.** The analyzed
  `... Tail Fur Wet.duf`'s `asset_info.id` field reads `.../ReynardAdd%20Fur%20Wet.duf` — the
  *body* fur variant's filename, not its own. The vendor evidently cloned the body preset to make
  the tail one and never updated the embedded id. Reinforces the existing caution above: never
  trust `asset_info.id` as a "what file is this" check.
- **Checking whether an `image_library` entry is actually used requires searching
  `scene.animations[]` with the percent-encoded filename, not just `scene.materials[]`'s `image`
  field with the literal name.** An earlier pass of this analysis wrongly concluded `... Eyes
  Fire.duf`'s two textures (`ReynardAdd 1007 Glow Splotchy.png`, `Noise.png`) were unused, because
  it searched for the literal (space-containing) filename and only checked `scene.materials[]` —
  both textures are in fact wired via `scene.animations[]` `.../image_file` entries (see the
  correction callout above), just addressed with `%20` in place of spaces. Any orphan-asset check
  needs to search both the literal and percent-encoded forms of every `image_library` name, across
  `scene.materials[]` **and** `scene.animations[]`, before concluding something is unused.
- **`extra[].item_post_load_script` entries can reference completely unrelated third-party
  products.** The same `Eyes Fire.duf`'s eye-surface entries carry `item_post_load_script` extras
  pointing at two other vendors' Genesis 8 Male hair products (`Soto/Dolb`, `Soto/Maxx`) — almost
  certainly scooped up because those items were also present/loaded in the original author's scene
  at save time, not anything intentionally part of this preset. A packaging-review pass (see
  `SKILL_PACKAGING.md`'s morph-export EULA check) should also flag stray, out-of-scope
  `item_post_load_script`/cross-product references picked up by an over-broad Save-dialog selection.

## `modifier_library` — morphs and ERC/JCM formulas (figure/prop products)

Ground truth added 2026-08-11 from decompiling two more real shipped products: a wardrobe item
(`IM00091633-01_dForceReadyToWearOutfitforGenesis9.zip`) and a full character
(`IM00091643-01_DAVYasakiforGenesis9.zip`). This is the missing piece for anything geometry/morph-
related — SKILL_PACKAGING.md and SKILL_RIGGING.md both describe the *workflow* (ERC Freeze,
DzERCLink) but not the actual on-disk representation those tools produce. Here it is.

### Morph deltas

A morph's `modifier_library[].morph` block:
```json
"morph": {
  "vertex_count": 25182,
  "deltas": {"values": [[0, 0.008783985, 1.525879e-05, 9.536743e-07], [1, -0.03922601, 0, ...], ...]},
  "hd_url": "/data/.../<same basename>.dhdm"
}
```
`deltas.values` is a **sparse list**: each entry is `[vertex_index, dx, dy, dz]`, only for vertices
actually moved by the morph — not one entry per `vertex_count`. `hd_url` (optional) points to a
same-basename **`.dhdm`** file carrying the higher-subdivision-level sculpt detail as a separate
proprietary binary blob (magic bytes `d0 d0 d0 d0 01 00 00 00`, not gzip/JSON — not reverse-
engineered further here). An HD character morph therefore ships as a `.dsf` (base-resolution
deltas + metadata) paired 1:1 with a `.dhdm` (HD delta layer) of the same name.

### ERC formulas — the real wire format behind DzERCLink/DzERCFreeze

A Joint Corrective Morph (JCM) modifier carries a `formulas` array — a **stack-machine expression**
that computes the morph's dial value from other properties. Real example, a shoulder-bend
corrective gated by whether the character's own HD body morph is active:

```json
{
 "id": "DAV Yasaki_body_cbs_shoulderup_z55n_r",
 "presentation": {"type": "Modifier/Corrective", ...},
 "channel": {
   "id": "value", "type": "float", "visible": false, "auto_follow": true,
   "value": 0, "min": 0, "max": 1, "clamped": true
 },
 "region": "Actor",
 "group": "/People/Hidden/DAV Yasaki",
 "formulas": [
  {
   "output": "Genesis9:#DAV%20Yasaki_body_cbs_shoulderup_z55n_r?value",
   "operations": [
    {"op": "push", "url": "r_shoulder:/data/.../Genesis9.dsf#r_shoulder?rotation/z"},
    {"op": "push", "val": -0.01818182},
    {"op": "mult"}
   ]
  },
  {
   "output": "Genesis9:#DAV%20Yasaki_body_cbs_shoulderup_z55n_r?value",
   "stage": "mult",
   "operations": [
    {"op": "push", "url": "Genesis9:/data/.../DAV Yasaki G9 HD Feminine Body.dsf#...Body?value"}
   ]
  }
 ]
}
```

- `operations[]` is **RPN/postfix**: `push` a literal (`val`) or the live value of another
  property (`url`, a DSON property path — same `<file>#<id>?<path>` addressing used everywhere
  else in this format), then combine with `mult`/etc. This first formula reads: `(r_shoulder Z
  rotation) × -0.01818182` — i.e. `rotation ÷ -55`, normalizing the shoulder's -55°..0° bend range
  to a 0..1 morph dial value.
- **Multiple `formulas` entries with a `stage` key chain together** — the second entry here has
  `"stage": "mult"`, meaning its result *multiplies into* the first formula's output rather than
  overwriting it. Here that second stage multiplies the corrective's strength by the value of the
  vendor's own `...HD Feminine Body` master morph dial — **so this JCM only activates when this
  specific character's HD body shape is dialed in**, and stays inert on a differently-shaped
  Genesis 9. This is how a vendor ships character-specific correctives without them corrupting
  other characters' shapes — confirmed mechanism, not previously documented anywhere in this
  project.
- `channel.visible: false` + `group: "/People/Hidden/<Vendor>"` — corrective morphs are shipped
  hidden from the Parameters pane's normal browsing (the "Hidden" group convention), only reachable
  through the ERC chain or by enabling Hidden Properties (same escape hatch documented in
  SKILL_PACKAGING.md's Smoothing Type troubleshooting recipe).
- `channel.auto_follow: true` is the on-disk flag for what the UI calls an auto-follow/ERC-driven
  property (as opposed to a plain user-dialed morph).
- `presentation.type: "Modifier/Corrective"` is a real, formal type tag for JCM-class modifiers.

This is almost certainly what `DzERCFreeze`/`DzERCLink.addKeyValue()` (SKILL_RIGGING.md) produce
under the hood when you freeze a pose-driven correction in the UI or via script — worth confirming
directly (freeze one live, diff the resulting `.dsf`), but the shape strongly matches.

### Character Presets reference morphs, they don't embed them

A Character Preset's (`asset_info.type: "character"`) `scene.modifiers[]` array **references
existing morphs by URL and sets a dial value** — it does not embed morph deltas at all:
```json
{
  "id": "body_bs_Navel_HD3",
  "url": "/data/Daz%203D/Genesis%209/Base/Morphs/Daz%203D/Base/body_bs_Navel_HD3.dsf#body_bs_Navel_HD3",
  "parent": "#Genesis9",
  "channel": {"id": "value", "type": "float", "value": 1, "current_value": 1}
}
```
This is the on-disk mechanism behind SKILL_PACKAGING.md's EULA rule ("never embed someone else's
morph deltas — use Reverse Deformation instead"): a compliant Character Preset is *just a list of
references to morphs that already exist* (the base figure's own morphs, or the vendor's own
separately-shipped ones) plus dial values — never a copy of someone else's delta data.

## A complete real conforming prop, end to end (ground truth — geometry, rigging, and skinning)

Confirmed 2026-08-22 by decompiling a real, simple, fully-shipped conforming prop
(`Oso3D`'s "Otter Tail" for Genesis 8 Male — a Pattern A item per the two-pattern split above: new
geometry, own bone chain, conforms to a base figure). This is the piece that section was missing —
it described the *file layout* but not how a prop's actual geometry/rigging/skinning is encoded.
Two files matter: the thin wrapper `.duf` (what's in `Content/People/.../Props/`) and the real
payload `.dsf` it references (under `data/<Vendor>/<Product>/`, **not necessarily gzip-compressed**
— this one was plain JSON despite the `.dsf` extension, reinforcing the existing "detect compression,
don't assume it" caution).

### Wrapper `.duf` — `scene.nodes[]` is a thin instantiate-and-override list

```json
{
  "id": "Ottertail6 UVMapped_3733",
  "url": "/data/Oso3D/Otter/Otter%20Tail/Ottertail6%20UVMapped_3733.dsf#Ottertail6%20UVMapped_3733",
  "label": "Otter Tail",
  "parent": "name://@selection:",
  "conform_target": "name://@selection:",
  "geometries": [{"id": "geometry", "url": ".../Ottertail6%20UVMapped_3733.dsf#Ottertail6%20UVMapped",
                  "type": "subdivision_surface", "current_subdivision_level": 1}]
}
```
Followed by **27 more `scene.nodes[]` entries**, one per bone (`hip` → `Tail1`...`Tail17`, plus
`pelvis`/`lThighBend`/`lThighTwist`/`lShin`/`rThighBend`/`rThighTwist`/`rShin`/`abdomenLower`/
`abdomenUpper` reusing Genesis 8's own bone *names* for the segment of skeleton this prop needs to
follow). Each is just `{id, url, name, label, parent, preview}` — **no explicit `"type"` key at
all** on any of these wrapper-level node entries; the real `type` (`"figure"` for the root,
implicitly `"bone"` for the rest) lives in the `node_library` entry the `url` points to, not
restated here. `preview` blocks (`center_point`/`end_point`/`oriented_box`/`rotation_order`) are
**cosmetic viewport-gizmo bounding data only** — flat `[x, y, z]` arrays, not real dial-able
properties; don't confuse them with the payload file's `node_library` fields of the same name (next
section), which are full property objects.

### Payload `.dsf` — `node_library[]`: real properties, not cosmetic previews

The referenced node's *actual* definition, e.g. `center_point`/`end_point`/`orientation`/
`rotation`/`translation`/`scale` are each a **list of one property object per axis**, not a flat
triple:
```json
"center_point": [
  {"id": "x", "type": "float", "name": "xOrigin", "label": "X Origin", "value": 0, "min": -10000, "max": 10000},
  {"id": "y", "type": "float", ...}, {"id": "z", "type": "float", ...}
]
```
`"type": "figure"` lives here (on the root node only — bone nodes' `type` wasn't inspected in
detail but the same file/library split applies). This confirms the general rule: **the wrapper
`.duf`'s `scene.nodes[]` entries are overrides on top of whatever the referenced `node_library`
entry already defines — absence of a field in the wrapper means "use the payload's own value," not
"this field doesn't exist."**

### `geometry_library[]` — the actual polymesh (vertices + polygons), fully ground-truthed

```json
{
  "id": "Ottertail6 UVMapped", "name": "geometry", "type": "subdivision_surface",
  "edge_interpolation_mode": "edges_only", "subd_normal_smoothing_mode": "smooth_all_normals",
  "vertices": {"count": 3733, "values": [[0.0026, 91.408, -7.327], [9.502, 100.72, -9.654], ...]},
  "polygon_groups": {"count": 18, "values": ["Tail17", "Tail16", ..., "Tail1", "Hip"]},
  "polygon_material_groups": {"count": 1, "values": ["Tail"]},
  "polylist": {"count": 3728, "values": [[17, 0, 85, 84, 86], [17, 0, 86, 84, 87], ...]},
  "default_uv_set": "/data/Oso3D/Otter/Otter%20Tail/UV%20Sets/Oso3D/Base/default.dsf#default",
  "root_region": {"id": "Actor", "children": [{"id": "Hip", "map": {"count": 3728, "values": [0,1,2,...]}}, ...]},
  "graft": {"vertex_count": 16384, "poly_count": 16196,
            "vertex_pairs": {"count": 84, "values": [[0, 4], [1, 1300], ...]}},
  "extra": [{"type": "studio_geometry_channels", "channels": [
    {"channel": {"id": "SubDRenderLevel", "type": "int", "value": 0}}, ...]}]
}
```
- **`vertices.values`**: flat list of `[x, y, z]` positions, index = vertex index used everywhere
  else in this geometry (polylist, weight maps, region maps, graft pairs).
- **`polylist.values`**: each entry is `[material_group_index, polygon_group_index, v0, v1, ...,
  vN]` — a **variable-length** vertex-index loop (this file is all triangles, 3 trailing indices;
  quads would have 4). The two leading integers index into `polygon_material_groups.values` and
  `polygon_groups.values` respectively — **not vertex indices themselves.**
- **`polygon_groups`** here are literally named after the bones (`"Tail17"`, ..., `"Hip"`) — a real,
  observed convention (face/smoothing groups mirroring the bone primarily responsible for them),
  not a schema requirement.
- **`root_region`**: a hierarchical tree (one node per body-region/bone, nested `children`) where
  each entry's `map` is a flat list of **polygon indices** belonging to that region — this is very
  likely what backs per-region Smoothing Modifier collision protection and similar region-scoped
  UI, not something this project has directly exercised yet.
- **`graft`** (new, not previously documented in this project): the mechanism a conforming
  accessory uses to seamlessly blend its geometry into a base figure at the attachment seam —
  `vertex_pairs.values` are `[thisPropVertexIndex, baseFigureVertexIndex]` pairs, mapping this
  prop's boundary vertices onto the corresponding vertices on the figure it conforms to (Genesis 8
  Male here) so normals/geometry blend smoothly across the seam instead of showing a hard edge.
  `vertex_count`/`poly_count` in this block describe the **base figure's** full mesh (Genesis 8
  Male's 16384 verts / 16196 polys), not this prop's own — confirmed by the numbers matching
  Genesis 8's known topology, not the Otter Tail's 3733/3728.

### `modifier_library[]`'s `"SkinBinding"` entry — the real weight-map format

This is the piece that makes `conform_target` (documented earlier in this file) actually work —
without it, `conform_target` alone is a confirmed dead end per SKILL_RIGGING.md:
```json
{
  "id": "SkinBinding", "name": "SkinBinding", "parent": "#geometry",
  "skin": {
    "node": "#Ottertail6%20UVMapped_3733",
    "geometry": "#Ottertail6%20UVMapped",
    "vertex_count": 3733,
    "joints": [
      {"id": "Tail17", "node": "#Tail17",
       "node_weights": {"count": 1255, "values": [[84, 1], [85, 1], [86, 1], ...]}},
      ... one entry per bone (24 here) ...
    ],
    "selection_map": { /* not inspected in detail */ }
  },
  "extra": [{"type": "skin_settings", "binding_mode": "General", "general_map_mode": "DualQuat",
             "scale_mode": "BindingMaps", "auto_normalize_general": true,
             "auto_normalize_local": true, "auto_normalize_scale": true}]
}
```
- **`skin.joints[].node_weights.values`** is a **sparse per-vertex weight list**: `[vertex_index,
  weight]`, one entry per vertex actually influenced by that joint (not one per `vertex_count`) —
  the same sparse-list convention as morph `deltas.values` (documented above) and
  `DzMorphDeltas.calculateDeltas()`'s live-confirmed output shape.
- The wrapper `.duf`'s own `scene.modifiers[]` entry for `"SkinBinding"` just references this by
  url + `parent: "#geometry"`; the actual weight data lives entirely in the payload file's
  `modifier_library`, never duplicated in the wrapper.
- `general_map_mode: "DualQuat"` (dual-quaternion skinning) is the modern default; `"General"`
  binding mode and the `auto_normalize_*`/`BindingMaps` scale settings are what the Transfer
  Utility/rigging tools write when weight-mapping a new item — worth treating as the standard
  values to reuse rather than guessing at alternatives if hand-authoring a skin binding.

### Base-figure morph fix, alongside the skin binding

The same prop ships a `"Tail Fix"` modifier (`scene.modifiers[]` in the wrapper, deltas in a
sibling `Morphs/Oso3D/Base/Tail Fix.dsf`) with `channel.current_value: 1` and
`group: "/Morphs/Morph Loader"` — an **always-on** corrective baked into the prop at full strength,
as opposed to a user-dialable JCM (which would ship `value: 0`, dialed in only under specific pose
conditions via ERC formulas, per the ERC section above). `current_value: 1` with no formulas is the
on-disk signature of "this always applies once the prop is loaded," not "this is a slider."

## Render settings — the real Iray `RenderOptions` schema (resolves the biggest open question)

Every prior version of this doc flagged Iray's actual render-settings property surface as unknown.
**Resolved 2026-08-11** by decompiling Daz's own `IM00013176-42_DefaultResourcesForDAZStudio423.zip`
("Default Resources for DAZ Studio") — both a narrow `Preset/Render-Settings` asset
(`Render Presets/Iray/Sun Dial Set.duf`, `asset_info.type: "preset_render_settings"`) and a full
bundled scene (which always embeds the complete current render settings) were inspected. The scene
gives the full picture.

### Where it lives

`scene.extra[]` (same array shape used for `studio_material_channels` on materials) carries a
`{"type": "studio_render_settings", "render_options": {...}}` entry. Top-level `render_options`
fields (a mix of generic/legacy fields still present in the container plus the modern Iray-specific
ones): `active_renderer` (confirmed real class name: **`"DzIrayRenderer"`**), `aspect_ratio`,
`imageSize` (`[w, h]`), `renderType`, `renderStyle`, `rayTraceDepth`, `openGLPasses`, `useGLSL`,
`isCurrentFrameRender`, `useMotionBlur`/`motionBlurPct`/`motionBlurSamples`, `xPixelSamples`/
`yPixelSamples`, `shadowSamples`, `shadingRate`, `doubleSided`, `gain`, `gamma`, `pixelFilter`,
`xFilterWidth`/`yFilterWidth`, `gammaCorrection`. (Several of these — `rayTraceDepth`,
`shadowSamples`, `shadingRate` — are the exact legacy 3Delight fields from
`SKILL_STUDIO_CONCEPTS.md`'s Rendering section; the container format never dropped them, Iray's
settings are additive via `render_elements` below, not a replacement schema.)

### `render_elements` — the actual Iray settings panels, with real channel names

```json
"render_elements": [
  {"id": "General Render", "channels": [
    {"channel": {"id": "Auto Headlamp", "type": "enum", "current_value": 0}},
    {"channel": {"id": "Post Process Script", "type": "file", "file_filter": "DAZ Script (*.dsa *.dsb *.dse)"}}
  ]},
  {"id": "NVIDIA Iray Render Options", "channels": [ /* 26 channels, see table */ ],
   "children": [
     {"id": "NVIDIA Iray Photoreal Options", "channels": [ /* 26 channels */ ]},
     {"id": "NVIDIA Iray Interactive Options", "channels": [ /* 23 channels */ ]}
   ]}
]
```

**`NVIDIA Iray Render Options`** (26 direct channels — the top-level Render Settings pane):
`Render Mode` (enum), `Min Samples`, `Max Samples`, `Max Time` (seconds), `Rendering Quality
Enable`, `Rendering Quality SSIM`, `Rendering Quality` (float), `Rendering Converged Ratio`
(display-as-percent float), `Progressive Aux Canvas`, `Post SSIM Available`/`Enable`/`Predict
Target`/`Max Memory`, `Pixel Filter` (enum) + `Pixel Filter Radius`, `Post Denoiser Available`/
`Enable`/`Start Iteration`/`Max Memory`/`Denoise Alpha`, `White Mode Enable` + `White Mode Color`
(float_color) + `White Mode BSDF Weight` (float_color), `Section Caps Enabled` + `Section Caps
Color` (float_color), `Active Canvas` (enum).

**`NVIDIA Iray Photoreal Options`** (26 channels — the "Photoreal" render-mode sub-panel):
`Min Update Samples`, `Update Interval`, `Default Alpha LPE` (enum) + `Custom Alpha LPE` (string),
`Max Path Length`, `Max SSS Path Length`, `Caustic Sampler`, `Guided Sampling`, `Instancing
Optimization` (enum), `Ray Tracing Low Memory` (enum), `Texture Compression` (enum) + `Texture
Compression Medium/High Threshold`, `Firefly Filter Enable`, `Nominal Luminance`, `Noise Degrain
Filtering`/`Radius`/`Blur Difference`, `Bloom Filter Enable`/`Radius`/`Threshold`/`Brightness
Scale`, `Spectral Rendering Enable` + `Spectral Conversion Color Space`/`Intent` + `Spectral
Observer` (all enum).

**`NVIDIA Iray Interactive Options`** (23 channels — the "Interactive"/NPR-ish render-mode
sub-panel): `Occlusion Mode` (enum), `Ambient Intensity` (float_color), `Ambient Falloff Min/Max
Distance`, `Ambient Falloff`, `Ambient Falloff Distance Space` (enum), `Indirect Light Mode` (enum),
`Indirect Outlier Rejection`, `Ambient Shadow Mode` (enum), `Shadows` (bool), `IBL Falloff`,
`Refinement Mode` (enum), `Max Ray Bounces`, `Max Reflection Bounces`, `Max Refraction Bounces`,
`Ray Importance Threshold`, `First Frame Antialiasing`, `Area As Point Lights`, `Environment Max
Resolution`, `Path Space Filtering (PSF)` + `PSF Geometry Filter`/`Lighting Filter`/`Convergence
Frame`.

This is a comprehensive, real, working Iray settings dump — likely `App.getRenderMgr()
.getRenderOptions()`'s actual property surface for an Iray-active scene (SKILL_DAZSCRIPT.md
documents `opts.renderImgFilename`/`aspectWidth`/`aspectHeight` as confirmed property-assignment
fields on that same object; the channels above should be reachable the same way, or via
`findProperty()` walking the `render_elements` groups — not yet cross-checked against a live
`daz_execute` call). **Caveat**: this was captured from a Daz Studio 4.2.3-era default scene, so a
current build may have added channels since (e.g. a separate Tone Mapping/Environment render_element
panel, common in modern Iray UIs, wasn't present here — only 2 top-level `render_elements` existed:
`General Render` and `NVIDIA Iray Render Options`). Treat this as a strong, real foundation, not
necessarily 100% exhaustive for the newest Daz Studio version.

### Shader `ContentType` taxonomy, extended

Beyond `Preset/Shader/MDL` (Iray) confirmed earlier, this package confirms the sibling legacy/
alternate-renderer families: **`Preset/Shader/RSL`** (3Delight/RenderMan Shading Language — the
literal content type for `DzDefaultMaterial`-era shaders) and **`Preset/Shader/FILA`** (FilaToon, a
bundled third-party toon shader system). `Category` root `/Default/Shaders/3Delight/<Type>` (Glass,
Lights, Metal, Other, Plastic, Skin, Stone, Toon, Utilities observed) is the literal sibling
namespace to `/Default/Shaders/Iray/<Type>` — confirms the legacy/modern split is a first-class
category-tree fork, not just an informal distinction. Also confirmed: `Preset/Render-Settings`
(category `/Default/Render-Settings/Iray`), bare `Prop` (non-conforming built-in props like the Daz
Material Ball), `Scene`, `Script/Documentation`, `Script/Utility` (Daz ships its own utility scripts,
e.g. a "Scene Builder" wizard, as installable content with `Category` root
`/Default/Scene Builder/<Step>` — recognizable if encountered, out of scope to fully catalog here).

## Real DIM store package structure (ground truth)

A store `.zip` (naming convention: `IM<8-digit product ID>-<2-digit part number>_
<ProductNameNoSpaces>.zip`, e.g. `IM00088988-01_SlimeShaders.zip`) contains:

**The `-NN` part number isn't just a generic multi-part split** — confirmed from a real product
shipped as two parts sharing one product ID (`IM00002789-01_Level19DS.zip` /
`IM00002789-02_Level19Ps.zip`, both GlobalID-linked to the same store product #2789): different
parts can be **entirely different content-format variants of the same product** (a modern DSON
version and a legacy Poser-format version), not necessarily sequential pieces of one install. Don't
assume `-01`/`-02` means "half A, half B of one thing" — check `Supplement.dsx`'s `ProductTags` on
each part to see what it actually targets.

```
Manifest.dsx              # DIM install file list
Supplement.dsx            # small per-package descriptor
Content/
  Runtime/
    Support/
      <Name>.dsx           # ContentDBInstall metadata
      <Name>.dsa           # DazScript auto-run snippet — registers the .dsx with the CMS
      <Name>.jpg            # product icon, 114x148 px (confirmed real-world size)
    Textures/<Vendor>/...   # texture maps — 2048x2048 px JPG observed for production diffuse/spec/normal maps
  <Content Type Folder>/<Vendor>/<Product>/   # e.g. "Shader Presets/Marshian/Slime Shaders/"
    <Item>.duf               # the actual asset
    <Item>.duf.png            # 91x91 px — Content Library/Smart Content grid icon
    <Item>.tip.png            # 250x250 px — hover/tooltip preview image
```

### Figure/prop products: two different `data/` payload patterns (resolved)

This was an open question after the Shader Preset analysis — now resolved from two more real
products (a wardrobe item and a full character). There are **two distinct patterns**, and which
one applies depends on whether the item is brand-new geometry or a morph modifying an existing
base figure:

**Pattern A — new geometry (a whole new figure/prop node), e.g. a clothing item:**
```
Content/
  People/<BaseFigure>/Clothing/<Vendor-or-Brand>/<Product>/
    <Item>.duf                     # human-facing reference/wrapper file
    <Item>.png / <Item>.tip.png    # grid icon / tooltip
    Material/<SubItem>/<Preset>.duf + .png + .tip.png   # per-item material variants
  data/<VendorFolder>/<CollectionOrProduct>/<Item>/
    <Item>.dsf                      # the actual DSON geometry/rigging payload
    Morphs/<BaseFigure> or similar subfolders as needed
```
Confirmed real example (`dForce Ready To Wear Outfit for Genesis 9`): wrapper files under
`Content/People/Genesis 9/Clothing/Daz Originals/Ready To Wear Outfit/`, payload under
`Content/data/AF Genesis 9/Ready To Wear/Ready To Wear Hoodie/Hoodie_7724.dsf`. Note the on-disk
vendor folder name (`AF Genesis 9`, matching `asset_info.contributor.author: "AF"` inside the
`.dsf`) **did not match** the storefront-facing `Artists` metadata (`Daz Originals` /
`fefecoolyellow`) — don't assume the `data/` folder segment is a reliable display name; it's
whatever internal author code the tooling used at save time.

**Pattern B — a morph that modifies an existing base figure** (character shapes, HD detail,
corrective/JCM morphs) — the payload installs **into the base figure's own `data/` tree**, not a
separate product-owned one:
```
Content/data/<BaseFigureVendor>/<BaseFigure>/Base/Morphs/<Vendor>/<Product>/
  <MorphName>.dsf          # base-resolution deltas + ERC formulas, see below
  <MorphName>.dhdm         # optional matching HD delta layer (proprietary binary, see below)
```
Confirmed real example (`DAV Yasaki for Genesis 9`): dozens of morphs installed under
`Content/data/DAZ 3D/Genesis 9/Base/Morphs/Dax Avalange/DAV Yasaki G9 HD Feminine/` — i.e. filed
under **Daz's own** `DAZ 3D/Genesis 9/Base` tree, organized into a vendor/product subfolder, rather
than under a `data/Dax Avalange/...` tree of the product's own. **This is the difference between
"this product adds a new node" (Pattern A) vs. "this product modifies Genesis 9 itself" (Pattern B)
— check which one applies before assuming a fixed `data/<Author>/<Product>/` layout.**

A character product commonly ships **both** patterns in one zip: Pattern B for the body/head morphs
that modify Genesis 9 itself, Pattern A for any bundled wardrobe/prop items (boots, helmet, outfit)
that are new geometry nodes.

### Real content-type/category taxonomy observed across three products

Beyond the Shader/Iray branch (`SKILL_PACKAGING.md`), three more `ContentType` families and their
matching `Category` namespace were confirmed:
- **`Actor/Character`** — a full Character Preset (`asset_info.type: "character"` in the `.duf`).
  Category: `/Default/Figures/People/<Gender>/<Style>` (e.g. `Female/Stylized`).
- **`Follower/Wardrobe/<Subtype>`** — confirmed subtypes beyond the wiki's examples: `Footwear`,
  `Full-Body` (a one-piece outfit), `Outerwear/Top`, `Headwear`. Category root:
  `/Default/Wardrobe/<Subtype>`.
- **`Follower/Attachment/Head/Forehead/Eyebrows`** — a deep, specific `Follower/Attachment` path,
  confirming that branch is a real, structured taxonomy and not just the shallow example in the
  wiki docs.
- **`Preset/Materials/MDL`** vs. **`Preset/Materials/Hierarchical/MDL`** — plain vs. hierarchical
  material presets are genuinely distinct content types. A hierarchical preset's `<Compatibilities>`
  list can name *multiple* `CompatibilityBase` targets at once (observed: a jacket material preset
  compatible with the jacket body **and** its zipper-slider and zipper-puller sub-props) — it
  colors the whole fitted assembly in one apply, not just the top-level garment surface.
  Category convention observed: nested per-product folders, e.g.
  `/Default/Materials/Iray/Feminine/<Product Name>/<Skin|Makeup|Nails|Eyebrows|Genitalia|...>`.
- **`Preset/Morph/Apply`** / **`Preset/Morph/Apply/Body`** / **`Preset/Morph/Apply/Head`** and the
  matching **`Preset/Morph/Remove/*`** — a formally-recognized Daz content-type family (with its
  own `Category` roots `/Default/Shaping/Apply/*` and `/Default/Shaping/Remove/*`) for **modular
  HD-morph installation**: separate "Apply Head" / "Apply Body" / "Apply Complete" and matching
  "Remove" presets, so a user can layer in just the parts of a character's HD sculpt they want (or
  cleanly strip it back off) rather than getting an all-or-nothing character shape. Worth adopting
  this pattern explicitly when packaging any character product with HD/sculpted detail — it's not
  vendor-specific convention, it's a first-class Daz taxonomy branch.
- **Genesis 9's own modular sub-figure architecture** is visible in the Compatibility values a
  character product declares: separate compatibility bases exist for `/Genesis 9/Base`,
  `/Genesis 9/Eyes`, `/Genesis 9/Eyelashes`, `/Genesis 9/Mouth`, `/Genesis 9/Tears`, and
  `/Genesis 9/Anatomical Elements Female` — Genesis 9 is a main figure plus several auto-fitted
  companion figures, each independently addressable/compatible. Relevant beyond packaging: any MCP
  tool that needs to target "the eyes" or "the eyelashes" specifically on a Genesis 9 figure is
  very likely dealing with a **separate node/figure**, not a sub-part of the main body mesh.
- **`Compatibility` base-path naming is not uniform across figure generations.** The original
  Genesis figure's own base is just **`/Genesis`** (no `/Base` suffix) — confirmed from a real
  wardrobe product for it (`IM00015339-01_AsheForGenesis.zip`) — vs. Genesis 9's `/Genesis
  9/Base`. Don't assume a fixed `/<Figure>/Base` pattern generalizes; check per generation.
- **`Follower/Accessory/<BodyPart>`** confirmed with a real sub-path (`Follower/Accessory/Neck`,
  a scarf) — the accessory branch does get body-part-specific subtyping, matching the wardrobe
  branch's pattern. Also confirmed: **`Preset/Materials`** with no render-engine suffix (vs.
  `Preset/Materials/MDL`) is valid on older content — the `/MDL` suffix isn't mandatory schema,
  older/simpler products omit it.
- **On-disk folder name casing is not consistent even among first-party products**: this same
  product ships textures under `Content/Runtime/textures/` (lowercase) where every other product
  analyzed used `Content/Runtime/Textures/` (capitalized). Windows' case-insensitive filesystem
  papers over this at install time, but an agent doing exact-string path validation against
  `Manifest.dsx`/the support `.dsx` should compare case-insensitively, not assume canonical casing.

### `Set`/Environment products: `ObjectCompatibilities`, and payload files are `SupportAsset` not `Asset`

Confirmed from a real environment product (`IM00002789-01_Level19DS.zip`, Stonemason's "Level 19"):
- Environments use `ContentType="Set"`, category root `/Default/Environments/<Style>/<Subtype>`
  (observed: `Architecture/Interior`), and live under a **new top-level content folder,
  `Content/Environments/<Product>/`** — a sibling to `People/` and `Shader Presets/`, confirming
  "Environments" is a first-class browsable root like the others.
- Unlike the wardrobe/character products, the `data/<Vendor>/<Product>/<Item>/<Item>.dsf` payload
  files (including the per-item `UV Sets/.../default.dsf` files) are **not** listed as their own
  `<Asset>` entries — only the human-facing wrapper `.duf` is. The payload `.dsf` files instead
  appear under `<SupportAssets>`, alongside the textures and icon. **`<Asset>` = independently
  browsable/loadable content; `<SupportAsset>` = anything an Asset depends on but that isn't itself
  meant to be browsed or loaded standalone** — this includes the DSON geometry/UV payload itself,
  not just images. This also confirms saving a UV set as its own `.dsf` file (SKILL_PACKAGING.md's
  UV-replace troubleshooting recipe) is Daz's **normal, intended packaging pattern** for shipped
  content, not just an editing workaround.
- A new schema element, `<ObjectCompatibilities>`, appears at the `<Product>` level (sibling to
  `<Assets>`/`<SupportAssets>`), only observed on this multi-node environment product:
  ```xml
  <ObjectCompatibilities>
   <ObjectCompatibility VALUE="/data/Stonemason/Level%2019/Level/Level19_100328.dsf#Level19_100328" REF="/Level 19/Level"/>
   <ObjectCompatibility VALUE="/data/Stonemason/Level%2019/Elevator_Shaft/Elevator.dsf#Elevator" REF="/Level 19/Elevator_Shaft"/>
  </ObjectCompatibilities>
  ```
  This maps a raw DSON node path (`<file>.dsf#<node id>`) to a friendlier `REF` compatibility
  path — the mechanism that presumably lets a future preset declare `Compatibility="/Level
  19/Elevator_Shaft"` (a clean name) and have the CMS resolve it back to the actual buried node
  inside the geometry payload. Appears to matter for products with multiple independently
  addressable pieces bundled in one geometry file; not seen on the single-node shader/simple-item
  products analyzed earlier.

### Legacy Poser-format content (`.cr2`/`.pp2`/`.pz2`/`.lt2`) — confirmed structure, pre-DSON

Confirmed by decompiling a genuine pre-DSON product still sold as-is
(`IM00002789-02_Level19Ps.zip` — the *same* store product/GlobalID family as the Level 19 DSON
conversion above, shipped as a **separate installer part** for users on older Poser/Daz Studio
versions). No `Content/data/` at all; instead:

```
Content/Runtime/
  Geometries/<Vendor>/<Product>/*.OBJ           # raw geometry, plain Wavefront OBJ
  Libraries/Props/<Vendor>/<Product>/*.cr2       # main prop/figure — Poser's "Character" container
  Libraries/Props/<Vendor>/<Product>/*.pp2       # a simpler static sub-prop
  Libraries/Pose/<Vendor>/MAT <Product>/*.pz2    # material presets — Poser overloads its "Pose" format for this
  Libraries/Light/<Vendor>/<Product>/*.lt2       # light presets
  Textures/<Vendor>/<Product>/*.jpg              # same texture files, byte-identical to the DSON conversion
```

- `.cr2`/`.pp2`/`.pz2`/`.lt2` are **plain-text, brace-delimited** (not JSON, not gzip) — a
  Poser-native declarative format, e.g.:
  ```
  { version { number 4.01 } figureResFile :Runtime:Geometries:stonemason:CB19:Level19.obj
  actor Main:1 { storageOffset 0 0 0  geomHandlerGeom 13 Main } ... }
  ```
  Geometry is referenced externally via a **colon-delimited pseudo-path**
  (`:Runtime:Geometries:stonemason:CB19:Level19.obj`, a legacy Mac-OS-classic path convention Poser
  inherited) rather than embedded — unlike DSON, where `image_library`/`geometry_library` items are
  referenced by ordinary `/`-delimited content-root-relative URLs.
  `.pz2` being reused for material presets (not just poses) is a well-known Poser-era overload —
  don't assume a `.pz2` file is pose data without checking its contents.
- **No Content DB / CMS metadata at all** — no `Runtime/Support/*.dsx`/`.dsa`, no product icon
  triple. `Supplement.dsx` still exists (DIM-level, format-agnostic) but its `ProductTags` reads
  `"DAZStudio4,DAZStudio3,DAZStudioLegacy,Poser9,PoserLegacy"` instead of a single `DAZStudio4_5`
  tag — a signal this content predates the Smart Content/CMS system entirely. `Manifest.dsx`'s
  shape (`DAZInstallManifest`/`GlobalID`/`<File TARGET="Content" ACTION="Install">`) is **identical**
  between the Poser and DSON packages — the DIM installer wrapper is fully decoupled from the
  content format inside it.
- **Practical implication for an agent**: recognize `.cr2`/`.pp2`/`.pz2`/`.lt2` on sight as legacy
  Poser format, don't attempt to hand-edit or hand-generate them the way `SKILL_DSON_FORMAT.md`
  describes for `.duf`/`.dsf` — they're a different, older ecosystem. If asked to "package" or
  "fix" one, the practical path is loading it into Daz Studio and re-saving through the normal DSON
  save workflow (SKILL_PACKAGING.md), not editing the Poser text format directly.

### Application/Software installer packages — a completely different Manifest shape

Confirmed from `IM00004222-01_Hexagon25Win.zip` (the Hexagon 2.5 modeler, a full standalone
application distributed through DIM). This is not a "Content" package at all:

- **No `Content/` folder.** Root instead contains the literal install tree
  (`Hexagon_2.5/DAZ 3D/Hexagon2/...` — `.exe`/`.dll`/data files) plus a `Temp/` folder for
  installer-support files (here, a VC++ redistributable + a batch script to run it).
- `Supplement.dsx`'s `<InstallTypes VALUE="Software"/>` (vs. `Content` for everything analyzed
  above) is the signal for which install pipeline DIM runs.
- `Manifest.dsx`'s `<File>` entries carry a **much richer attribute set** than any Content package:
  `TARGET="Application"` (or `"Temp"` for staging files), plus `VERSION`, `PLATFORM` (`"PC"`),
  `TYPE` (an app identifier, e.g. `"Hexagon"`), and `ACTION` values beyond `Install`:
  - `ACTION="Execute"` — run a file post-install, with `EXECUTEONINSTALL`/`EXECUTEONUNINSTALL`
    (bool) controlling which lifecycle phase triggers it, and `EXECUTEELEVATED="True"` for
    admin-rights operations (observed on `.dzime` file-association register/unregister scripts).
  - `ACTION="SetVariable"` — defines an install-relative variable (observed:
    `VARIABLE="INSTALL_APP_DIR"` pointing at the app's install folder) for other entries to
    reference.
  - A distinct `<AppMenu>` element (sibling to `<File>`, same attribute style) registers a Start
    Menu shortcut: `PATH` (target exe), `VALUE` (menu path, e.g.
    `"AppMenu/DAZ 3D/Hexagon 2/Hexagon 2.5.2"`).
- **Confirms `Manifest.dsx` is a small general-purpose installer DSL**, not a Content-specific
  format — Content packages just happen to only use its simplest subset (`TARGET="Content"`,
  `ACTION="Install"`). An agent inspecting an unknown DIM zip should check `Supplement.dsx`'s
  `InstallTypes` first to know which shape to expect before parsing `Manifest.dsx`.

### Legacy multi-part product strategy & `.dsx` extension overloading (M4-era ecosystem)

Confirmed from Michael 4's full product family (11 packages spanning base figure, morphs,
genitalia, hand poses, hair, skin maps, and clothing — product numbers `7844`/`7877`/`7878`/
`7966`/`7998`/`8044`). Pre-DSON figures shipped as **coordinated multi-part installs under one base
product number**, not a single zip:
- **`-01`** — the raw legacy Poser content itself (e.g. `Michael4Base` -01: 999 files, almost
  entirely `.pz2` MAT-pose files plus the figure's Poser Character library file, **zero** CMS
  metadata beyond a retroactively-added `Runtime/Support/*.dsx` triple).
- **`-02` "StudioCF"`** — a small companion pack (~17 files) that adds a minimal Daz-Studio-native
  wrapper: a `People/<Figure>/` folder with hand-authored **`.ds`** material-preset *scripts* (a
  real DazScript GUI tool — class-based, uses `App.getAppSettingsMgr()` for persisted settings,
  `shiftPressed()`/`ctrlPressed()` for modifier-key-aware behavior, `getScriptFileName()` — see
  SKILL_DAZSCRIPT.md) so the same underlying legacy content browses sanely inside Daz Studio's
  Materials system, without needing the `.duf`/preset-file mechanism at all.
- **`-03`/`-04` "PwrLoader"** — a **PowerLoader** companion pack: cached mesh/preset delta data
  under `Runtime/libraries/!DAZ/<Figure>/Deltas/*.dsx` plus a compiled
  `Runtime/libraries/Character/<Vendor>/<Figure>.dsb`, for faster loading of a figure with many
  morphs installed. PowerLoader is a defunct pre-DSON performance system, not relevant to current
  content — but it explains the `-PwrLoader` product-name suffix recurring across this figure
  generation's catalog.

**Confirms `Supplement.dsx` and CMS metadata are both genuinely optional, not edge cases**: none of
these 11 packages ship a `Supplement.dsx` at all, and the pure pose product (`M4HandPoses`, `.hd2`
Poser hand-pose files under `Runtime/Libraries/Hand/`) has **no `Runtime/Support/*.dsx` metadata
whatsoever** — it's reachable only via the Content Library's raw "by format and location" browse
mode, never Smart Content, and that's a legitimate, still-functional install state.

**`.dsx` is a heavily overloaded extension — don't assume ContentDBInstall metadata just because of
the extension.** Under `Runtime/Support/`, `.dsx` is the ContentDBInstall schema documented earlier
in this file. Under a PowerLoader `Deltas/` folder, the *same extension* is a completely unrelated
XML schema:
```xml
<PowerLoader PLATFORM="Michael 4" TYPE="MESH">
 <SUBD DEFAULT="false" VALUE="1" />
 <LOD DEFAULT="true"><SOURCE DIR="/Runtime/Geometries/.../..._LOD"><M4_LOD_17K .../></SOURCE></LOD>
</PowerLoader>
```
**Determine a `.dsx` file's actual role from its folder location, not the extension alone.**

**Real-world packaging artifacts worth recognizing, not treating as validation failures**:
`Michael4Base` -01 ships with stray macOS metadata (`.DS_Store`, `.plist` files) and — more
unusually — an **entire bundled macOS helper application**
(`Runtime/libraries/!DAZ/DzCreateExPFiles.app/`, complete with its own embedded Python 2.5
interpreter's `.so` modules) shipped directly inside the content zip. A validation pass shouldn't
hard-fail on unexpected junk or bundled-tool files in an older product; flag for manual review
instead. Other confirmed-real legacy extensions encountered but not deeply parsed here: `.hd2`
(Poser hand pose), `.hr2` (Poser dynamic hair prop), `.mc6` (Poser 6 Material Collection — a
material-only sibling to `.pz2`, texture-focused).

### `.dse` — encrypted/protected DazScript (opaque, but a recognized real format)

Confirmed from a real commercial script product (`IM00068289-01_CharacterConverterfromGenesis2
MaletoGenesis8Male.zip`, RiverSoftArt's Character Converter G2M→G8M). Alongside plain-text `.dsa`
files, this product ships several `.dse` files — a **binary-encrypted** script container:
```
44 41 5A 42  ff ff ff ff  a6 00 03 00 ...    ("DAZB" magic, then binary/encrypted payload)
```
This is Daz Studio's own script-protection format for commercial script products — not readable
without Daz Studio's own decryption, and not something to attempt to reverse for this project (the
whole point is vendors can sell script logic without exposing source). **Recognize it on sight and
don't attempt to read/edit it** — if an agent needs to understand what a `.dse`-based tool does,
the answer is "run it and observe behavior," not "read the file." The product's plain-text `.dsa`
files (constants, UI-building helpers, documentation launchers) are still normal source and
readable — vendors commonly keep non-proprietary scaffolding in `.dsa` and protect only the actual
algorithm in `.dse`. This particular product's algorithm-holding files (the actual G2-to-G8
conversion logic, `RSG2G8CharacterConversionFunctions.dse`) are encrypted — the constants/UI-helper
`.dsa` files confirm the tool's shape (`DEFAULT_TOLERANCE = 0.06`, `DEFAULT_CONVERT_JCMS = true`,
three evolving conversion algorithm generations named "Original/2019/2020 Method") and that it
**writes new packageable content** on completion (`sNewFigurePreset = 'People/%1 %2/'`,
`sBaseFigurePreset = '%1 Basic %2.duf'` — the exact same `People/<Product>/` convention this file
documents elsewhere) — but not the conversion algorithm itself.

Also confirmed from this product: `Script/Documentation` + `Script/Utility` ContentTypes (matching
the Default Resources bundle), category `/Default/Utilities/Scripts` (new, alongside the earlier
`/Default/Scene Builder/*`), and that a script asset can declare a real figure `Compatibility`
(`/Genesis 2/Male` here) for Smart-Content filtering — scripts aren't exempt from the same
Compatibility mechanism geometry/material assets use.

### Non-DIM manual script distribution — a real, common alternative packaging mode

Confirmed from a real community script ("ZGFX dForce Manager", 4-file zip): not all Daz Studio
content is a DIM/store package at all. This one is just:
```
Scripts/<Vendor>/<ScriptName>.dsa
Scripts/<Vendor>/<ScriptName>.png
```
— no `Manifest.dsx`, no `Supplement.dsx`, no `Content/` wrapper, nothing. The user manually unzips
this directly into a mapped content directory root so `Scripts/<Vendor>/` lands where Daz Studio's
Content Library expects scripts. **This is a legitimate, common third-party/free-script
distribution mode** (typical of scripts shared outside the Daz store — forums, ShareCG-style sites,
a vendor's own site) — an agent asked to "install" or "package" a script shouldn't assume every
`.zip` needs the full DIM apparatus documented elsewhere in this file. If asked to package a script
for casual/manual distribution rather than store submission, this minimal shape is the right
target, not a full Manifest/Supplement/ContentDBInstall build-out.

Also confirmed: `new DzAppSettings()` is a real, working settings-persistence class — an
alternative to `App.getAppSettingsMgr()` (SKILL_DAZSCRIPT.md) rather than a broken/deprecated one;
both exist in real shipped scripts.

### `conform_target` — confirmed real usage, clarifies (doesn't contradict) SKILL_RIGGING.md

The wardrobe item's `scene.nodes[]` entry sets `"conform_target": "name://@selection:"` directly —
seemingly at odds with SKILL_RIGGING.md's finding that hand-authoring `conform_target` alone is "a
confirmed dead end" for real deformation. **No contradiction**: this shipped item's node *also* has
a full weight-mapped bone hierarchy matching Genesis 9's skeleton (`hip` → `pelvis` → `l_thigh` →
...), which is exactly what the Transfer Utility computes and bakes in. `conform_target` is a real,
legitimate "auto-fit to the current selection on load" convenience flag — but it rides on top of
proper weight-map data that has to exist first. SKILL_RIGGING.md's dead-end finding was specifically
about setting `conform_target` on a hand-authored figure **without** going through Transfer
Utility's weight computation first — that combination doesn't work; `conform_target` on a properly
weight-mapped node (the normal Transfer-Utility-produced case) does.

### `Manifest.dsx` — DIM's install file list

```xml
<DAZInstallManifest VERSION="0.1">
 <GlobalID VALUE="<uuid>"/>              <!-- matches the Product's GlobalID in the .dsx below -->
 <File TARGET="Content" ACTION="Install" VALUE="Content/Runtime/Support/<Name>.dsa"/>
 <File TARGET="Content" ACTION="Install" VALUE="<relative path under Content/, one per shipped file>"/>
 ...
</DAZInstallManifest>
```
Every file in the package — asset, texture, icon, tooltip, support file — gets its own `<File>`
entry (312 entries observed for a 99-preset product). `TARGET="Content"` was the only value
observed here; an application/plugin install presumably uses a different target, not confirmed.

### `Supplement.dsx` — package-level descriptor

```xml
<ProductSupplement VERSION="0.1">
 <ProductName VALUE="Slime Shaders"/>
 <InstallTypes VALUE="Content"/>
 <ProductTags VALUE="DAZStudio4_5"/>
</ProductSupplement>
```
Minimal — just enough for DIM to label the install. `ProductTags` here is a minimum-Daz-Studio-
version compatibility tag, not a search/marketing tag.

### `<Name>.dsa` — the auto-run script that wires metadata into the CMS

```javascript
// DAZ Studio version 0.0.0.0 filetype DAZ Script
if( App.version >= 67109158 ) //4.0.0.294
{
	var oFile = new DzFile( getScriptFileName() );
	var oAssetMgr = App.getAssetMgr();
	if( oAssetMgr )
	{
		oAssetMgr.queueDBMetaFile( oFile.baseName() );
	}
}
```
**This is the actual mechanism that registers Content DB Editor metadata with the CMS.** Daz Studio
auto-executes every `.dsa` under `Runtime/Support` on a content-directory scan; this one calls
`App.getAssetMgr().queueDBMetaFile(<same basename>)`, which queues the matching `.dsx` in the same
folder for ingestion into the Content Database. This resolves one of `SKILL_PACKAGING.md`'s open
questions: **`DzAssetMgr.queueDBMetaFile()` is a confirmed, real, callable DazScript API.** Worth a
further SDK-header pass to see what else `DzAssetMgr` exposes — this may be the entry point for a
programmatic (non-UI) metadata-registration tool.

### `<Name>.dsx` — ContentDBInstall metadata (the Content DB Editor's real save format)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ContentDBInstall VERSION="1.0">
 <Products>
  <Product VALUE="<Product Name>">
   <StoreID VALUE="DAZ 3D"/>
   <GlobalID VALUE="<uuid>"/>
   <ProductToken VALUE="<numeric store SKU>"/>
   <Artists><Artist VALUE="<Author>"/></Artists>
   <Assets>
    <Asset VALUE="<path relative to Content/, e.g. 'Shader Presets/Marshian/Slime Shaders/SS BloodBlue.duf'>">
     <ContentType VALUE="Preset/Shader/MDL"/>
     <Audience VALUE="Teens"/>
     <Categories><Category VALUE="/Default/Shaders/Iray/Liquid"/></Categories>
     <Tags><Tag VALUE=""/></Tags>
     <Compatibilities><Compatibility VALUE="/AnySurface"/></Compatibilities>
     <!-- items with their OWN identity (a wardrobe piece, a full character) carry this too: -->
     <CompatibilityBase VALUE="/<Product Name>/<Item Name, or omitted for the product root>"/>
     <Userwords><Userword VALUE=""/></Userwords>
    </Asset>
    <!-- one <Asset> block per shipped .duf -->
   </Assets>
   <SupportAssets VALUE="/Runtime/Support/<Name>.dsx">
    <SupportAsset VALUE="/Runtime/Textures/<Vendor>/<...>.jpg"/>
    <SupportAsset VALUE="/<Content Folder>/<...>.duf.png"/>
    <SupportAsset VALUE="/<Content Folder>/<...>.tip.png"/>
    <!-- every texture + every thumbnail/tooltip image: everything an Asset references but that isn't itself a browsable asset -->
   </SupportAssets>
  </Product>
 </Products>
</ContentDBInstall>
```

Confirmed real values for a generic/any-surface shader product: `ContentType` =
`Preset/Shader/MDL`, `Compatibility` = `/AnySurface`, `Category` rooted at
`/Default/Shaders/Iray/<Category>` (observed leaves: `Liquid`, `Wax`, `Emissive`, `Utilities`,
`Utilities/Bump`, `Utilities/Diffuse`, `Utilities/Glossiness`, `Utilities/Tiling`, `Utilities/Top
Coat`, `Utilities/Translucency`). This is real-world evidence for the abstract Content DB Editor
field descriptions in `SKILL_PACKAGING.md` — **`Category` values are literal virtual filesystem-
style paths mirroring the live Daz Studio category tree, not free text.**

Two more real fields confirmed from the wardrobe/character products (absent from the shader
product, which has neither): **`<Tags><Tag VALUE="..."/></Tags>`** (present but empty on every
asset observed so far — schema confirmed, real-world usage not yet observed) and
**`<CompatibilityBase>`**, which only appears on assets that have their own identity for other
content to target — the product-root wearable preset and each individual wardrobe piece each
declare one (root = product name, each item = `<product>/<item>`, exactly matching
`SKILL_PACKAGING.md`'s documented UI convention); plain material/pose presets that only *target* a
base never declare their own `CompatibilityBase`. See "Real content-type/category taxonomy observed
across three products" above for the full taxonomy findings.

## Validation checklist for an agent reviewing a candidate package

1. Zip root has `Manifest.dsx` and a `Content/` folder — nothing else loose at the root.
   **`Supplement.dsx` is common but not guaranteed**: a real shipped product
   (`IM00015339-01_AsheForGenesis.zip`) ships with no `Supplement.dsx` at all. Don't treat its
   absence as a validation failure on its own.
2. Every file that exists on disk under `Content/` has a matching `<File>` entry in `Manifest.dsx`,
   and vice versa — no orphaned files, no manifest entries pointing at missing files.
3. `Manifest.dsx`'s `GlobalID` matches the `<Product><GlobalID>` inside `Runtime/Support/*.dsx`.
4. Every asset `.duf` under a content-type folder has a same-basename `.duf.png` (91×91) and
   `.tip.png` (250×250) alongside it, plus a corresponding `<Asset>` entry in the support `.dsx`.
5. `Runtime/Support/` contains a matching `.dsa` + `.dsx` + product icon (114×148) triple, all
   sharing one basename.
6. Every `<Asset>` entry has a non-empty `ContentType` and at least one `Category`. A
   `Compatibility` of `/AnySurface` is only correct for genuinely generic (non-figure-specific)
   content — figure-specific assets should reference a real Compatibility Base per
   `SKILL_PACKAGING.md`.
7. Don't trust `asset_info.id` inside any individual `.duf` as a product-identity check — it can be
   stale/copy-pasted from an unrelated prior product and nothing validates it. Use the
   Manifest/Supplement/ContentDBInstall metadata instead.
8. For a figure/prop product: confirm which `data/` pattern applies to each shipped item (Pattern
   A: new node under `data/<VendorFolder>/<Product>/<Item>/`, or Pattern B: a morph filed into the
   *base figure's own* `data/<BaseVendor>/<BaseFigure>/Base/Morphs/<Vendor>/<Product>/` tree) —
   don't assume one fixed layout for the whole package; a character product commonly ships both.
9. If the product includes corrective/JCM morphs, spot-check that any `formulas` array with a
   `"stage": "mult"` entry referencing the product's own master morph dial is present where
   appropriate — its absence means the corrective could misfire on other characters' shapes wearing
   the same base figure.

## Building a DIM-installable zip from scratch — live-confirmed 2026-08-12

Everything above this point came from decompiling *existing* store products. This section is the
reverse: a from-scratch minimal package was built by hand and dropped into a real user's DIM
`Downloads/` folder to confirm what DIM actually requires vs. what's optional convention. See
`plugins/daz/skills/daz-dim-packaging/SKILL.md` (AIHelpers hub) for the full step-by-step; this is
the ground-truth record of what was tested.

**A package with just `Manifest.dsx` + `Supplement.dsx` + `Content/<payload>` — no
`Runtime/Support` `ContentDBInstall` `.dsx`/`.dsa`/icon triple at all — is sufficient for DIM to
recognize and correctly list the package.** Test package: a single `Content/Scripts/VangardTest/
HelloWorld/HelloWorld.dsa` file (a one-line `print()` script), zipped as
`IM99999999-01_VangardHelloWorldTest.zip`, dropped into `InstallManager/Downloads/`. After a
manual refresh in DIM, it appeared under "Ready to Install" → "Products" with:
- **Product Name**: read verbatim from `Supplement.dsx`'s `ProductName`.
- **Tag(s)**: a human-readable rendering of `Supplement.dsx`'s `ProductTags` (`DAZStudio4_5` →
  "DAZ Studio 4.5+").
- **Product ID / Package ID**: parsed straight from the filename (`IM99999999-01` →
  `99999999`/`1`), not from `Manifest.dsx`'s `GlobalID` (which is a UUID, unrelated).
- **"Show Package Files"** listed the content path as `/Scripts/VangardTest/HelloWorld/
  HelloWorld.dsa` — confirming the `Content/` prefix in `Manifest.dsx`'s `<File VALUE="...">` is
  stripped for display; the real install target is relative to the content library root, i.e.
  `TARGET="Content"` + `Content/X` installs to `<ContentDirectory>/X`.

**This means the `Runtime/Support` `ContentDBInstall` layer (`.dsx`/`.dsa`/icon triple,
Content-DB-Editor-style metadata) is specifically for Smart Content searchability by
Type/Category/Compatibility — not required for DIM itself to install a package.** Treat it as an
optional second tier, not a mandatory part of "does this zip work in DIM."

**DIM generates its own companion `.dsx` sidecar next to the zip in `Downloads/` — do not
hand-author it.** Every real product in a populated Downloads folder has a matching
`IM<ID>-<part>_<Name>.dsx` sitting alongside its `.zip`. This looked at first like a required
input (it's a `ProductSupplement`-rooted XML, same root element name as the one that goes *inside*
the zip, but with different fields), but a controlled test proved otherwise: the file was removed,
DIM was refreshed with only the `.zip` present, and it regenerated an equivalent file from
scratch. Confirmed schema (fields not seen in the internal `Supplement.dsx`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ProductSupplement VERSION="0.1">
 <ProductName VALUE="<from internal Supplement.dsx>"/>
 <ProductStoreIDX VALUE="<ProductID>-<PackagePart, no leading zero>"/>   <!-- from the filename -->
 <UserOrderDate VALUE="<ISO8601, stamped at scan/refresh time>"/>
 <InstallerDate VALUE="<same as UserOrderDate for a locally-dropped, never-ordered package>"/>
 <ProductFileGuid VALUE="<uuid, freshly RANDOMIZED on every re-scan>"/>   <!-- NOT the internal Manifest.dsx GlobalID -->
 <InstallTypes VALUE="Content"/>        <!-- copied from internal Supplement.dsx if present -->
 <ProductTags VALUE="DAZStudio4_5"/>    <!-- copied from internal Supplement.dsx if present -->
</ProductSupplement>
```
Real examples confirm the same shape: `IM00007844-01_M4HandPoses.dsx` (`ProductStoreIDX="7844-1"`,
no `InstallTypes`/`ProductTags` — that product's internal `Supplement.dsx` presumably lacks them
too) and `IM00002789-01_Level19DS.dsx` (has both extra fields, `ProductTags="DAZStudio4_5,
CloudAvailable"`). `ProductFileGuid` is confirmed ephemeral/random per scan, not a stable hash of
the zip's contents or its internal `GlobalID` — don't rely on it for identity checks across scans.

**Follow-up confirmed the actual install too — full end-to-end, not just "DIM lists it
correctly".** Clicking `Install` in DIM on the Tier 1 test package completed successfully: DIM
moved it from "Ready to Install" to "Installed", its hover tooltip showed a correct
`Installed To: <library path>`, `Installed Size`, and `Install Date`, and the file landed exactly
where `Manifest.dsx` said it should — `<Content Library>/Scripts/VangardTest/HelloWorld/
HelloWorld.dsa` (the `Content/` prefix stripped on install, matching the "Show Package Files"
display behavior noted above).

**Bonus finding**: even this bare Tier 1 package — no `ContentType`/`Category`/icon, no
`Runtime/Support` metadata at all — showed up in Daz Studio's **Smart Content "Products" search**
by product name after install (searching a substring of the product name surfaced it). It renders
with a broken/warning-triangle icon in place of a thumbnail, since there's no icon file and no
`Asset`/`ContentType` registration for Smart Content to categorize it against. **This means the
`Runtime/Support` ContentDBInstall layer is specifically for getting a proper
thumbnail/Type/Category in Smart Content — not for making the product discoverable there at all**,
which was the wrong assumption going in; basic name-searchability comes for free from
`Supplement.dsx`'s `ProductName` alone.

**Tier 2 (the `Runtime/Support` ContentDBInstall triple) confirmed live 2026-08-21 — closes the
one gap the Tier 1 test left open.** Built a second test package, same shape as the Tier 1 one
plus the full triple: `Runtime/Support/<Name>.dsx` (`ContentType="Script/Utility"`, category
`/Default/Utilities/Scripts` — the taxonomy leaf documented above from the RiverSoftArt product),
`Runtime/Support/<Name>.dsa` (the verbatim `queueDBMetaFile()` registration script), a 114×148
product icon, plus a 91×91 grid icon and 250×250 tooltip image on the shipped `.dsa` asset itself.
Dropped in DIM's Downloads folder, installed, then opened in Daz Studio's Smart Content pane:
- The real icon image rendered in the file grid — no broken/warning-triangle placeholder, unlike
  the bare Tier 1 package.
- A **"Script" type badge** appeared on the tile, read directly from the declared `ContentType`.
- The item was filed under a **"Utilities"** node in the left-hand category tree, matching the
  declared `/Default/Utilities/Scripts` `Category` path exactly.
- DIM's own product list/tooltip still matched `Supplement.dsx`'s `ProductName`/`ProductTags`
  verbatim, same behavior as Tier 1.

This confirms the full two-tier model end-to-end: Tier 1 alone is enough for DIM to install and
for Smart Content to find the product by name (with a broken icon); adding the Tier 2 triple is
what turns that into a real thumbnail with correct type/category filtering. Not yet tested by this
process: a package that includes an actual `data/` geometry/morph payload alongside the
ContentDBInstall metadata.

**A non-script `ContentType` confirmed live 2026-08-22 too — the badge/category mechanism
generalizes, not a script-specific quirk.** Built a third test package: a placeholder wardrobe item
(a syntactically-valid but geometry-free `.duf` — this test targets the DIM/ContentDB/Smart-Content
packaging plumbing, not actual cloth-fit correctness) declaring `ContentType="Follower/Wardrobe/
Shirt"`, `Category="/Default/Wardrobe/Shirts"`, `Compatibility="/Genesis 9/Base"`, and its own
`CompatibilityBase="/VangardTest/TestShirt"` (the item-has-its-own-identity case from the taxonomy
notes above, not previously exercised by the script test since a script never declares a
`CompatibilityBase`). Installed via DIM and opened in Smart Content: real thumbnail rendered, a
**"Wardrobe"** type badge appeared (not "Script" — confirmed the badge text is driven by the
declared `ContentType`, not hardcoded), and the item filed under a **"Wardrobe"** category node.
Confirms the Tier 2 mechanism is generic across `ContentType` values, not something that happened
to only work for `Script/Utility`.

## Open questions for future SDK/IDA investigation

- ~~How a reference-and-patch, multi-group Material Preset actually gets applied via script~~ —
  **resolved 2026-08-22**: a bare `scene.materials[]` patch does NOT apply via
  `App.getContentMgr().openFile()`, but a `scene.animations[]`-addressed
  `name://@selection#materials/<Group>:?diffuse/value` entry does (confirmed live, gamma-decoded
  value read back correctly) — see the material-presets section above. Still genuinely open: why the
  real `ReynardAdd Color Ginger Fox.duf` showed no visible change when applied to a bare Genesis 8
  Male — now understood to be because its `scene.animations[]` entries target literal node names
  (`dForce Hair`, `dForce Hair-1`, ...) that don't exist without the full addon's fur-prop setup
  loaded, not a failure of `openFile()` itself — but this hasn't been re-verified against a scene
  that actually has those nodes present.
- What other methods `DzAssetMgr` exposes beyond `queueDBMetaFile()` — worth a full method dump via
  the SDK headers or IDA against the compiled plugin.
- Whether `daz_apply_material_preset`/`daz_set_material_property` internally traverse the same
  `name://@selection#materials:?extra/.../value` path scheme, or a different internal API.
- ~~The equivalent top-level `.duf`/`.dsf` schema for figure/prop/pose products~~ — **resolved
  2026-08-11** by decompiling a wardrobe product and a full character product; see the
  `modifier_library`/ERC-formulas section above and the two `data/` package patterns.
- Whether `DzERCFreeze`/`DzERCLink.addKeyValue()` (SKILL_RIGGING.md) actually produce the exact
  `formulas`/`operations` JSON shape documented above — inferred from a shipped product, not yet
  confirmed by freezing one live and diffing the result.
- The proprietary `.dhdm` binary format (HD morph delta layer) — magic bytes `d0 d0 d0 d0 01 00 00
  00` confirmed, internal structure not reverse-engineered.
- Full `ContentType`/`Category` taxonomy is still partial — five product types observed so far
  (Shader/Iray, Wardrobe, Character, Environment/Set, legacy Poser) out of more that likely exist
  (poses as their own standalone product, animations/aniBlocks, scripts/plugins as content rather
  than full applications).
- `<ObjectCompatibilities>`'s exact purpose/consumer is inferred (DSON-node-path → friendly-
  Compatibility-path mapping) but not confirmed against SDK source or live CMS behavior.
- Whether `daz_load_file`/`daz_load_product` (or any MCP tool) has to special-case
  `Supplement.dsx`'s `InstallTypes` (`Content` vs `Software`) at all, or whether that distinction
  only matters to DIM itself — Application-type packages are almost certainly out of scope for a
  Daz *Studio* automation server, but worth confirming there's no accidental overlap.
