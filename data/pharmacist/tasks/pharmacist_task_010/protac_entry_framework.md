# PROTAC Entry Framework — Revised (v3)

## Corrected Starting Path

A first-pass PROTAC plan moves through five staged decisions. Each stage narrows the options; skipping a stage or keeping it "open" makes later results uninterpretable. The endpoint is a degradation curve — if you never reach it, the earlier stages were wasted effort.

### Stage 1 — Target: BRD4 (one target, not three)

Pick **one** protein with a known, potent, commercially available binder. For a first pass, that protein is **BRD4**.

**Why BRD4, not AR or ER:**

- JQ1 is commercially available, potent (Kd ~50 nM for BRD4 BD1/BD2), and has known SAR and known exit vectors. Enzalutamide-derived and vepdegestrant-derived binders are not commercially available in PROTAC-ready format and require complex synthesis.
- BRD4 degradation is easily read out by Western blot with published DC50 benchmarks (dBET1: >85% degradation at 100 nM in MV4-11; MZ1: DC50 8–23 nM in H661/H838).
- BRD4 has precedents with both CRBN and VHL, so you can swap E3 later without changing the target.
- AR and ER are valuable targets with clinical precedent (ARV-110, ARV-471), but they are **Tier 2** choices for a beginner: restricted cell line requirements (AR+ or ER+ only), complex warhead synthesis, and no simple commercially available PROTAC-ready binder.

**Do not keep multiple targets open.** A negative result with one target tells you nothing about whether the target, E3, or linker was wrong. Pick BRD4, get a degradation curve, then branch to other targets.

### Stage 2 — E3 Ligase: CRBN (default, not "CRBN or VHL")

The default E3 is **CRBN** (thalidomide/pomalidomide-derived ligands). VHL is a secondary alternative, not an equal choice for a first pass.

**Why CRBN first:**
- CRBN ligands (thalidomide, lenalidomide, pomalidomide) are commercially available, well-characterized, and have known exit vectors (4-position of the phthalimide/glutarimide ring).
- All clinical-stage PROTACs (ARV-110, ARV-471, gridegalutamide, catadegbrutinib) use CRBN. ARV-471 (vepdegestrant) NDA submitted to FDA June 6, 2025; NDA accepted August 8, 2025; PDUFA action date June 5, 2026 — anticipated to be the first FDA-approved PROTAC.
- dBET1 — the canonical beginner PROTAC — uses CRBN.

**Critical practical point — check CRBN expression before interpreting results:**

A 56-cell-line profiling study (Steinebach et al., iScience 2022, DOI: 10.1016/j.isci.2022.104048, PMID: 35641325) showed dBET1 was **frequently inactive** in many solid tumor lines due to low CRBN expression, while MZ1 (VHL-based) was broadly active. Hematological lines (MV4-11, Kasumi, NB4) consistently showed high CRBN.

**Practical rule:** If you choose CRBN, use MV4-11 (AML) — it has high CRBN and is the standard dBET1 benchmarking line. If you must use a solid tumor line, verify CRBN expression by Western blot/qPCR first. Do not interpret "no degradation" as a chemistry failure without checking E3 expression.

**Critical practical point — CRBN neosubstrate off-target degradation:**

Thalidomide and pomalidomide are not inert scaffolds. They are molecular glues that independently recruit and degrade CRBN neosubstrates — most notably IKZF1 (Ikaros), IKZF3 (Aiolos), ZFP91, CK1α, and GSPT1. This means:

- **Any CRBN-based PROTAC using a thalidomide/pomalidomide E3 handle will also degrade IKZF1/IKZF3** in cells that express them. This is not a PROTAC-specific effect — it is the E3 ligand's intrinsic molecular glue activity.
- A beginner running proteomics or multi-target Western blots may see IKZF1/IKZF3 loss and misattribute it to PROTAC-mediated degradation of a novel target. It is not — it is the pomalidomide/thalidomide handle acting as a molecular glue.
- **Practical rule:** When interpreting degradation data from a CRBN-based PROTAC, always include the E3 ligand alone (pomalidomide or thalidomide alone) as a control. Any protein degraded by both the PROTAC and the E3 ligand alone is a neosubstrate, not a PROTAC-specific target.
- Recent work (Bricelj et al., Nat. Commun. 2026, DOI: 10.1038/s41467-026-70663-1) has developed dihydrouracil-based CRBN ligands that mitigate IMiD-associated neosubstrate degradation. These are not yet standard but represent the direction for reducing off-target liabilities.

**When to switch to VHL:** Only after a CRBN-based baseline works (or fails specifically because of low CRBN expression in your cell line). VHL uses VH032-derived ligands, has broader activity across cell lines, but is inactive in VHL-mutant RCC lines. MZ1 (VHL–JQ1–BRD4) is the canonical VHL-based comparator.

