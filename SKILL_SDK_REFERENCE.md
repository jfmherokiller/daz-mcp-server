# Skill: SDK Reference — Confirmed DazScript Class API

Ground truth pulled directly from the official Daz Studio 6.25+ BETA SDK's Doxygen documentation
(`docs/DAZScript/class_*.html` — this SDK snapshot ships **two parallel doc trees**: the raw C++
plugin-SDK docs at `docs/*.html`, and a `docs/DAZScript/*.html` tree specifically describing what's
exposed to DazScript, which is what this server actually drives). Read 2026-08-11 to resolve open
questions accumulated across `SKILL_STUDIO_CONCEPTS.md`, `SKILL_PACKAGING.md`, `SKILL_DSON_FORMAT.md`,
and `SKILL_DAZSCRIPT.md`. SDK location:
`E:\DazStuff\Applications\Data\DAZ 3D\My DAZ 3D Library\Daz Studio 6.25+ BETA SDK Latest\docs\DAZScript\`
(the base 4.5+ SDK and the non-"Latest" 6.25+ SDK have smaller/identical class sets respectively —
use the "Latest" 6.25+ tree, it's the most complete: 531 documented classes vs. 399 in the 4.5+ SDK).

**How to keep mining this**: `docs/DAZScript/classes.html` is the full alphabetical class index;
each class has a `class_dz_<name>.html` page (Doxygen-mangled: `ERC`→`e_r_c`, camelCase→snake_case
with underscores at case boundaries). Grep the page for `<td class="memname">` for a quick method
list, then pull specific `<div class="memdoc">` blocks for full signatures/descriptions — these
pages are large (the biggest, `dz_asset_mgr`, is ~10,500 lines), don't `Read` them whole.

---

## DzAssetMgr — Content DB / CMS metadata (`App.getAssetMgr()`)

**Headline finding: the entire manual Content DB Editor workflow (Compatibility Base, Category,
Content Type assignment) is scriptable end-to-end**, via one static method:

```javascript
// filepath, contentType, compatibleWith (the base this asset works WITH), category,
// [assetNode] (pull compat base from a node instead), [compatibilityBase] (the base this asset IS)
DzAssetMgr.setFileMetadata(filepath, contentType, compatibleWith, category);
DzAssetMgr.setFileMetadata(filepath, contentType, compatibleWith, category, assetNode);
DzAssetMgr.setFileMetadata(filepath, contentType, compatibleWith, category, assetNode, compatibilityBase);
```
Since 4.9.0.17. This is a one-call equivalent of dragging a file onto the Content DB Editor's
assignment fields — no `.dsx` authoring or `queueDBMetaFile`/`processDBMetaFileQueue` round-trip
needed, confirming `SKILL_PACKAGING.md`'s manual-workflow-only framing was **incomplete** (the manual
UI path is real and still valid, but a fully scripted packaging-metadata tool is also possible).

**Taxonomy creation** (create-if-missing patterns, useful for building the metadata structure
before calling `setFileMetadata`):
```javascript
var assetMgr = App.getAssetMgr();
var baseId = assetMgr.createCompatibilityBase("MyProduct/MyItem");     // → RowIDType
var typeId = assetMgr.createType("Follower/Wardrobe/Shirt", /*defaultOpen*/ false);
var catId  = assetMgr.findCategoryID("/Default/Wardrobe/Shirts", /*isVendor*/ true, /*create*/ true);
// findCompatibilityBaseID(base) / findCompatibilityBaseID(base, create) also create-on-lookup
```

**The `.dsa`-driven import pipeline** (what a `Runtime/Support/*.dsa` RunOnce script actually
triggers — matches `SKILL_DSON_FORMAT.md`'s confirmed `queueDBMetaFile()` finding, now with the
full surrounding pipeline):
```javascript
assetMgr.queueDBMetaFile(productRelativePath);      // adds a .dsx to the queue
assetMgr.getDBMetaFileQueue();                       // inspect the queue
assetMgr.clearDBMetaFileQueue();                     // clear it
assetMgr.processDBMetaFileQueue();                   // UI-MODAL: shows the metadata import dialog
assetMgr.processDBMetaFile(path[, runSilent[, markAsVendor[, groupAsNew]]]);   // headless-capable variant
assetMgr.processDBMetaFileNoEmit(path, ...);          // same, skips category-container UI refresh (batch-friendly)
assetMgr.importMetadataFiles([absolutePaths], runSilent, markAsVendor);        // batch import by absolute path
assetMgr.reimportDBMetaFiles();                       // requeues+imports every *.dsx under every mapped Runtime/Support
assetMgr.checkForNewMetadataScripts();                // scans RunOnce dirs (note: lowercase-f variant is a deprecated alias)
```
`processDBMetaFile`/`processDBMetaFileNoEmit`/`importMetadataFiles` all default to `runSilent=false`
(progress dialog shown) and treat data as user-owned unless `markAsVendor=true` — pass explicit
`true`/`true` for a fully headless, vendor-tagged import.

**Product/store/artist metadata**: `createProduct(name[, storeID])`, `createProductFromAssets(...)`,
`findProductByGuid(guid)`, `findProductByStoreToken(storeID, token)`, `createStore(storeID, token,
url)` (fails on reserved `"DAZ 3D"`/`"LOCAL USER"` IDs), `getStoreToken`/`getStoreUrl`. **No direct
"Artists" setter was found** on `DzAssetMgr` — the only documented read path is indirect, through
`showMoreProductInfo(product)`'s per-store-script JSON payload (`product_artists` array) — likely a
setter exists on `DzProductAssetContainer`/`DzAsset` instead (separate SDK pages, not yet checked).

**CMS lifecycle/control**: `canStartAndStopCMS()`, `isConnectedToCMS()`, `startCMS()`,
`stopCMS(mode, wait[, timeout])` (mode: `StopModeSmart`/`StopModeFast`/`StopModeImmediate`),
`getCMSOptions()`/`setCMSOptions(clusterDir, port)`, `resetDatabase()` (**destructive** — deletes
and rebuilds the DB), `vacuumDatabase()`.

**Content-type classification helpers**: `isClothingType(type)`, `isFigureType(type)`,
`isFollowingType(type)`, `isHairType(type)`, `isPropType(type)`, `isPresetType(type)`,
`isReplaceableType(type)`, etc. — all `(String) → bool`, cross-reference `DzContentReplaceMgr`
(below) for how "replaceable" content types tie into the load-replace mechanism.

**Search**: `searchForAssets(expression, categories[], compatibilityBases[], contentTypes[],
sorting)` and siblings (`searchForProducts`, `searchForAssetsByKeywords`,
`searchForAssetsInCategory`, `searchForAssetAddOns`) — DB-level searches supporting an "Advanced
Filtering" syntax (`cat:`, `compat:`, `type:` scope prefixes). `searchFiles(expression, options)` is
the filesystem-level (non-DB) sibling.

---

## Simulation / dForce (`App.getSimulationMgr()`)

Resolves the "Start Bones from Memorized Pose" location a prior session's community-script analysis
had to defensively probe for, confirms `DzSimulationMgr`/`DzDForceEngine` usage already baked into
this server's tools, and reveals **`DzDForceModifier` is a real, fully documented class** — an
earlier SDK-class-list grep missed it (it only searched the base 4.5+ SDK's non-DazScript doc tree;
it's present and thoroughly documented in the 6.25+ SDK's `docs/DAZScript/` tree).

### Class hierarchy
```
DzSimulationMgr          — App.getSimulationMgr(), singleton
  └─ manages N DzSimulationEngine (only concrete subclass shipped: DzDForceEngine)
DzDForceEngine            — the dForce engine itself; mostly STATIC methods
DzDForceEngineSettings    — GLOBAL simulation settings (subclass of DzElement)
DzDForceModifier          — OBJECT-level dForce modifier attached to a node (subclass of DzModifier)
DzDForceSettingsProvider  — SURFACE/material-level dForce settings, one per material
```

### Finding things (use these, not fuzzy class-name string matching)

**`[corrected 2026-08-11 by live testing]`** The SDK docs mark `findDForceModifierOnNode`/
`addModifier`/etc. as `static` on `DzDForceEngine`, implying `DzDForceEngine.findDForceModifierOnNode(node)`
would work directly on the class. **It does not** — calling any of these on the bare
`DzDForceEngine` class object throws `TypeError: ... is not a function`; live enumeration shows the
class object only exposes `scriptConnect`/`scriptDisconnect`/`inherits`/`className`/`deleteLater`.
**These methods only exist on an actual engine instance**, confirmed by enumerating a real
instance's members (`findDForceModifierOnNode`, `addModifier`, `getPropertyHolder`, `simulate`,
etc. all present there):
```javascript
var engine = App.getSimulationMgr().findSimulationEngine("DzDForceEngine");   // or getActiveSimulationEngine()
var mod = engine.findDForceModifierOnNode(node);              // instance method — NOT DzDForceEngine.findDForceModifierOnNode(node)
var mod2 = engine.findDForceModifierOnObject(node.getObject());
```
**This server's `_SET_DFORCE_PROPERTY_SCRIPT` (`_registry.py`) currently locates the dForce
modifier via `className().toLowerCase().indexOf("dforce") !== -1` fuzzy matching.**
`engine.findDForceModifierOnNode(node)` (via an engine instance, per the correction above) is the
documented, exact, one-call replacement — flagged here as a real, low-risk improvement candidate,
not yet applied to the server's own code. **`engine.addModifier(node, DzDForceModifier.DynamicSurface)`
was live-tested on a bare non-mesh node (a camera) and correctly failed** (non-zero `DzError`
return, no modifier attached afterward) — consistent with dForce modifiers requiring real facet-mesh
geometry to attach to; not yet tested on an actual mesh/clothing node to confirm the success path.

### Global settings — "Start Bones from Memorized Pose" resolved
```javascript
var settings = App.getSimulationMgr().getActiveSimulationEngine().getPropertyHolder();
// getPropertyHolder()'s declared return type is DzElement*, but the live object is a
// DzDForceEngineSettings — DazScript's duck typing lets you call its methods directly, no cast needed.
settings.setStartFromMemorizedPose(true);           // THE confirmed answer
settings.getStartFromMemorizedControl();             // → DzBoolProperty, for keyframing

// Or read/write the WHOLE global settings bundle as one JSON object:
var all = engine.getGlobalSimulationSettings();       // → QVariantMap
engine.simulate(nodes, nodeSettings, simulationSettingsObject);   // custom sim run with overrides
```
Other `DzDForceEngineSettings` fields (same getter/`*Control`/setter pattern throughout): Air
Resistance, Collision Iterations, Collision Mesh Resolution (enum `BaseResolution`/
`ViewportResolution`), Frames Per Second Multiplier, Frames To Simulate (enum `FsCurrentFrame`/
`FsAnimatedPlayRange`/`FsAnimatedCustom`), Gravity, Initialization Time, Iterations, Pose
Transition Time, Send Subframe Updates, Simulation Range, Stabilization Time, Subframes, Velocity
Limit, Visualize Cell Frames.

### Object-level: `DzDForceModifier` (the Freeze toggle lives here)
```javascript
mod.getFreezeSimulation();          // bool — true means EXCLUDED from simulation (frozen/inert)
mod.setFreezeSimulation(true);      //   "the object does not participate... as a simulated mesh"
mod.getFreezeSimulationControl();   // → DzBoolProperty
mod.clearSimulationData();
mod.getSimulationObjectType() / setSimulationObjectType(type);  // enum: StaticSurface/DynamicSurface/
                                                                  // DynamicSurfaceAddOn/Volume/VolumeAddOn
mod.getSimulationBaseShapeMode() / setSimulationBaseShapeMode(mode);  // StartFrame/ZeroFrame/
                                                                        // ShapeAtStartFrame/ShapeAtZeroFrame
// Per-vertex weight-map painting (one getter/setter/invalidate triad EACH for):
// Bend Stiffness, Buckling Ratio, Buckling Stiffness, Influence, Mass Density, Shear Stiffness,
// Stretch Stiffness, Surface Smoothing, Velocity Smoothing:
mod.getBendStiffnessWeights();              // → DzWeightMap
mod.setBendStiffnessWeights(weightMap);     // → DzError
mod.invalidateBendStiffnessWeights();
```
Attach/detach a dForce modifier at the object level via `DzDForceEngine.addModifier(node, objType)`
/ `removeModifier(node)` (static) — `addModifier` auto-calls `addSettingsProviders()` on success.

### Surface-level: `DzDForceSettingsProvider` (one per material — distinct from the object-level modifier)
```javascript
DzDForceEngine.addSettingsProviders(node, /*isSimItem*/ false);   // static, attaches one provider per material
```
Fields (getter/`*Control` where noted/setter): Bend Damping, Bend Stiffness, Buckling Ratio,
Buckling Stiffness, **Collide** (bool — surface participates in collision), Collision Layer,
Collision Offset, Collision Response Damping, Compression Resistance, Contraction/Expansion Ratio,
Damping, Density (gsm), **Dynamics Strength** (amount of simulation result applied to this surface —
distinct from the object-level Freeze flag), Friction, **Self Collide** (bool), Shear
Damping/Stiffness, Stretch Damping/Stiffness, Surface Smoothing (+Iterations), Velocity Smoothing
(+Iterations), **Visible In Simulation** (bool — confirms the earlier community-script finding that
this lives on a different element than the object-level Freeze flag; more precisely, it's per-
*surface* here, not per-*node* as the community script's node-level `findPropertyByLabel` approach
assumed — worth reconciling if `daz_set_dforce_property` needs surface-level granularity).

**If `daz_set_dforce_property` currently only reaches object-level (`DzDForceModifier`)
properties, per-surface properties (collision layer, self-collide, density, stiffness/damping) are
architecturally unreachable through it** — they live on a different element type
(`DzDForceSettingsProvider`, one per material on the node's shape), found via the node's
shape/materials, not the modifier stack.

---

## ERC / Joint Corrective Morphs — `DzERCLink` vs. `DzFormula`/`DzFormulaController`

**Corrects an assumption from earlier in this project's own analysis**: `SKILL_DSON_FORMAT.md`
documented a real shipped JCM's on-disk `formulas`/`operations` stack-machine JSON and speculated
`DzERCLink`/`DzERCFreeze` produce it. **That's only half right** — there are two distinct classes:

- **`DzERCLink`** — a **fixed-shape** wrapper, only 6 possible formulas (enum `ERCType`):
  `ERCDeltaAdd: f(v)=v+(c*m)+a` (default), `ERCDivideInto`, `ERCDivideBy`, `ERCMultiply`,
  `ERCSubtract`, `ERCAdd`, plus `ERCKeyed: f(v)=v+P(c)` (a keyframed curve via `addKeyValue`). This
  is what `DzERCFreeze` actually builds (confirmed — see below), and it's genuinely what most
  *simple* real-world JCMs compile down to (a scalar multiply + optional keyframe curve).
- **`DzFormula`/`DzFormulaController`** — documented in the SDK as the **real general-purpose RPN
  stack machine** and the literal 1:1 mirror of the on-disk `operations` array. **`[live-tested
  2026-08-11: NOT usable from DazScript]`** — `typeof DzFormula` and `typeof DzFormulaController`
  are both `"object"`, not `"function"`; `new DzFormula()` throws `TypeError: Type error`.
  Enumerating their live members shows they're **enum-only namespace objects** — just the
  `Operation`/`Stage` constants (and the live `Stage` enum names are `StageSum`/`StageProduct`, not
  the SDK docs' `SecSum0`/`SecProduct0`/`SecProduct1` — a real naming drift between the SDK
  snapshot and the tested running version). **No constructor, no `addOp`/`addOpPush`/`evaluate`/
  `addFormula` method is reachable from script at all.** The code below is what the SDK docs
  describe and is **kept here only as a record of what does NOT work** — do not use it:
  ```javascript
  // DOES NOT WORK in live DazScript, despite matching the documented SDK API:
  var f = new DzFormula();              // throws TypeError: Type error
  ```
  **Practical conclusion**: if a real shipped product's on-disk JCM formula needs more than
  `DzERCLink`'s 6 fixed shapes can express, there is currently **no confirmed live DazScript path**
  to author it directly from a script — matching it would require going through the UI/ERC-Freeze
  workflow or hand-editing the `.dsf` JSON's `formulas`/`operations` array directly (per
  `SKILL_DSON_FORMAT.md`), not a `DzFormula`-based script.

### `DzERCFreeze` — confirmed constructible live; API matches prior project notes (no corrections needed)

`new DzERCFreeze()` and `new DzERCLink()` both succeed live (`typeof` is `"function"` for both,
unlike `DzFormula`/`DzFormulaController` above) — these remain the only real, script-usable path
for JCM/ERC authoring, even though `DzERCLink` is only a fixed 6-formula wrapper rather than a
general stack machine.
```javascript
var freeze = new DzERCFreeze();
freeze.setControllerNode(node);           // confirmed exact signature
freeze.setControllerProperty(prop);       // confirmed exact signature
freeze.setKeyed(true);                    // confirmed — true => ERCKeyed links; false => ERCDeltaAdd
freeze.setPropertiesToFreeze([...]);      // confirmed exact signature (or addPropertiesToFreeze(node))
freeze.doFreeze();                        // confirmed exact signature
```
Also confirmed real: `DzERCBake` (the inverse — unlinks/removes a controller's `DzERCLink`s,
`doBake()`/`doBakeKeyed(warn)`). Both require the "Property Hierarchy" plugin active (built-in,
since 4.9.3.95/4.9.3.101 respectively).

### `DzController` (common base of `DzERCLink`, `DzFormulaController`, `DzExpression`, `DzTransformConstraintController`)
`ControllerEffect` enum governs how multiple stacked controllers on one property combine:
`Sequential` (uses upstream value as input), `Substitutive` (ignores it, computes independently),
`Summative` (independent, then all Summative results are summed into the value), `Multiplicative`
(independent, results multiplied into the value). `getOwner()` → the property this controller is
attached to (the *output*, distinct from `DzERCLink.getProperty()`, the *input*/driving property).

---

## Live-verification pass (2026-08-11) — corrections and confirmations against a running Daz Studio 6.25.2026.14722

Everything below this point was tested against a real running instance via direct `POST
http://127.0.0.1:18811/execute` calls (bypassing the MCP tool layer, which wasn't registered in
that session — same DazScriptServer bridge this project's MCP server talks to). This caught two
real corrections that static SDK-doc reading alone could not have found:

1. **The SDK docs' `[static]` annotation does not reliably mean "callable on the bare class name
   from DazScript."** `DzDForceEngine.addModifier(...)`/`findDForceModifierOnNode(...)`/etc. are
   documented `static` in the C++ SDK, but calling them directly on the `DzDForceEngine` class
   object in live DazScript throws `TypeError: ... is not a function` — the class object only
   exposes `scriptConnect`/`scriptDisconnect`/`inherits`/`className`/`deleteLater`. **The real
   methods only exist on an actual engine instance**
   (`App.getSimulationMgr().findSimulationEngine("DzDForceEngine")` or
   `getActiveSimulationEngine()`), confirmed by enumerating the instance's members directly.
   Corrected example:
   ```javascript
   var engine = App.getSimulationMgr().findSimulationEngine("DzDForceEngine");  // NOT DzDForceEngine.findDForceModifierOnNode(...)
   engine.addModifier(node, DzDForceModifier.DynamicSurface);
   var mod = engine.findDForceModifierOnNode(node);
   ```
   **Apply this lesson broadly** — don't trust `[static]` from the SDK docs alone for any class in
   this reference; if a "static" call throws a not-a-function error, get an instance first and
   retry on that instance before concluding the method doesn't exist.

2. **A documented public C++ constructor does not guarantee `new ClassName()` works from
   DazScript.** `DzFormula` and `DzFormulaController` (documented with public default constructors
   in the SDK) come back as `typeof === "object"` in live DazScript, not `"function"` — `new
   DzFormula()` throws `TypeError: Type error`. Enumerating their members live shows they're
   **enum-only namespace objects** (just the `Operation`/`ControllerEffect`/`Stage` constants, e.g.
   `DzFormula.OpMultiply`, `DzFormulaController.StageSum`/`StageProduct` — note: live enum names
   are `StageSum`/`StageProduct`, NOT the SDK docs' `SecSum0`/`SecProduct0`/`SecProduct1`, a real
   naming drift between the SDK snapshot and this running version) — **no constructor, no
   `addOp`/`addOpPush`/`evaluate`/`addFormula` methods are reachable from script at all.**
   **This corrects `SKILL_SDK_REFERENCE.md`'s earlier recommendation** ("target `DzFormula`/
   `DzFormulaController` for arbitrary op chains") — that path is **not usable from DazScript** in
   practice, regardless of what the SDK class docs show. `DzERCLink`/`DzERCFreeze` **are** properly
   constructible (`new DzERCFreeze()` and `new DzERCLink()` both succeed, confirmed live) — they
   remain the only real, live-usable path for JCM/ERC authoring from script, even though they're
   only a fixed 6-formula wrapper rather than a general stack machine. If a real shipped product's
   on-disk `.dsf` formula needs more than what `DzERCLink`'s 6 `ERCType` shapes can express, there
   is currently **no confirmed live DazScript path** to author it directly — it would need to come
   from the UI/ERC Freeze workflow or hand-editing the `.dsf` JSON directly (per `SKILL_DSON_FORMAT.md`).

