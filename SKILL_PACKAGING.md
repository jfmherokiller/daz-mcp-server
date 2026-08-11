# Skill: Product Packaging & Asset Preparation

Source: `docs.daz3d.com/public/publishing/*` and
`.../software/dazstudio/4/userguide/creating_content/packaging/tutorials/*` (official DAZ 3D
Published Artist documentation, fetched 2026-08-11). Covers preparing, packaging, and
troubleshooting a Daz Studio content product for distribution — not scene-building or rendering.

## Submission process (business workflow, not technical)

Preliminary Review → Full Review → QA and Testing → PA Final Acceptance. At Preliminary Review:
email promo images (**JPEG, 500×650**), a brief description — **do not send actual product files
yet**, and never include nudity. Weak promo lighting/shadow quality is the most commonly cited
rejection cause (shadows visually ground the item). Not useful for technical packaging schema —
included only so an agent doesn't confuse it with the technical steps below.

## File format & folder structure

Current-generation Daz Studio content is `.dsf` (asset/geometry/morph/UV payload) + `.duf`
(scene/preset/character files) — supersedes legacy Poser `.cr2`/`.pz2`. Saving a Figure/Prop asset
produces **two separate trees** that must ship together:

- **Human-browsable reference file** — e.g. `People\Genesis\Clothing\<Product>\<Item>.dsf`
- **Actual DSON payload** — `data\<Author>\<Product>\<Item>\` (include *every* subfolder; texture
  and geometry data live here)

Three sanctioned ways to assemble exactly this set for a zip, no more:
1. **Manual cleanup** — zip the whole content library, then delete everything that isn't this product.
2. **Dual mapped content directories** — a scratch directory used *exclusively* for the product
   being built (nothing else goes there) + a second directory for the installed base content it
   depends on. Whatever lands in the scratch directory is the deliverable.
3. **Content Directory Manager** (Content Library pane → options) — the standard tool for managing/
   isolating mapped directories during packaging.

A support/metadata file lives at `Runtime\Support\<name>.dsx`, with a **product icon of the same
basename** in the same folder (114×148 px current spec, 100×143 px legacy).

## Setting identity before saving (in the live scene)

- **Content Type** — Scene pane → option menu → **Edit → Scene Identification**. Drives Smart
  Content's auto-replacement (swap one same-type item for another, e.g. shoes ↔ shoes). Example
  taxonomy: `Follower/Wardrobe/Shirt`, `Follower/Accessory` (belts/earrings/necklaces),
  `Follower/Attachment` (geografted items). **Special case:** skirts use
  `Follower/Wardrobe/Pant` specifically so they auto-replace correctly against pants.
- **Node Name vs Node Label** — **Tools → Joint Editor** → Tool Settings option menu →
  **Edit → Rename Node**. Node Name = internal identifier written into the data folder; Node Label
  = display name shown in the Scene pane. Two different fields, don't conflate them.
- **Save**: **File → Save As → Support Asset → Figure/Prop Assets**. Save Options dialog's top 3
  required fields: **Author Name** (presettable once in Preferences), **Product Name**, **Item
  Name**. The dialog's Content Database section is low-priority at this stage — real metadata
  entry happens in the Content DB Editor (below), separately.

## Metadata — Content DB Editor

Open: Content Library pane → select the **Products** folder → pane option menu →
**Content DB Editor…**. Two pages:

**Product page:**

| Field | Notes |
|---|---|
| Store | e.g. "DAZ 3D" for store submissions |
| Global ID | Auto-set GUID — **never change once distributed** |
| Token | Store SKU — **QA-assigned; don't finalize metadata before it exists** |
| Description | Optional; shown in Smart Content Info Page |
| Artists | Right-click to add — **must match the store page spelling exactly** |
| Support | Relative path to the `.dsx` file; auto-generated if "Auto Fill" checked |
| Files | Product's asset list; populate via "Add from Directory (Recursive)" |
| Scene IDs | Read-only, auto-populated |

**Assets page** (confirm "Sync Product and Local Database" is checked first):

| Field | Notes |
|---|---|
| Type | Drives content-swap auto-replacement |
| Audience | Age rating (Child/Teen/Adult) |
| Categories | Right-click to add; should mirror store categorization |
| Tags | Recommend artist name + supported figure(s) |
| Description | Leave blank unless behavior is nonstandard |
| Compatibility | See "Compatibility Base vs Compatibility" below |
| Userwords / User Notes | **Leave blank as the content creator** — end-user-only field |

**Compatibility Base vs. Compatibility — two distinct concepts, easy to conflate:**
- **Compatibility Base** = what the item *is* (identity for filtering). Set per-object in the live
  scene: Scene pane → select object → option menu → **Edit → Scene ID Editor…** → **Compatibility
  Base** button → pick or right-click-create. Convention: root base = product name, sub-bases =
  individual item names for multi-item products. **Mandatory for Smart Content filtering to work
  at all** — an item with no Compatibility Base link is invisible to Smart Content's compatibility
  matching.
- **Compatibility (assignment)** = what the item *works with*. Content DB Editor → Compatibility
  sub-page. Applies to material presets, poses, morph injections, auto-parented props,
  multi-fit clothing — items can declare multiple compatible bases.

**Categorization**: Content Library pane → select thumbnail(s) → right-click → **Categorize…**.
Pick the single most specific category; if genuinely multi-category, go up one level rather than
over-tag. Make a product-specific category for product-specific lights, custom-figure clothing,
all materials, or anything non-generic.

**Gotcha**: Content DB Editor metadata and the storefront product page are **separate systems** —
DB metadata does **not** populate store categorization. Keep both in sync manually.

## Artwork standards

| Asset | Dimensions | Render source | Post-production |
|---|---|---|---|
| Main Promo Illustration | 1000×1300 px, portrait | Any software | Fully allowed (Photoshop etc.) |
| Pop-Up Illustration | min 500×650 portrait / 650×500 landscape | **DAZ Studio or Poser only** | Restricted: color correction, sharpening, pass-combining only |
| Shop Page Thumbnail | 240×312 px, portrait | — | Optional if it differs from a scaled main promo |

File format/DPI/bit-depth/background treatment are **not specified** by the source doc — don't
assume PNG or any particular spec; verify at the vendor portal at submission time.

Per-category shot checklist: **People** — full front, full back, portrait close-up, skin-texture
detail (1–4 shots). **Clothing** — front worn, back worn, multi-body-shape comparison, untextured
display, texture swatch. **Hair** — 3/4 portrait, 3–5 morph/texture/angle variations, texture-option
shots, untextured display. **Props** — per-prop close-up, textured + untextured. **Environment** —
multiple angles, textured + untextured. **Poses** — one image showing 3+ poses with the rest as
insets, figures dressed simply or as untextured clay so the pose reads clearly.

Artwork is reviewed **twice** — at Approval and again immediately pre-publication. Expect a
revision round; don't assume one-shot acceptance.

## Saving morphs as distributable assets

Minimum Daz Studio version **4.6.3.52+**. Three related outputs, don't confuse them: **Scene
Saving** (WIP shape, not distributable) vs. **Morph Asset Export** (the actual distributable path)
vs. **Character Preset** (a load-wrapper around a saved shape).

**Create the property first:**
1. Right-click in the Properties pane → **Edit Mode**.
2. Right-click again → **Create New Property**.
3. Fields: **Name** (internal id), **Label** (user-facing slider name), **Path** (`Actor/Full
   Body/` for split head/body shapes, `Actor/People/` for a combined full-shape scale), **Type** =
   `Modifier/Shape`, **Min** = `0` (recommended), **As Percent** = typically `No`.
4. Right-click the new property → **ERC Freeze** — this is what actually activates the slider;
   skipping it leaves the property inert.

**Export**: **File → Save As → Support Asset → Morph Asset(s)…** — dialog fields: Asset Directory
(verify pre-filled path), Vendor Name (optional), Product Name, Properties (checkbox list of which
created properties to export).

**Character Preset (optional wrapper)**: **File → Save As → Character Preset…** → `.duf`.
Character Data dialog: Shape Settings / Material Settings / Compress File checkboxes. Icon: **91×91
px PNG**, filename must exactly match the `.duf` basename.

**Legal/compliance gotcha (hard EULA rule):** *"Embedding someone else's morphs, even if you change
them further, is in violation of the EULA."* If a shape was built by dialing in existing base-figure
or other-vendor morphs, those source morphs must not be baked/embedded as raw deltas into the
export — use **Reverse Deformation** so the exported asset references the source morphs instead of
embedding their deltas. A packaging-review pass should flag any morph export that skips Reverse
Deformation when the shape derives from non-owned source morphs.

## Mesh density for Transfer Utility targets ("Less Can Be More")

The Transfer Utility projects morphs/weights from a source mesh to a target mesh by **vertex
proximity**. A target mesh **denser than the source** produces "blocky and overly rough"
deformation — one source vertex's delta smears across many nearby target vertices instead of each
getting independently meaningful data. Counterintuitive fix: **reduce target mesh density** (or
selectively decimate specific problem regions) rather than adding resolution — this is documented
to produce *better* weight maps and more realistic fabric tension at posed extremes than a
higher-poly target does.

## Troubleshooting recipes (asset-fixing before submission)

None of these four workflows are achievable purely through DazScript/MCP tool calls as currently
documented — each requires either an external modeling-tool round trip or a raw filesystem
text-edit of a `.dsf` file. Tell the user this rather than trying to force it through `daz_execute`.

### JCM needed on clothing (Transfer Utility's auto-morph isn't enough at extreme poses)
Symptom: clothing deforms wrong only at extreme joint rotation (e.g. a coat collar breaking when
the neck bends back). 5 steps:
1. Pose the figure **with the clothing fitted**, pushed to the problem extreme.
2. **File → Export… → obj**, while still posed (pose must be baked into the exported mesh).
3. Fix the broken area in an external modeler; delete the figure from that scene, keep only the
   corrected clothing mesh.
4. **Gotcha:** the Genesis figure back in Daz Studio must still be posed exactly as it was at
   export time before you load the correction back in — pose state must match on both sides.
5. **Morph Loader Pro…**, with **Reverse Deformations = True** — easy to miss, and without it the
   morph double-applies/misapplies the existing pose-driven deformation.

### UV replace/update (no clean in-app path — documented as a text-editing workaround)
1. Load the new UV set onto the model in Studio; rename it to a simple unique temp name (e.g. `"new"`).
2. **File → Save As → Support Asset → DSF UV Set File** → writes `new.dsf`.
3. Open `new.dsf` in a text editor, find/replace every occurrence of `"new"` → `"default"`.
4. Save that edited content **over** the original `default.dsf`; delete the now-redundant `new.dsf`.

Requires raw filesystem/text-edit access to a DSON asset file — this is not a DazScript or
UI-only operation, and needs write access to the content library.

### Auto-generated morph breaks under a parent character morph
**Hard rule, applies to the whole fix:** always work with **Scale = 100%** on every character
shape involved — anything else and the resulting morph develops scaling issues.
1. Scale the child (character) morph to 100%.
2. Fix via **(A)** external modeler: export the child morph and the clothing item (both at 100%
   scale; if subdivided, set **Resolution: Base, SubD: 0** before export — never export a
   subdivided mesh for morph work), fix the shape, export back out **reusing the exact original
   auto-generated morph's name** (this is what targets the overwrite); or **(B)** in-Studio: apply
   a Smoothing value that resolves it (same SubD caution), export using the original name.
3. Reimport via **Morph Loader Pro**, option **"Overwrite Existing: Deltas Only"** — patches just
   the delta data without breaking the existing property linkage (different from a fresh load).
4. Test — sometimes the fix doesn't visibly apply until you re-dial the child morph slider to force
   Daz Studio to recompute the morph stack. Check for mesh interpenetration if SubD is involved.
5. Save the corrected morph target, ideally as its own DSF asset.

### Smoothing modifier explodes/vanishes clothing mesh
Escalating 3-step fix — try each only if the previous one fails:
1. **Lower the Smoothing Iterations value first** (cheap fix — iteration count needed scales with
   mesh resolution; too few polys for the set iteration count is what blows the mesh up).
2. If unresolved: enable **Hidden Properties** (Parameters pane → option menu — this parameter
   isn't shown by default), find **Smoothing Type**, change it from **"Base Shape Matching"** to
   **"Generic."**
3. If Generic overcorrects on a low-poly mesh: add resolution in the affected areas only, as a
   last resort.

**Mandatory cleanup:** turn Hidden Properties back **off** when done — don't ship with it exposed.

### Cross-cutting gotchas
- **Morph Loader Pro has two different critical options for two different scenarios** — don't
  confuse them: `Reverse Deformations = True` (pose-driven JCM fixes) vs. `Overwrite Existing:
  Deltas Only` (patching an existing auto-morph in place).
- **Scale = 100% and Resolution: Base / SubD: 0** whenever exporting geometry for *any*
  morph-target work — otherwise topology/delta magnitudes won't match on reimport.
- "Hidden Properties" in the Parameters pane is a general escape hatch for normally-hidden
  controls (used here for Smoothing Type) — always revert visibility after use, in any workflow.

## Ground truth from real store packages

The metadata schema described above (Content DB Editor fields, Compatibility Base, categorization)
was reverse-engineered from the docs alone when first written. It's since been confirmed — and
given exact XML schemas, real dimension numbers, and the actual DIM zip layout — by decompiling six
real shipped products spanning five different package shapes: a Shader Preset
(`IM00088988-01_SlimeShaders.zip`), a dForce wardrobe item
(`IM00091633-01_dForceReadyToWearOutfitforGenesis9.zip`), a full HD character
(`IM00091643-01_DAVYasakiforGenesis9.zip`), an Environment/Set with its legacy Poser-format sibling
(`IM00002789-01_Level19DS.zip` / `-02_Level19Ps.zip`, same product, two content-format variants),
and a standalone Application install (`IM00004222-01_Hexagon25Win.zip`, not a content package at
all — a full software installer, useful mainly to know what *doesn't* apply here). **See
`SKILL_DSON_FORMAT.md`** for: the `Manifest.dsx` /
`Supplement.dsx` / `<Name>.dsx` (`ContentDBInstall`) schemas verbatim, confirmed real icon/thumbnail
dimensions (product icon 114×148, preset grid icon 91×91, tooltip preview 250×250), the `Category`
namespace convention (literal virtual paths, not free text) with real examples across
Shader/Wardrobe/Character content, **both `data/` payload patterns** for figure/prop products (new
geometry vs. a morph filed into the base figure's own data tree), the real `modifier_library`
morph-delta and **ERC/JCM formula wire format** (a stack-machine expression tied to bone rotation,
confirmed from a real corrective morph), and a package-validation checklist an agent can run
against a candidate zip before submission. It also documents the raw `.duf`/DSON JSON structure
(gzip+JSON) for anyone editing or generating asset files directly rather than through the Daz
Studio UI.

**Real `ContentType`/`Category` taxonomy observed** (beyond the wiki's abstract examples): `Actor/
Character` (full character presets), `Follower/Wardrobe/{Footwear,Full-Body,Outerwear/Top,
Headwear}`, `Follower/Attachment/Head/Forehead/Eyebrows`, `Preset/Materials/MDL` vs. `Preset/
Materials/Hierarchical/MDL` (the latter can target multiple `CompatibilityBase` sub-props in one
preset — e.g. a jacket + its zipper slider + zipper puller), and a formally-recognized `Preset/
Morph/{Apply,Remove}/{Body,Head}` family with matching `/Default/Shaping/{Apply,Remove}/*`
categories — **this is Daz's own convention for shipping HD character detail as separately
add/removable modules**, worth following explicitly for any character product with sculpted HD
detail rather than shipping an all-or-nothing shape. Full detail in `SKILL_DSON_FORMAT.md`.

## Open questions for future SDK/IDA investigation

- ~~No DazScript-level API confirmed for Content DB Editor field writes~~ — **fully resolved
  2026-08-11**: `DzAssetMgr.setFileMetadata(filepath, contentType, compatibleWith, category[,
  assetNode[, compatibilityBase]])` (static) directly assigns Content Type + Compatibility Base +
  Category to a file in one call — the whole manual Content DB Editor workflow is scriptable, not
  just the `.dsx`-file-ingestion path (`queueDBMetaFile`/`processDBMetaFileQueue`, still separately
  confirmed and useful for importing hand-authored `.dsx` files). Full API in
  `SKILL_SDK_REFERENCE.md`. **This changes the packaging skill's guidance** — see
  `daz-product-packaging`'s note about this being scriptable now, not purely manual.
- Scene ID / Compatibility Base **assignment on a node in the live scene** (the Scene ID Editor's
  "Compatibility Base" button) is covered by the same `DzAssetMgr` API — `createCompatibilityBase`/
  `setFileMetadata`'s `compatibilityBase` param. Morph Asset export (the Save-dialog-driven
  packaging workflow) still has no confirmed DazScript API — remains manual UI as far as verified.
- ~~Exact `.dsx` support-file schema~~ — **resolved**, full schema now in `SKILL_DSON_FORMAT.md`.
- ~~The `data/<Author>/<Product>/<Item>/` DSON payload schema for figure/prop/pose products~~ —
  **resolved 2026-08-11**, two distinct patterns confirmed, full detail in `SKILL_DSON_FORMAT.md`.
- ~~Whether `DzERCFreeze`/`DzERCLink` produce the `formulas`/`operations` JSON shape~~ — **resolved,
  with a correction**: `DzERCLink` is a fixed 6-shape wrapper (what `DzERCFreeze` actually builds);
  the real general-purpose stack machine matching arbitrary on-disk `operations` arrays is
  `DzFormula`/`DzFormulaController`, a separate class family. Full detail in
  `SKILL_SDK_REFERENCE.md`. Still not confirmed by freezing one live and diffing the file.
- ~~Legacy Poser-era product packaging hasn't been analyzed~~ — **resolved**, a real Poser-format
  product was directly compared against its DSON conversion; full detail in `SKILL_DSON_FORMAT.md`.