**Do not compare CRBN, VHL, and a novel E3 in parallel for a first pass.** Novel E3 ligases (DCAF1, RNF4, KEAP1) introduce unvalidated ligand affinity, unknown tissue expression, and uncharacterized substrate specificity — all of which make a first result uninterpretable.

### Stage 3 — Linker: short flexible amide-ether linker at known exit vectors (reproduce dBET1, not invent)

Use a **short flexible linker** attached at the known JQ1 exit vector (solvent-exposed carboxyl position, via an amide bond) and the thalidomide 4-position (via an ether bond). This reproduces the dBET1 architecture. It is not creative, but it is interpretable.

**Important correction on linker terminology:** dBET1's linker is a short flexible connector with an amide bond on the JQ1 side and an ether bond on the thalidomide side, with ~8 bonds separating the linking atoms from the two warheads. Some mass spectrometry literature describes this motif as a "glycolamide" (referring to the HOCH₂C(O)NH₂ structural element), but the PROTAC design literature more commonly describes it simply as a "short flexible amide-ether linker." The previous draft used "glycolamide" throughout, which is technically correct but may confuse a beginner searching the primary literature. Both terms refer to the same structure.

**Important correction:** dBET1 does NOT use a PEG2–PEG4 linker. The previous v1 draft incorrectly described dBET1 as having a "PEG2–PEG4" linker, which would mislead a beginner trying to reproduce the architecture. dBET1's linker contains no ethylene glycol repeats.

**Why simple short linker first:**
- PROTACs violate Lipinski's Rule of 5 (MW >700 Da, bRo5 space). Cell permeability is a major practical barrier. Short, flexible linkers tend to have better permeability than rigid, bulky alternatives in early-stage molecules. Recent computational work (PROTAC-TS, JACS Au 2026) confirms that permeability-favorable PROTACs adopt folded, low-PSA conformations — shorter linkers facilitate this.
- dBET6 achieved improved degradation potency primarily through improved cell permeability and a modified linker, not through a fundamentally different linker concept (Winter et al., Mol. Cell 2017, DOI: 10.1016/j.molcel.2017.06.004, PMID: 28673542). Note: this paper is about BET proteins as transcription elongation factors; dBET6 is a tool compound in the study, not the paper's subject.
- The linker's role is to enable productive ternary complex formation. It is the most visible design feature in a figure, but it is not the most informative starting point.

**PEG linkers (PEG2–PEG4) are a valid alternative class** — MZ1 uses a PEG3 linker, and many subsequent PROTACs use PEG-based linkers. But for a first pass that reproduces dBET1, the linker should match dBET1's actual amide-ether architecture, not a PEG linker that dBET1 never had.

**Macrocyclic, ferrocene-hinge, rigid aromatic, and computationally optimized linkers are deferred** until a simple-linker baseline shows degradation. Exploring them before having a baseline makes every result uninterpretable.

### Stage 4 — Negative Controls: minimum required vs. ideal

Before running the degradation assay, prepare controls. Some are minimum required; others are ideal if available.

**Minimum required (3 controls):**

| Control | What It Tests | Example |
|---|---|---|
| **Parent warhead alone** | Confirms degradation is PROTAC-dependent, not inhibitor-mediated downregulation | JQ1 alone (should inhibit but not degrade BRD4) |
| **E3 ligand alone** | Confirms E3 ligand does not independently affect target; also identifies neosubstrate off-targets (IKZF1/IKZF3 degradation by pomalidomide alone) | Pomalidomide alone (should not degrade BRD4; will degrade IKZF1/IKZF3) |
| **Proteasome inhibitor (MG132)** | Confirms proteasome dependence | MG132 co-treatment (should rescue BRD4 from degradation) |

**Ideal if available (3 additional controls):**

| Control | What It Tests | Example |
|---|---|---|
| **Inactive stereoisomer** | Confirms ternary complex geometry matters | cisMZ1 (inactive VHL stereoisomer; should not degrade BRD4) |
| **E3 knockout / knockdown** | Confirms E3 dependence | CRBN-KO cells (dBET1 should lose activity) |
| **Excess competing ligand** | Confirms binary engagement is required | Excess JQ1 or excess pomalidomide co-treatment (should block PROTAC by occupying binding sites) |

Without the minimum three controls, a Western blot showing BRD4 loss could be misattributed to degradation when it might be transcriptional downregulation, off-target toxicity, or assay artifact.

### Stage 5 — Validation: DC50/Dmax from a full concentration series (the endpoint)

The first assay must measure **target protein depletion** and report **DC50** and **Dmax**. This is the endpoint of the starting path — if you never reach it, the earlier stages were wasted effort.