### Confirmed correct, live, no changes needed

- **Iray render settings location — fully confirmed**, see the detailed section below; this was
  the headline open question and it's now proven end-to-end against a live instance, not just
  inferred from docs.
- **`DzUberIrayMaterial`'s 452 named accessors — fully confirmed live**:
  ```javascript
  var mat = new DzUberIrayMaterial();          // constructs fine — typeof "function", real constructor
  mat.getDiffuseWeight();                       // → 1 (default)
  mat.setDiffuseWeight(0.42);
  mat.getDiffuseWeight();                       // → 0.41999998... (float round-trip confirmed)
  ```
- **Joint-limit clamping — resolved with a concrete mechanism**, see the property-limits section
  below: `setValue()` DOES clamp to `[min, max]` once a property's `isClamped` flag is `true`.

## Iray render settings — resolved (2026-08-11 follow-up pass): `getPropertyHolder()`

Following the `DzRenderOptions` dead end below, a second pass located the real Iray settings
object. **`DzIrayRenderer` (subclass of `DzRenderer`) has `getPropertyHolder() → DzElement*`** —
*"The element that holds the properties for this renderer."* `DzElement` is the generic
property-container base (`findProperty()`, `findPropertyByLabel()`, `getPropertyList()`,
`getPropertyGroups() → DzPropertyGroupTree`, element-tree navigation via `getElementChild`/
`getNumElementChildren`) — exactly the mechanism needed to reach nested groups like "NVIDIA Iray
Render Options" → "NVIDIA Iray Photoreal Options" found in the decompiled scene JSON.