**DC50**: Concentration at which 50% of maximal degradation is observed. Fit Dmax values across a concentration series to a variable-slope dose–response model (Riching et al., ACS Chem. Biol. 2018, DOI: 10.1021/acschembio.8b00692, PMID: 30137962).

**Dmax**: Maximum percent degradation at the optimal concentration. A PROTAC with DC50 = 1 nM but Dmax = 50% may be less useful than one with DC50 = 100 nM and Dmax = 95%.

**Always run a full concentration series** (0.1 nM – 10 μM, 8–10 points). PROTAC dose–response curves are often bell-shaped (hook effect): degradation peaks at an optimal concentration, then decreases as binary complexes outcompete the productive ternary complex. A single-concentration measurement may miss the peak entirely.

**Important correction on dBET1 potency:** dBET1's DC50/5h is ~500 nM in HiBiT-HEK293 cells (Riching et al., ACS Chem. Biol. 2018), not ~50 nM as stated in the v1 draft. dBET1 achieves >85% BRD4 degradation at 100 nM in MV4-11 after 18 h treatment, but the half-maximal degradation concentration measured by live-cell kinetics is ~500 nM at 5 h. The "~50 nM" figure in the v1 draft was incorrect — it likely conflated the concentration at which visible degradation occurs (>85% at 100 nM) with the DC50. For a beginner, the practical benchmark is: **dBET1 shows clear BRD4 loss at 100 nM in MV4-11 after 18 h; the DC50/5h is ~500 nM in HiBiT-HEK293**.

**Note on cell-line-dependent DC50:** The DC50/5h ~500 nM figure is from HiBiT-tagged HEK293 cells. MV4-11 cells (the standard benchmarking line) may show different absolute DC50 values due to higher CRBN expression and different BRD4 levels. The key point is that dBET1 is a moderate-potency tool compound, not a sub-nanomolar degrader.

**Assay technology note — Western blot vs. HiBiT:**
- **Western blot** is the default first-pass assay: widely available, no special cell lines needed, directly measures endogenous protein. Limitations: semi-quantitative, low throughput, no kinetic information.
- **HiBiT-CRISPR live-cell assay** (Promega) is the current gold standard for quantitative kinetic degradation profiling: endogenous tagging, real-time luminescence readout, plate-based format, measures rate/Dmax/DC50 simultaneously. Limitation: requires CRISPR-edited cell lines (available commercially for BRD4 and other common targets).
- **For a beginner:** Start with Western blot. Upgrade to HiBiT when you need kinetic data, throughput, or quantitative DC50 fitting.

**Secondary validations** — ubiquitination detection, ternary complex formation (AlphaLISA/NanoBRET), time-course kinetics — come after the primary degradation signal is confirmed. Do not postpone degradation validation until after the chemistry story looks interesting.

---

## PROTAC vs. Molecular Glue — a beginner distinction

PROTACs are heterobifunctional molecules (two ligands + linker) that bring an E3 ligase and a target protein into proximity, triggering ubiquitination and proteasomal degradation. Molecular glues are small, monovalent molecules that stabilize or create a novel interface between an E3 and a target — no linker, no second ligand.

**Why this matters for a beginner:**
- PROTACs are modular and rationally designable: you pick a target binder, an E3 binder, and a linker. This modularity is what makes the staged approach above possible.
- Molecular glues (e.g., lenalidomide → IKZF1/3 via CRBN) are not modular — you cannot swap components independently. Their discovery is largely phenotypic/serendipitous, not rational.
- The clinical landscape includes both: lenalidomide/pomalidomide are molecular glues (IMiDs), while ARV-110/ARV-471 are PROTACs. A beginner starting with PROTAC design should not confuse the two modalities, because the design logic and validation path are fundamentally different.
- **Critically, the CRBN ligands used in PROTACs (thalidomide, pomalidomide) are themselves molecular glues.** This means every CRBN-based PROTAC carries an intrinsic molecular glue activity that will degrade IKZF1/IKZF3 independently of the PROTAC's intended target. This dual identity is a source of confusion and off-target effects that a beginner must understand from the start.

---

## Clinical Landscape (mid-2025 snapshot)

Three PROTAC drugs have reached Phase III trials with the US FDA:

| Drug | Target | E3 | Sponsor | Phase III Trial | Status |
|---|---|---|---|---|---|
| **Vepdegestrant (ARV-471)** | ER | CRBN | Arvinas/Pfizer | VERITAC-2 (NCT05654623) | NDA submitted June 6, 2025; NDA accepted August 8, 2025; PDUFA June 5, 2026. ESR1m subgroup: median PFS 5.0 vs 2.1 mo (HR 0.57, 95% CI 0.42–0.78), statistically significant. ITT population: median PFS 3.7 vs 3.6 mo (HR 0.83, 95% CI 0.68–1.02, P=0.07), did not reach statistical significance. |
| **Gridegalutamide (BMS-986365/CC-94676)** | AR | CRBN | BMS/Celgene | rechARge (NCT05917421) | Phase III ongoing; dual AR degrader + antagonist. |
| **Catadegbrutinib (BGB-16673)** | BTK | CRBN | BeiGene | NCT06973187 | Phase III ongoing (initiated 2025); degrades WT and C481S-mutant BTK; three randomized Phase III trials in R/R CLL including head-to-head vs. pirtobrutinib. |

ARV-110 (bavdegalutamide) remains in Phase I/II for mCRPC (NCT03888612); no Phase III announced yet.

**Notable pattern:** All three Phase III PROTACs use CRBN as the E3 ligase. No VHL-based PROTAC has reached Phase III. This reinforces CRBN as the default E3 choice for a beginner learning the clinically validated path.

---

## Precedent Priority Table

| Priority Tier | Route | Target | E3 | Linker | Readout | Precedent | DC50 | When to Use | Why Not Default |
|---|---|---|---|---|---|---|---|---|---|
| **Tier 1 — Default** | BRD4 + CRBN + short amide-ether linker + Western blot DC50/Dmax + minimum controls | BRD4 | CRBN | Short flexible amide-ether (~8 bonds) | Western blot DC50/Dmax + JQ1/pomalidomide/MG132 controls | dBET1 | >85% degradation at 100 nM in MV4-11 (18 h); DC50/5h ~500 nM in HiBiT-HEK293 | First pass; baseline; learning full workflow | None — this is the starting point |
| **Tier 2a — E3 swap** | BRD4 + VHL + PEG3 + Western blot + cisMZ1 control | BRD4 | VHL | PEG3 | Western blot DC50/Dmax + cisMZ1 control | MZ1 | DC50 8–23 nM (H661/H838); DC50/5h ~30 nM (HiBiT-HEK293) | After Tier 1 CRBN baseline works; teaches E3 choice effects; avoids CRBN neosubstrate off-targets | Requires VHL expression; VHL-mutant RCC lines inactive; needs working Tier 1 comparator |
| **Tier 2b — Linker variation** | BRD4 + CRBN + modified linker (same target/E3) | BRD4 | CRBN | Modified amide-ether | Western blot DC50/Dmax + permeability assessment | dBET6 | DC50/5h ~10 nM for BRD4BD1; ~50 nM for BRD4BD2 | After Tier 1 shows degradation; teaches linker/permeability effects | Requires working Tier 1 comparator; dBET6 paper is mechanistic (BET elongation), not PROTAC design-focused |
| **Tier 2c — Target branch** | AR + CRBN + clinical precedent (different target, same E3) | AR | CRBN | Piperidine-piperazine (short, rigid) | Western blot DC50/Dmax + PSA PD biomarker | ARV-110 / bavdegalutamide | DC50 ~1 nM in LNCaP/VCaP | After Tier 1 BRD4 baseline works; branching to hormone receptor targets | Complex warhead synthesis; restricted to AR+ cell lines; no simple commercially available PROTAC-ready binder |
| **Tier 2d — Mechanism deepening** | Full concentration series + hook-effect modeling + ternary complex assay | BRD4 | CRBN or VHL | Amide-ether or PEG3 | 8-point dose–response + hook-effect curve + MG132 + AlphaLISA/NanoBRET | dBET1/MZ1 dose–response (Riching 2018) | Bell-shaped peak | After initial degradation confirmed; teaches PROTAC-specific pharmacology | Requires plate reader or NanoBRET instrumentation |
| **Tier 3a — Novel E3** | Novel E3 (DCAF1) + validated target binder + standard linker | BTK | DCAF1 | PEG-based | Western blot + proteomics | DBt-10 | DC50 ~149 nM in TMD8 | Only after Tier 1 and Tier 2 mastered; for overcoming CRBN resistance | DCAF1 ligand affinity and tissue expression less validated; DC50 worse than CRBN-based BTK PROTACs |
| **Tier 3b — Covalent E3** | Covalent E3 recruiter (RNF4/CCW16) + target | BRD4 | RNF4 (CCW16) | Covalent | Ubiquitination first, degradation later | CCW28-3 | "Active" in 231MFP (but see Why Not Default) | Only with experienced team and established infrastructure | CCW16-derived PROTACs **failed to degrade RNF4** in all tested cell lines; CCW16 induces RNF4-independent ferroptosis via off-target cysteine reactivity (Schwalm et al., EMBO Rep. 2025, DOI: 10.1038/s44319-025-00593-4, PMID: 41102521); MG132 rescue at toxic concentrations gave inconclusive results |