```javascript
var renderMgr = App.getRenderMgr();
var iray = renderMgr.findRenderer("DzIrayRenderer");     // or getActiveRenderer() if already active
var holder = iray.getPropertyHolder();                    // DzElement*
var maxSamples = holder.findProperty("Max Samples");
maxSamples.setValue(500);
var denoiser = holder.findProperty("Post Denoiser Enable");
denoiser.setValue(true);
```

A second, likely-equivalent path also exists: **`DzRenderMgr.getOptionHelper() → DzElement*`**
(since 4.7.1.27), backed by the small `DzRenderOptionsHelper` class — *"an element that uses
properties to edit a render options object"* — which tracks whichever renderer is currently active
rather than requiring you to `findRenderer("DzIrayRenderer")` explicitly:
```javascript
var holder = App.getRenderMgr().getOptionHelper();
```

**`[live-verified 2026-08-11]` — fully confirmed, exact structure, no longer speculative.** Tested
against a running Daz Studio 6.25.2026.14722 by enumerating both holders' actual property lists.
Both paths are real and **complementary, not redundant** — they hold different groups:

- `App.getRenderMgr().findRenderer("DzIrayRenderer").getPropertyHolder()` → **className is
  `DzIrayPropertyHolder`** (see correction below), **26 properties**, an exact 1:1 match to the
  decompiled JSON's top-level "NVIDIA Iray Render Options" group: `Render Mode`, `Min Samples`,
  `Max Samples`, `Max Time (secs)`, `Rendering Quality Enable/SSIM/[value]`, `Rendering Converged
  Ratio`, `Progressive Aux Canvas`, `Post SSIM Available/Enable/Predict Target/Max Memory`, `Pixel
  Filter` + `Pixel Filter Radius`, `Post Denoiser Available/Enable/Start Iteration/Max
  Memory/Denoise Alpha`, `White Mode Enable/Color/Albedo Canvas Color`, `Section Caps
  Enabled/Color`, `Active Canvas`.