---

## Deferred Beginner Traps

### 1. Keeping multiple targets, E3 ligases, and linker styles open simultaneously

A negative result tells you nothing about which variable failed. Pick one target, one E3, one linker class, get a degradation curve, then branch.

### 2. Starting with novel linker ideas before a baseline exists

Short, flexible linkers at known exit vectors give a baseline ternary complex geometry. Creative linkers (macrocycles, ferrocene hinges, rigid aromatic spacers) should be explored only after a simple linker shows that the target–E3 pairing is degradable. Without a baseline, every linker result is uninterpretable.

### 3. Postponing degradation validation until the chemistry feels interesting

A PROTAC that cannot be shown to degrade its target by Western blot or live-cell imaging is not yet a PROTAC. Degradation readout (DC50, Dmax, time-to-nadir) is the primary validation, not a later-stage confirmation.

### 4. Changing multiple variables at once when the first result is weak

If a construct fails to degrade, change **one** variable at a time: swap CRBN→VHL (same target, same linker), or modify linker length/composition (same target, same E3), or change cell line (same construct). Changing target + E3 + linker simultaneously produces an uninterpretable result and wastes synthesis effort. This applies whether you call it "optimizing several variables" or "revealing a stronger combination" — both are the same mistake.

### 5. Ignoring the hook effect

PROTAC dose–response curves are often bell-shaped. A single-concentration measurement may miss the peak entirely. Always run a full concentration series (0.1 nM – 10 μM) and fit DC50/Dmax with a hook-effect model.

### 6. Skipping negative controls

Without JQ1 alone, pomalidomide alone, and MG132 co-treatment, a Western blot showing BRD4 loss could be misattributed. These three controls are the minimum required to claim PROTAC-mediated degradation.

### 7. Choosing a cell line without checking E3 expression

CRBN expression varies widely across cell lines. dBET1 was frequently inactive in the 56-cell-line panel (Steinebach et al., iScience 2022) because many solid tumor lines have low CRBN. A "no degradation" result in a low-CRBN line is an E3 availability failure, not a chemistry failure. Check E3 expression before interpreting a negative result.

### 8. Chasing novelty before a comparator exists

Designing a novel E3 recruiter, novel target binder, or novel linker architecture before having a working baseline PROTAC means every result — positive or negative — is uninterpretable because you cannot attribute it to any specific variable.

### 9. Confusing PROTACs with molecular glues

PROTACs are modular (target binder + linker + E3 binder); molecular glues are monovalent interface stabilizers. The design logic and validation path are fundamentally different. A beginner working on PROTAC design should not apply molecular glue reasoning (e.g., "just find a small molecule that brings two proteins together") to a PROTAC project.

### 10. Misremembering dBET1's linker and potency

dBET1 uses a **short flexible amide-ether linker** (amide bond on JQ1 side, ether bond on thalidomide side, ~8 bonds), NOT a PEG2–PEG4 linker. dBET1's DC50/5h is ~500 nM in HiBiT-HEK293 (Riching 2018), NOT ~50 nM. The practical benchmark is: >85% BRD4 degradation at 100 nM in MV4-11 after 18 h. Confusing the linker type or potency makes the default route uninterpretable and prevents meaningful comparison to published data.

### 11. Ignoring CRBN neosubstrate off-target degradation

Thalidomide and pomalidomide are molecular glues that independently degrade IKZF1, IKZF3, ZFP91, CK1α, and GSPT1 via CRBN. Any CRBN-based PROTAC using these E3 handles will carry this off-target activity. A beginner who sees IKZF1/IKZF3 loss in proteomics or Western blot may misattribute it to their PROTAC's intended mechanism. **Always run the E3 ligand alone control and compare.** Any protein degraded by both the PROTAC and the E3 ligand alone is a neosubstrate, not a PROTAC-specific target. This is especially important when claiming selectivity or novel target engagement.

---

## Default First Route

**BRD4 + CRBN + short amide-ether linker (~8 bonds) + MV4-11 cells + Western blot DC50/Dmax + 3 minimum controls.**

### Actionable checklist:

1. **Synthesize or purchase** a dBET1-like PROTAC: JQ1 connected to thalidomide via a short flexible linker (amide bond at the JQ1 carboxyl exit vector, ether bond at the thalidomide 4-position), with ~8 bonds separating the linking atoms from the two warheads. dBET1 is commercially available from multiple vendors (e.g., Tocris, MedChemExpress, Cayman Chemical).
2. **Use MV4-11 cells** (AML; high CRBN expression; standard dBET1 benchmarking line).
3. **Treat** with 8–10 point concentration series (0.1 nM – 10 μM) for 6–24 h.
4. **Run Western blot** for BRD4; quantify band intensity; fit DC50/Dmax.
5. **Run 3 minimum controls**: JQ1 alone, pomalidomide alone, MG132 co-treatment.
6. **Check for hook effect** at high concentrations (>1 μM).
7. **Interpret with awareness** of CRBN neosubstrate off-targets: if you probe for IKZF1/IKZF3, expect them to be degraded by both the PROTAC and pomalidomide alone.

### Expected result:

dBET1 shows >85% BRD4 degradation at 100 nM in MV4-11 after 18 h. The DC50/5h is ~500 nM in HiBiT-HEK293 (Riching 2018). If your construct achieves comparable degradation at similar concentrations → baseline established → branch by changing one variable. If not → failure is interpretable (synthesis failed? linker suboptimal? CRBN low?) → test each by changing one variable at a time.

### What to do next (after baseline works):

- **Swap E3**: VHL-based BRD4 PROTAC (MZ1 architecture, PEG3 linker) → compare DC50/Dmax and cooperativity (α). MZ1 is more potent (DC50 8–23 nM) and avoids CRBN neosubstrate off-targets, but requires VHL expression.
- **Modify linker**: Change linker length/composition (same target, same E3) → measure effect on DC50, Dmax, and hook-effect window.
- **Branch target**: AR (ARV-110 architecture) or ER (ARV-471 architecture) → compare across target classes.
- **Deepen mechanism**: AlphaLISA/NanoBRET ternary complex, ubiquitination detection, time-course kinetics.
- **Upgrade assay**: Move from Western blot to HiBiT-CRISPR live-cell assay for quantitative kinetic profiling.

---

## Key Literature Anchors (traceable citations)

| Ref | Full Citation | DOI | PMID | Key Contribution |
|---|---|---|---|---|
| dBET1 | Winter GE, Buckley DL, Paulk J, et al. "Phthalimide conjugation as a strategy for in vivo target protein degradation." *Science* 2015; 348(6241): 1376–81. | 10.1126/science.aab1433 | 25999370 | Canonical CRBN–JQ1–BRD4 degrader; short amide-ether linker (~8 bonds); >85% BRD4 degradation at 100 nM in MV4-11; EC50 ~430 nM |
| dBET6 | Winter GE, Mayer A, Buckley DL, et al. "BET Bromodomain Proteins Function as Master Transcription Elongation Factors Independent of CDK9 Recruitment." *Mol. Cell* 2017; 67(1): 5–18.e19. | 10.1016/j.molcel.2017.06.004 | 28673542 | Mechanistic study of BET elongation function; dBET6 is a tool compound (not the paper's subject); DC50/5h ~10 nM for BRD4BD1, ~50 nM for BRD4BD2 |
| MZ1 | Zengerle M, Chan KH, Ciulli A. "Selective Small Molecule Induced Degradation of the BET Bromodomain Protein BRD4." *ACS Chem. Biol.* 2015; 10(8): 1770–7. | 10.1021/acschembio.5b00216 | 26035625 | Canonical VHL–JQ1–BRD4 degrader; PEG3 linker; unexpectedly selective for BRD4 over BRD2/BRD3; DC50 8–23 nM |
| ARV-110 | Snyder LB, Neklesa TK, Willard RR, et al. "Preclinical Evaluation of Bavdegalutamide (ARV-110), a Novel PROTAC AR Degrader." *Mol. Cancer Ther.* 2025; 24(4): 511–22. | 10.1158/1535-7163.MCT-23-0655 | 39670468 | First PROTAC in human clinical trials (NCT03888612); CRBN-based AR degrader; DC50 ~1 nM in LNCaP/VCaP; short rigid piperidine-piperazine linker |
| ARV-471 | Gough SM, Flanagan JJ, Teh J, et al. "Oral Estrogen Receptor PROTAC Vepdegestrant (ARV-471) Is Highly Efficacious…" *Clin. Cancer Res.* 2024; 30(16): 3549–63. | 10.1158/1078-0432.CCR-23-3465 | 38819400 | CRBN-based ER degrader; DC50 ~0.9 nM in MCF7; NDA submitted June 6, 2025; NDA accepted August 8, 2025; PDUFA June 5, 2026 |
| ARV-471 NDA | "NDA Submission of Vepdegestrant (ARV-471) to U.S. FDA: The Beginning of a New Era of PROTAC Degraders." *J. Med. Chem.* 2025. | 10.1021/acs.jmedchem.5c01818 | — | NDA acceptance; Phase 3 VERITAC-2 positive in ESR1m subgroup (PFS 5.0 vs 2.1 mo, HR 0.57); ITT not significant (PFS 3.7 vs 3.6 mo, HR 0.83, P=0.07); Fast Track designation |
| Riching 2018 | Riching KM, Mahan S, Corona CR, et al. "Quantitative Live-Cell Kinetic Degradation and Mechanistic Profiling of PROTAC Mode of Action." *ACS Chem. Biol.* 2018; 13(9): 2758–70. | 10.1021/acschembio.8b00692 | 30137962 | DC50/Dmax methodology; HiBiT live-cell degradation kinetics; dBET1 DC50/5h ~500 nM; MZ1 DC50/5h ~30 nM |
| Hook effect | Riching KM, Caine EA, Urh M, Daniels DL. "The importance of cellular degradation kinetics for understanding mechanisms in targeted protein degradation." *Chem. Soc. Rev.* 2022; 51: 6210–21. | 10.1039/D2CS00339B | 35792307 | Bell-shaped curve; degradation rate, extent, and duration as separate kinetic parameters |
| E3 profiling | Steinebach C, Kehm H, Lindner S, et al. "Profiling of diverse tumor types establishes the broad utility of VHL-based PROTACs and triages candidate ubiquitin ligases." *iScience* 2022; 25(4): 104048. | 10.1016/j.isci.2022.104048 | 35641325 | 56-cell-line panel; CRBN expression predicts dBET1 activity; VHL broadly active |
| CRBN neosubstrate | Bricelj A, et al. "A dihydrouracil CRBN ligand mitigates IMiD associated safety liabilities in heterobifunctional targeted protein degrader." *Nat. Commun.* 2026. | 10.1038/s41467-026-70663-1 | — | Dihydrouracil CRBN ligands reduce IKZF1/IKZF3/GSPT1 off-target degradation while retaining PROTAC activity |
| CRBN neosubstrate (original) | Krönke J, Udeshi ND, Narla A, et al. "Lenalidomide causes selective degradation of IKZF1 and IKZF3 in multiple myeloma cells." *Science* 2014; 343(6168): 301–5. | 10.1126/science.1244851 | 24292625 | Discovery that IMiDs degrade IKZF1/IKZF3 via CRBN; foundational molecular glue mechanism |
| Linker review | Troup RI, Fallan C, Baud MGLE. "Current strategies for the design of PROTAC linkers: a critical review." *Explor. Target. Anti-Tumor Ther.* 2020; 1(5): 273–312. | 10.37349/etat.2020.00018 | 36046485 | Comprehensive linker class overview; PEG, alkyl, rigid, macrocyclic |
| E3 ligand review | Konstantinidou M, Zarganes-Tzitzikas T, Magiera-Müller K, et al. "E3 Ligase Ligands for PROTACs: How They Were Found and How to Discover New Ones." *SLAS Discov.* 2021; 26(4): 471–503. | 10.1177/2472555220965528 | 33143537 | CRBN/VHL ligand discovery history; novel E3 recruiters |
| Assay review | Zorba A, Nguyen V, Koegl M, et al. "Assays and Technologies for Developing Proteolysis Targeting Chimera Degraders." *Future Med. Chem.* 2020; 12(14): 1313–33. | 10.4155/fmc-2020-0073 | 32431173 | Step-by-step assay workflow along ubiquitin–proteasome pathway |
| PROTAC review | Békés M, Langley DR, Crews CM. "PROTAC targeted protein degraders: the past is prologue." *Nat. Rev. Drug Discov.* 2022; 21(3): 181–200. | 10.1038/s41573-021-00371-6 | 35042991 | Comprehensive 20-year review; clinical landscape |
| DCAF1 PROTAC | Nowak RP, Che Y, Sack JS, et al. "DCAF1-based PROTACs with activity against clinically validated targets overcoming intrinsic- and acquired-degrader resistance." *Nat. Commun.* 2023; 14: 8455. | 10.1038/s41467-023-44237-4 | 38177131 | DBt-10 (DCAF1–BTK); overcomes CRBN resistance; DC50 ~149 nM |
| RNF4 ligand | Ward CC, Kleinman JI, Brittain SM, et al. "Covalent Ligand Screening Uncovers a RNF4 E3 Ligase Recruiter for Targeted Protein Degradation Applications." *ACS Chem. Biol.* 2019; 14(11): 2430–40. | 10.1021/acschembio.8b01083 | 31059647 | CCW16 discovery; covalent RNF4 recruiter |
| RNF4 follow-up | Schwalm MP, et al. "Cysteine-reactive covalent chloro-N-acetamide ligands induce ferroptosis mediated cell death." *EMBO Rep.* 2025; 26: e00593-4. | 10.1038/s44319-025-00593-4 | 41102521 | CCW16-derived PROTACs failed to degrade RNF4; CCW16 induces RNF4-independent ferroptosis; MG132 rescue inconclusive at toxic concentrations |
| E3 validation workflow | Miletić N, Weckesser J, Mosler T, et al. "Workflow for E3 Ligase Ligand Validation for PROTAC Development." *ACS Chem. Biol.* 2025; 20(2): 507–21. | 10.1021/acschembio.4c00812 | — | Systematic E3 ligand validation; DCAF1, KEAP1, GID4, TRIM24 landscape |
| PROTACs 2025 review | Qin S, Xiao X. "PROTACs in 2025: from the laboratory concept to clinical breakthrough." *Future Med. Chem.* 2026. | 10.1080/17568919.2026.2655682 | — | ARV-471 milestone; 3 PROTACs in Phase III; VHL→CRBN switch reduced MW, improved oral bioavailability |
| dBET1 linker detail | Lebraud H, Lehn D, Wright D, et al. "Protein Degradation by In-Cell Self-Assembly of Proteolysis Targeting Chimeras." *ACS Cent. Sci.* 2016; 2(12): 932–40. | 10.1021/acscentsci.6b00280 | — | dBET1 linker has ~8 bonds separating linking atoms from JQ1 and thalidomide; comparison with ARV-825 (17 bonds) |
| dBET6 potency detail | Chan KH, Zengerle M, Testa A, Ciulli A. "Plasticity in binding confers selectivity in ligand induced protein degradation." *Sci. Adv.* 2018; 4(10): eaao0598. | 10.1126/sciadv.aao0598 | — | dBET6 DC50/5h ~10 nM for BRD4BD1, ~50 nM for BRD4BD2; dBET1 DC50/5h ~500 nM; dBET23 DC50/5h ~50 nM |
| Cooperativity | Schiemer J, Horst R, Meng Y, et al. "Affinity and cooperativity modulate ternary complex formation to drive targeted protein degradation." *Nat. Commun.* 2023; 14: 4177. | 10.1038/s41467-023-39904-5 | — | SPR-measured cooperativity (α) for BRD4/SMARCA2 VHL PROTACs; bell-shaped ternary complex curves; cooperativity drives cellular potency |
| Permeability | Atilaw Y, Poongavanam V, Svensson Nilsson C, et al. "Solution Conformations Shed Light on PROTAC Cell Permeability." *ACS Med. Chem. Lett.* 2021; 12(1): 107–14. | 10.1021/acsmedchemlett.0c00556 | — | Folded conformations with low 3D PSA favor PROTAC permeability; bRo5 property space |

---

## Changelog

### v3 (2026-04-27) — corrections from v2

1. **NDA date corrected**: v2 said "NDA accepted June 2025." Corrected to: NDA submitted June 6, 2025; NDA accepted August 8, 2025 (Arvinas press release).
2. **CRBN neosubstrate off-target warning added**: New section in Stage 2 and new Beginner Trap #11. Thalidomide/pomalidomide-based PROTACs independently degrade IKZF1/IKZF3/ZFP91/CK1α/GSPT1 as molecular glue neosubstrates. This was entirely missing from v2 and is critical for interpreting degradation data.
3. **Linker terminology clarified**: v2 used "glycolamide" throughout. v3 notes that "glycolamide" is technically correct (used in MS literature) but the PROTAC design literature more commonly says "short flexible amide-ether linker." Both terms retained with explanation.
4. **Assay technology note added**: Western blot vs. HiBiT-CRISPR comparison added to Stage 5. Western blot remains the default; HiBiT is the recommended upgrade for quantitative kinetic profiling.
5. **Cell-line-dependent DC50 note added**: Clarified that DC50/5h ~500 nM is from HiBiT-HEK293, not MV4-11. Different cell lines may give different absolute DC50 values.
6. **Excess competing ligand control added**: New "ideal" control in Stage 4 (excess JQ1 or pomalidomide to block binary engagement).
7. **E3 ligand alone control description expanded**: Now explicitly notes that pomalidomide alone will degrade IKZF1/IKZF3, which is expected and not a PROTAC-specific effect.
8. **Clinical landscape updated**: Catadegbrutinib entry expanded with 2025 Phase III initiation and head-to-head vs. pirtobrutinib detail.
9. **Tier labels refined**: Tier 2 entries now labeled 2a/2b/2c/2d for clearer cross-referencing.
10. **PROTAC vs. molecular glue section expanded**: Added critical note that CRBN ligands used in PROTACs are themselves molecular glues, creating a dual-identity issue.
11. **Commercial availability note added**: Default First Route checklist now notes that dBET1 is commercially available (Tocris, MedChemExpress, Cayman Chemical).
12. **New literature anchors added**: CRBN neosubstrate (Krönke 2014, Bricelj 2026), cooperativity (Schiemer 2023), permeability (Atilaw 2021).