- That holder's **child elements, reached via `getElementChild(i)`/`getNumElementChildren()`**
  (confirmed 2 children), are exactly the two sub-groups from the decompiled JSON:
  - `getElementChild(0)` → className `DzIrayPhotorealHelper`, 26 properties — `Min Update Samples`,
    `Update Interval (secs)`, `Default/Custom Alpha LPE`, `Max Path/SSS Path Length`, `Caustic
    Sampler`, `Guided Sampling`, `Instancing Optimization`, `Ray Tracing Low Memory`, `Texture
    Compression` (+Medium/High Threshold), `Firefly Filter Enable`, `Nominal Luminance`, `Noise
    Degrain Filtering/Radius/Blur Difference`, `Bloom Filter Enable/Radius/Threshold/Brightness
    Scale`, `Spectral Rendering Enable` (+Color Space/Intent/Observer).
  - `getElementChild(1)` → className `DzIrayInteractiveHelper`, 23 properties — `Occlusion Mode`,
    `Ambient Intensity/Falloff Min-Max Distance/Falloff/Falloff Distance Space`, `Indirect Light
    Mode`, `Indirect Outlier Rejection`, `Ambient Shadow Mode`, `Shadows`, `IBL Falloff`,
    `Refinement Mode`, `Max Ray/Reflection/Refraction Bounces`, `Ray Importance Threshold`, `First
    Frame Antialiasing`, `Area As Point Lights`, `Environment Max Resolution`, `Path Space
    Filtering (PSF)` (+Geometry/Lighting Filter, Convergence Frame).
- `App.getRenderMgr().getOptionHelper()` → **className `DzRenderOptionsHelper`, 16 properties** —
  confirmed to be a **different group** (matching the decompiled JSON's "General Render" element,
  extended): `Dimension Preset (Global)`, `Pixel Size (Global)`, `Aspect Ratio (Global)`,
  `Constrain Proportions (Global)`, `Render Type`, `Render Target`, `Render Range`, `Image
  Name`/`Path`, `Movie Name`/`Path`, `Series Base`/`Path`, `Auto Headlamp`, `Post Process Script`,
  `Render Style`.

Working, live-tested probe pattern (use this shape for any similar "what properties does this
element hold" question — `getProperty(i).getLabel()`, not `findProperty()`, when you don't already
know the exact label string):
```javascript
var iray = App.getRenderMgr().findRenderer("DzIrayRenderer");
var holder = iray.getPropertyHolder();
for (var p = 0; p < holder.getNumProperties(); p++) { /* holder.getProperty(p).getLabel() */ }
for (var c = 0; c < holder.getNumElementChildren(); c++) {
  var child = holder.getElementChild(c);   // DzIrayPhotorealHelper, DzIrayInteractiveHelper
}
```

**Correction to the earlier SDK-docs-only pass**: that pass ruled out `DzIrayPropertyHolder` as
"entirely unrelated" (canvas/AOV + node-list manager only) based on its own *declared* C++ methods.
**That was wrong** — `DzIrayPropertyHolder` is in fact exactly what `getPropertyHolder()` returns,
and it exposes the Iray render-settings channels too, just not as declared C++ methods. As a
`DzElement` subclass, it carries a **runtime-attached generic property list** in addition to its
declared canvas/node-list methods — that property list is invisible to a pure Doxygen-docs read
(which only shows compile-time-declared members) and only shows up by calling
`getNumProperties()`/`getProperty(i)` on a live instance. **General lesson: for any `DzElement`
subclass, its declared methods and its runtime property list are two separate things — reading the
SDK docs only tells you about the former.** `DzRendererMode` (`renderer.getRendererMode()`) is
still not the Photoreal/Interactive settings switch — confirmed separately, it's a read-only
capability descriptor (biased vs. physically-based, RenderMan-compliant, camera feature flags), no
`setMode()` exists anywhere; the actual Photoreal/Interactive split is just two sibling child
elements as shown above.

No render-triggering method (`DzRenderMgr.doRender()`/`doCustomRender()`/`doIPRRender()`,
`DzRenderer.render()`/`customRender()`) accepts anything but the legacy `DzRenderOptions` object as
an explicit parameter — Iray-specific settings must be configured beforehand by mutating the
property holder in place, then rendering with `opt=null` so "current user render options" (which by
then reflect the property edits) are used implicitly.

## Iray materials — `DzUberIrayMaterial` confirmed with 452 named per-channel accessors

Resolves whether the 110-channel table (`SKILL_DSON_FORMAT.md`, extracted from a decompiled `.duf`)
is reached generically or via dedicated methods: **dedicated named methods, confirmed.**
`DzUberIrayMaterial` (`QObject → DzBase → DzElement → DzMaterial → DzUberIrayMaterial`, "provided by
the NVIDIA Iray Renderer plugin", since 4.8.0.55) has **452 methods** following a fully regular
per-channel pattern that maps 1:1 onto the channel `id` strings already documented:
```javascript
material.getDiffuseWeight();          // raw value
material.getDiffuseWeightControl();    // → DzFloatProperty, for keyframing/animation
material.getDiffuseWeightMap();        // → DzTexture, the mapped/textured version
material.setDiffuseWeight(0.8);
material.setDiffuseWeightMap(texturePath);
// same 5-method family (value/Control/Map getters + value/Map setters) repeats for every channel:
// getGlossyRoughness*, getTopCoatWeight*, getSSSAmount*, getEmissionColor*, etc.
```
Since it still derives from `DzElement` (via `DzMaterial`), generic `findProperty("Diffuse
Weight")` presumably also works as a fallback/uniform-access path — but the named accessors are the
primary, documented, type-safe surface. **This is a plausible improvement path for
`daz_set_material_property`**: if it currently drives everything through generic
`findProperty(channel_name).setValue(...)`, the named setters would be more discoverable/type-safe
for the ~100 Iray Uber channels specifically — not applied here, just flagged as a real option.
`DzIrayPropertyHolder` (see above) is on a completely separate inheritance branch and has no
connection to `DzUberIrayMaterial` — the two "generic Iray channel access" candidates this project
was hunting for turned out to be two different, unrelated classes for two different concerns
(canvas/AOV management vs. material channels), not one unified mechanism.

### `DzFloatColorProperty` inherits `DzColorProperty` — confirms `daz_set_material_property` already handles Iray's ~15 float_color channels correctly

Checked while auditing this server's own `_SET_MATERIAL_PROPERTY_SCRIPT` (`_registry.py`) for a
suspected gap: it branches purely on `prop.inherits("DzColorProperty")` before calling
`setColorValue(new QColor(r,g,b))`, and `SKILL_DSON_FORMAT.md`'s 110-channel table lists ~15 Iray
Uber channels (`Diffuse Overlay Color`, `Glossy Color`, `SSS Color`, `Emission Color`, `Top Coat
Color`, `Metallic Flakes Color`, etc.) as type `float_color` — a *different* declared type from the
legacy `color` channels, raising the question of whether those properties are actually
`DzFloatColorProperty` instances that DON'T inherit `DzColorProperty`, in which case the generic
setter's `inherits("DzColorProperty")` check would silently fail every Iray Uber color channel.

**Checked directly against the SDK's Doxygen inheritance diagram for `DzFloatColorProperty`
(`class_dz_float_color_property.html`, not yet live-verified but a static-structure question, not a
"does this method exist at runtime" question)**: the page's own inheritance section lists methods
"inherited from `DzColorProperty`" and "inherited from `DzIntProperty`" — confirming
`DzFloatColorProperty` genuinely extends `DzColorProperty` (chain: `DzProperty → DzNumericProperty →
DzIntProperty → DzColorProperty → DzFloatColorProperty`). So `prop.inherits("DzColorProperty")` is
`true` for Iray Uber's float_color channels too, and `setColorValue()` (inherited, 0-255 sRGB int)
works on them exactly as documented for legacy color channels in `SKILL_DAZSCRIPT.md`'s "Colors —
linear values need `setFloatColorValue`" section. **No bug found** — `daz_set_material_property`'s
existing generic color branch already covers Iray Uber's float_color channels correctly; it just
can't reach `setFloatColorValue()`'s exact-linear round-trip (not needed for a hex-string-input
tool). Recorded here so this doesn't get re-investigated as a suspected bug in a future session.

## Render settings — `DzRenderOptions` is a dead end for Iray (important negative result)

`App.getRenderMgr().getRenderOptions()` returns `DzRenderOptions` — **confirmed to expose ONLY
legacy scanline/RenderMan/OpenGL-preview settings** (`rayTraceDepth`, `shadingRate`,
`shadowSamples`, `pixelFilter`, `xFilterWidth`/`yFilterWidth`, `useGLSL`, `openGLPasses`,
`motionBlur*`, `renderStyle` [Normal/Cartoon], `renderType` [ScreenShot/HardwareAssisted/Software]).
**No Iray-specific field exists anywhere on this class** — no `Render Mode`, `Max Samples`, `Max
Time`, denoiser, or renderer-selection method. No generic `render_elements[]`/channel-group
accessor either. Confirmed-legitimate on this class (matches `SKILL_DAZSCRIPT.md`'s existing
notes): `imageSize`, `aspect`/`aspectWidth`/`aspectHeight`/`setAspectRatio()`,
`renderImgFilename`/`renderImgToId`, `renderMovFilename`/`renderMovToId`, `startTime`/`endTime`,
`isCurrentFrameRender`. Whole-object ops: `applyChanges()`, `resetOptions()`,
`restoreDefaultSettings()`, `copyFrom(otherOptions)` — no preset save/load method.

**Open question, unresolved by this pass**: where the confirmed-real Iray settings (documented in
`SKILL_DSON_FORMAT.md` from a decompiled scene file — Render Mode, Min/Max Samples, denoiser, ray
bounces, etc.) actually live on the DazScript object graph. `DzRenderOptions` is not it. Next
candidate to check: a `DzRenderer`/`DzIrayRenderer` class reached via
`App.getRenderMgr().getActiveRenderer()` or similar (not yet confirmed to exist under that name —
worth a follow-up SDK pass specifically searching for `dz_renderer`/`dz_iray*` class pages).

---

## Property limits — does `setValue` clamp to min/max? `[live-verified 2026-08-11: yes, when isClamped is true]`

Tested directly: created a fresh camera, took its `YRotate` property, called `setMinMax(-45, 45)`
and `setIsClamped(true)`, then `setValue(999)`. Result: **`getValue()` returned `45`** — the
out-of-range value was clamped to `max`, not stored as-is. So the mechanism is real and works
exactly as the property's own `isClamped` state says it should — the earlier "nuanced, no
guarantee" framing from the docs-only pass undersold it. The actual practical answer:

**`setValue()` clamps to `[min, max]` whenever the property's `isClamped` flag is `true` — which
is the normal state for properties that have meaningful limits (e.g. most bone rotations).** The
real remaining nuance is just: check `isClamped()` first if you're unsure, and be aware some
properties' clamp is display-only per `doesClampChangeValue()` (not re-tested live here — the one
property tested had `doesClampChangeValue` return `false` *before* `setIsClamped(true)` was called,
which is consistent with it being a separate flag from `isClamped` rather than a live indicator of
what just happened; worth a follow-up probe on a property that's clamped-by-default out of the box,
e.g. an actual figure bone, rather than a manually-clamped camera property).

Original docs-only analysis, still accurate as supporting detail:

- `DzNumericProperty.isClamped()` — *"true if this property's value is clamped **(for display
  purposes)**"* — the parenthetical is the only characterization given anywhere in the docs.
- `DzNumericProperty.doesClampChangeValue()` (since 4.9.0.24) — *"true if the clamp on this
  property changes its value"* — confirms clamping is **not uniform**: some properties' clamp is
  purely cosmetic (UI shows out-of-range, stored value untouched), others' clamp actually mutates
  the value. No script-facing `setDoesClampChangeValue()` exists — this appears fixed per property
  at creation time, not something a script can toggle.
- `DzFloatProperty.setValue(...)` (all 4 overloads) and `DzNumericProperty.setDoubleValue(...)`:
  **none of their Doxygen descriptions mention min/max/clamping at all.**
- `getMin()`/`getMax()`/`setMin()`/`setMax()`/`setMinMax()` live on `DzFloatProperty`, one level
  below `DzNumericProperty` — pure metadata accessors, described with no enforcement language
  ("allowable value").

**Practical conclusion**: there's no documented guarantee `setValue()`/`setDoubleValue()` clamps to
`[getMin(), getMax()]`. This is consistent with the observed UI behavior (Pose Tool ring
two-toning as a *visual* state; "turn limits off" prompt implying out-of-range values can genuinely
be stored). **If precise behavior matters for a specific property, probe `doesClampChangeValue()`
and compare `getValue()` before/after setting something out-of-range** — don't assume either way.

---

## Morph deltas — `DzMorphDeltas` (confirms the decompiled `.dsf` structure exactly, 1:1)

Confirms `SKILL_DSON_FORMAT.md`'s reverse-engineered `{vertex_count, deltas: {values: [[vertex_idx,
dx,dy,dz], ...]}, hd_url}` structure exactly — and the live API is a **direct read/write mirror**,
not just a passive data holder:
```javascript
var deltas = morph.getDeltas();               // DzMorph.getDeltas() / setDeltas(deltas)
deltas.getNumDeltas();                          // sparse count (NOT full mesh vertex count)
deltas.getDeltaIndex(i);                        // delta index -> mesh VERTEX index
deltas.getDeltaVec(i);                          // delta index -> DzVec3(dx,dy,dz)
deltas.getVertexDeltaIndex(vertIdx);            // reverse lookup, -1 if that vertex has no delta
deltas.addDelta(vertIdx, DzVec3(dx,dy,dz)[, checkDuplicates]);   // returns new delta index, or -1
deltas.setDelta(deltaIndex, DzVec3(dx,dy,dz));  // → DzError, overwrite an existing delta
deltas.removeDelta(deltaIndex) / removeVertex(vertIdx) / removeAllDeltas();
deltas.getHDUrl();                              // the .dhdm URL, confirmed — matches morph.hd_url
deltas.getTargetVertexCount() / setTargetVertexCount(n);   // matches .dsf's vertex_count field
deltas.hasDeltas() / deltas.loadDeltas();       // confirms LAZY LOADING — deltas aren't necessarily
                                                  // resident until loadDeltas() or first access
// Programmatically generate a morph from two mesh states (source vs. sculpted target):
var newDeltas = DzMorphDeltas.calculateDeltas(sourceGeom, targetGeom, /*tolerance*/ 0.001);  // static
```
`DzMorph.getValueControl()` (since 4.9.3.137, deprecates `getValueChannel()`) returns the
`DzFloatProperty` weight/dial that controls the morph's strength — this is the "enable" lever (0 =
inert), and inherits all the `DzFloatProperty` min/max/clamp machinery above.
`DzMorphDeltas.calculateDeltas()` is a genuinely useful find: **a documented, scriptable way to
generate a morph purely from two mesh states**, without the manual "Morph Loader Pro" round trip
`SKILL_PACKAGING.md`'s troubleshooting recipes currently describe as the only path.

---

## Content loading & the Camera/Light preset Replace-mode question — resolved

`SKILL_STUDIO_CONCEPTS.md`/`SKILL_DSON_FORMAT.md` flagged whether a scriptable equivalent exists
for the UI's Ctrl-drag "Replace All / Replace Selected / Add" choice when loading a Camera(s) or
Light(s) Preset. **Resolved: `DzContentReplaceMgr` (`App.getContentMgr().getContentReplaceMgr()`)
is exactly that mechanism**, but it's a stateful side-manager you drive yourself, not a parameter
on the load call:

```javascript
var mgr = App.getContentMgr().getContentReplaceMgr();
mgr.setReplaceMode(ContentReplaceMode.AlwaysReplace);   // "Replace All" — also the plain load default
mgr.setReplaceMode(ContentReplaceMode.NeverReplace);    // "Add" — never remove existing content
// "Replace Selected" has no single-call headless equivalent — build the subset yourself:
var potential = mgr.getPotentialReplaceNodeList(baseNode);   // everything that COULD be replaced
// ... filter potential down to your desired subset ...
mgr.setReplaceNodes(yourSubset);
mgr.doReplace();          // executes the removal, THEN load your new content
```
`ContentReplaceMode.AskWhenMatching`/`AskToReplace` can open a **blocking UI dialog** — avoid both
in headless/automated scripts. Separately, `App.getContentMgr()`'s own load methods
(`openFile`/`openNativeFile`/`mergeFiles`/`loadAsset`) only ever expose a plain boolean `merge`
flag — the 3-way replace choice is entirely `DzContentReplaceMgr`'s responsibility, coordinated by
hand around your own load call, not an extra parameter you can pass into `openFile()`.

`DzDefaultMaterial` was also re-checked here: confirmed **no** conversion/upgrade method exists on
it or its `DzMaterial` base (only `getShaderLanguages()`, a generic reflection query) — validates
that `daz_convert_to_iray_uber`'s `openFile()`-based shader-preset-application approach
(SKILL_DAZSCRIPT.md) is the only real path, not an oversight.

---

## Open questions still unresolved after this pass

1. ~~Where Iray's actual settings live on the DazScript object graph~~ — **fully resolved and
   live-verified 2026-08-11**: `DzIrayRenderer.getPropertyHolder()` (26 props, className
   `DzIrayPropertyHolder`, with 2 child elements `DzIrayPhotorealHelper`/`DzIrayInteractiveHelper`
   matching the decompiled JSON exactly) and `DzRenderMgr.getOptionHelper()` (16 props, a different,
   complementary group). Confirmed by direct property enumeration against a running instance, not
   just inferred from docs. See the "Iray render settings" section above.
2. Whether a direct "Artists" metadata setter exists (found only an indirect read path via
   `DzAssetMgr.showMoreProductInfo()`) — check `DzProductAssetContainer`/`DzAsset` SDK pages.
   `ProductToken`/`GlobalID` writing likewise unconfirmed on `DzAssetMgr` itself. **Not tested
   live this pass** — `DzAssetMgr`'s write methods (`setFileMetadata`, `createCompatibilityBase`,
   etc.) mutate the real Content Database and were deliberately not exercised without explicit
   permission; this remains a docs-only finding.
3. ~~Whether `DzERCFreeze`/`DzERCLink` produce the exact on-disk JSON~~ — **partially addressed**:
   confirmed live that `DzERCLink`/`DzERCFreeze` are the *only* usable script-side path (see the
   `DzFormula`/`DzFormulaController` correction above) — but whether `doFreeze()`'s actual output
   matches a real shipped product's `.dsf` `formulas` shape byte-for-byte is still untested (would
   require freezing a real correction on a real figure and inspecting the saved file — deliberately
   not attempted this pass since it mutates scene structure and wasn't asked for).
4. Reconcile the per-surface `DzDForceSettingsProvider.getVisibleInSimulation()` finding here
   against the earlier community-script-derived note (in `SKILL_DAZSCRIPT.md`) that "Visible in
   Simulation" lives directly on the node — **not tested live this pass** (would need a real
   dForce-enabled clothing item loaded; the live dForce test used a bare camera node specifically
   to avoid touching the user's content library, and correctly failed to attach a modifier since
   dForce needs real mesh geometry). Still an open question.
5. Whether `setValue()`'s clamping behavior (confirmed live for a manually-`setIsClamped(true)`
   camera property) holds the same way for a property that's clamped *by default* out of the box —
   e.g. an actual Genesis figure bone rotation — rather than one manually configured for the test.
   Same caveat as #4: would need a real figure loaded, not attempted this pass.
