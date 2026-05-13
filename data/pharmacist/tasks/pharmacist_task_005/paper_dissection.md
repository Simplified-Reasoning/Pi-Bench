# Paper Dissection Note (v5 — re-grounded from PDF + SVGs; v4 treated as flawed draft)

**Paper**: Liu et al., *Nature Communications* (2018) 9:2612, DOI: 10.1038/s41467-018-05035-5
**Title**: Peptide density targets and impedes triple negative breast cancer metastasis

**Sources used**: `s41467-018-05035-5.pdf` (11 pages), `figure_1_study_design.svg`, `figure_3_in_vivo_results.svg`

**v4 → v5 corrections**: (1) IV-model protocol was pre-incubation + wash, not co-injection — changes the mechanistic interpretation. (2) Core Question no longer claims 74k "does not translate to metastasis suppression in vivo" — 74k was never tested in vivo. (3) sDV1 is a single-residue substitution (L→A at position 1), not a scrambled sequence in the usual sense. (4) SVG Panel A discrepancy retained and sharpened. (5) New "What the paper supports / What remains uncertain / What experiment would close the gap" structure added to Boundary section.

---

## Core Question

Can a *specific* surface density of the CXCR4-binding peptide DV1 on a liposome suppress TNBC metastasis — where neither the mere presence of DV1, nor a lower density, nor a clinically tested single-molecule CXCR4 antagonist can? `[PDF+Fig1]`

The paper's answer: yes, and the density is 24,000 molecules/μm² (interpeptide spacing ≈ 45 Å). The authors' mechanistic claim is that this spacing matches the CXCR4 homodimer binding-pocket distance (PDF p. 8, citing ref 29: Wu et al. 2010 crystal structure), enabling simultaneous dual-peptide engagement of both subunits. This dual engagement blocks two downstream signaling arms — p115 RhoGEF (via Gα12/13) and p85-PI3K (via Gαi, per Fig. 6b diagram) — that must *both* be suppressed to halt metastasis (PDF p. 5, Fig. 6). Lower densities (9k, 71 Å spacing) permit only single-subunit binding and achieve only partial pathway knockdown. Higher densities (74k, 26 Å spacing) inhibit migration in vitro through an uncharacterized, p115 RhoGEF-independent pathway (PDF p. 8), but 74k was never tested in the in vivo metastasis models, so its in vivo effect is unknown. `[PDF]`

Figure 1 (SVG) frames the study as three modules — peptide construct (A) → in vitro density screen (B) → in vivo metastasis model (C) — and states the key idea: "targeting and signaling regulation depend on the density of DV1 peptides displayed on the liposome surface, not just on whether DV1 is present." This is the hypothesis; the proof comes from the in vivo endpoint. `[Fig1]`

---

## Primary Evidence

The decisive data are the **in vivo metastasis results** (PDF Figs. 4–5), not uptake, not binding, not migration. `[PDF]`

**IV-injection model (PDF Fig. 4, 31 days)**: MDA-MB-231-Luc cells were pre-incubated with liposomes (or controls) for 1 h on ice, then washed to remove unattached liposomes, and injected IV at 3.33 × 10⁶ cells/mL (300 μL per mouse) (PDF Methods p. 10). This is not a co-injection or a circulating-liposome model — the liposomes acted on the cells *before* injection. At day 31, 5/6 L-DV1-24k mice had no detectable tumor signal; the one positive mouse showed 951 kp sec⁻¹ cm⁻² sr⁻¹ (background: 15). Sham averaged 5.1 × 10⁵; L-DV1-9k averaged 1.3 × 10⁴ kp sec⁻¹ cm⁻² sr⁻¹. Post-mortem organ evaluation: sham showed metastasis in 100% of lungs, 100% of brains, 67% of livers, 67% of spleens, 33% of kidneys. Lung metastasis was observed in all conditions *except* L-DV1-24k (PDF p. 5, Fig. 4c–e). `[PDF]`

*Methodological implication*: Because cells were pre-treated and washed, the IV model tests whether a single 1 h exposure to L-DV1-24k durably alters cell behavior (signaling, migration capacity) before the cells ever encounter the in vivo microenvironment. This is a stronger claim than "liposomes circulate and continuously block CXCR4" — it implies that 24k-density engagement reprograms the cell's metastatic machinery in a sustained way. `[PDF]`

**Orthotopic primary-tumor model (PDF Fig. 5, 27 days)**: MDA-MB-231-Luc cells were injected into the mammary fat pad, followed by weekly IV injections of PBS, L-sDV1-24k, or L-DV1-24k (100 μL, 11.8 mg/kg lipid, 0.4 mg/kg peptide; administered at days 8, 14, 20, 23, 26; PDF Methods p. 10). Five of six L-DV1-24k mice exhibited no spontaneous metastases over 27 days. L-DV1-24k also significantly impaired primary tumor growth — without encapsulating any chemotherapeutic (PDF p. 5, Fig. 5a–d). `[PDF]`

*Methodological contrast*: Unlike the IV model, the orthotopic model involves repeated systemic dosing against an established primary tumor. The two models test different questions: the IV model asks "can pre-treatment prevent metastatic seeding?"; the orthotopic model asks "can repeated treatment prevent spontaneous metastasis from a growing tumor?" Both answer yes for L-DV1-24k. `[PDF]`

**LY2510924 negative control**: This clinical CXCR4 peptide antagonist (in clinical trials) had no effect on metastasis in the IV model (PDF p. 5, Supplementary Fig. S9). This is the sharpest control in the paper: it proves that blocking CXCR4 with a single-molecule antagonist is insufficient, and that the multivalent density-matched presentation is what distinguishes L-DV1-24k. `[PDF]`

**24k vs. 9k — the most informative density comparison**: Both are tested in the IV model. 9k achieves a ~40-fold reduction in luminescence versus sham (1.3 × 10⁴ vs. 5.1 × 10⁵) but does not eliminate metastasis. 24k achieves near-complete elimination (5/6 tumor-free). The mechanistic explanation (PDF p. 5, 8): at 71 Å spacing, 9k likely binds only one subunit of the CXCR4 homodimer, yielding 17% p115 RhoGEF suppression and 44% p85-PI3K inhibition — partial but insufficient. `[PDF]`

**L-sDV1-24k partial-activity control**: sDV1-N3 differs from DV1-N3 by a single residue at position 1 (L→A; PDF Methods p. 9), with IC₅₀ = 23,500 nM vs. DV1's 32 nM (PDF p. 2, citing ref 10). Despite this ~730-fold weaker affinity, L-sDV1-24k showed reduced tumor growth and metastasis relative to sham in the orthotopic model, "due to the similarity in peptide sequence to DV1" (PDF p. 5). This partial effect confirms that the anti-metastatic outcome is peptide-sequence-specific, not merely a liposome or PEG effect — but also shows that even a weak CXCR4 binder at 24k density retains some activity. `[PDF]`

SVG Figure 3, Panel C summarizes the in vivo outcome qualitatively: "Primary-tumor escape: slower with 24k DV1," "Metastatic spread: suppressed for 27 days," "signaling depends on peptide density." All quantitative values above come from the PDF, not the SVG. `[PDF+Fig3]`

---

## Supporting Evidence

These intermediate readouts validate the concept and explain the mechanism but are not the biological endpoint. `[PDF+Fig3]`

**Binding and uptake (PDF Fig. 2d–f)**: L-DV1-24k exhibited the highest binding and uptake on both MDA-MB-231 and MDA-MB-436 by flow cytometry (Fig. 2d–e) and confocal microscopy (Fig. 2f). The PDF legend states: "L-DV1-24k exhibited equal or greater binding relative to L-DBCO and all other densities" (p. 4). Uptake is non-monotonic: it peaks at 24k and declines through 39k–74k. `[PDF]`

*SVG discrepancy note*: SVG Panel A shows a polyline across five densities (9k, 24k, 39k, 53k, 74k). The polyline coordinates place the visual peak at the **39k** position (third point, y=178, highest on screen), not 24k (second point, y=205). This contradicts the PDF data, where 24k is the clear peak on both cell lines with statistical significance markers. The SVG is a simplified schematic that does not faithfully reproduce the quantitative flow cytometry data. **Use PDF Fig. 2d–e, not SVG Panel A, for the uptake peak identity.** `[Fig3]`

**Migration inhibition (PDF Fig. 3b)**: L-DV1-24k showed significantly lower cell migration than all other densities in the transwell assay (n ≥ 9, p < 0.05 or p < 0.01; PDF p. 5, Fig. 3 legend). Free DV1-N3 peptide also inhibited migration in a concentration-dependent manner (PDF Fig. 3a), but these are separate experimental panels with different controls — a direct magnitude comparison between free peptide and liposomal formulation should be made cautiously. SVG Panel B shows four bars (L-DBCO, 24k, 39k, 74k) — a subset of the full PDF Fig. 3b data, which also includes 9k, 53k, and L-sDV1-24k. In the SVG, 24k is the tallest bar. `[PDF+Fig3]`

**Signaling dissection (PDF Fig. 6, p. 5–8)**: This is the mechanistic keystone. Three effectors were measured by Western blot after 1 h pre-incubation:

| Effector | L-DV1-9k | L-DV1-24k | L-DV1-39k/53k/74k | Interpretation |
|---|---|---|---|---|
| p115 RhoGEF | 17% suppression | Undetectable | Variable (see Fig. 6a bar chart) | Density-dependent; requires dual homodimer engagement |
| p85-PI3K | 44% inhibition | 96.5% inhibition | Variable | Density-dependent; same geometric logic |
| p55γ-PI3K | ~40% inhibition | ~40% inhibition | ~40% for all DV1 densities | Density-*independent*; insufficient alone for metastasis blockade |

The uniform ~40% p55γ-PI3K inhibition across all DV1 densities is the critical negative result: it shows that a pathway can be inhibited without suppressing metastasis, proving that *which* pathways are blocked matters, not just *whether* some CXCR4 signaling is disrupted. Only simultaneous blockade of p115 RhoGEF + p85-PI3K (achieved exclusively at 24k) correlates with metastasis suppression. The PDF (p. 8) notes: "this suggested that p55γ-PI3K has less impact on metastasis." `[PDF]`

**DV1 peptide characterization (PDF Fig. 1, p. 2–3)**: DV1-N3 competitively binds CXCR4 with IC₅₀ = 32 nM, stronger than LV1 (456 nM) and AMD3100 (890 nM). AFM unbinding forces on DV1-N3-modified tips were ~120% higher on MDA-MB-231 and MDA-MB-436 relative to MCF-10A (PDF p. 3, Fig. 1d). CXCR4 surface densities: MDA-MB-231 = 85 molecules/μm², MDA-MB-436 = 334 molecules/μm² (PDF p. 3). This justifies the peptide choice but does not address density-dependent outcomes. `[PDF]`

---

## Rejected Interpretation

**Rejected 1 — "The highest-density formulation is the best."** `[PDF+Fig3]`

Uptake is non-monotonic: 74k has the most peptide but lower uptake than 24k (PDF Fig. 2d–e). However, 74k was **not tested** in either in vivo metastasis model — only sham, L-sDV1-24k, L-DV1-9k, and L-DV1-24k were used in the IV model; only sham, L-sDV1-24k, and L-DV1-24k in the orthotopic model (PDF Figs. 4–5, Methods p. 10). So the claim "highest density fails in vivo" cannot be made from direct in vivo data. What *can* be said: 74k's moderate migration inhibition in vitro operates through a p115 RhoGEF-independent pathway (PDF p. 8), meaning it does not engage the dual-blockade mechanism that correlates with metastasis suppression at 24k. `[PDF+Fig3]`

**Rejected 2 — "Any CXCR4 pathway inhibition is sufficient to block metastasis."** `[PDF]`

The p55γ-PI3K result directly refutes this. All DV1 densities inhibit p55γ by ~40%, yet only 24k suppresses metastasis. p55γ inhibition alone — despite its known role in ALK-induced AKT phosphorylation and cell migration (PDF p. 5, citing ref 24) — is insufficient. The paper's logic: metastasis blockade requires *simultaneous* suppression of both the Gα12/13 → p115 RhoGEF → RhoA/ROCK/LIMK arm and the Gαi → p85-PI3K → AKT arm (PDF Fig. 6b). `[PDF]`

**Rejected 3 — "L-DV1-74k partially works through the same mechanism as 24k, just less efficiently."** `[PDF]`

The PDF (p. 8) explicitly states: L-DV1-74k's migration inhibition "was independent of p115 RhoGEF, suggesting that this particular density may inhibit other CXCR4 pathways not investigated here." At 26 Å spacing (roughly half the homodimer distance), 74k engages CXCR4 in a geometrically distinct mode. Its partial migration effect is mechanistically unrelated to the dual-blockade that defines 24k's anti-metastatic action. `[PDF]`

**Rejected 4 — "Figure 1 (SVG) alone explains why the paper matters."** `[PDF+Fig1]`

Figure 1 (SVG) presents the study design (Module A → B → C) and states the density-dependence hypothesis. A reader who stops here understands *what the authors proposed* but has seen no evidence. The concept-validation data (binding, AFM) in PDF Figs. 1–2 confirm that DV1 binds CXCR4 selectively, but they do not address density-dependent signaling or metastasis. The proof requires the in vivo data (PDF Figs. 4–5) and the signaling dissection (PDF Fig. 6). `[PDF+Fig1]`

---

## First Figure To Inspect

**Figure 3 (SVG), Panel C** — the in vivo metastasis summary — not Panel A (uptake) and not Figure 1 (study design). `[Fig3]`

**Rationale**: Panel C directly states the biologically decisive outcome: primary-tumor escape is slower with 24k DV1, metastatic spread is suppressed for 27 days, and signaling depends on peptide density. A reader who starts here immediately grasps *what the paper proved* before encountering the concept-validation setup. `[Fig3]`

**What is directly visible in the SVG**: Panel A shows a polyline across five densities — but the visual peak is at 39k, not 24k (see SVG discrepancy note in Supporting Evidence; do not trust this for the uptake optimum). Panel B shows four migration-inhibition bars (L-DBCO, 24k, 39k, 74k) with 24k tallest. Panel C provides qualitative text on the in vivo outcome. The SVG subtitle warns: "better uptake alone does not fully predict the best in vivo outcome." `[Fig3]`

**What still requires PDF context**: (a) Quantitative metastasis data — 5/6 mice tumor-free, luminescence values, organ-by-organ breakdown (PDF Figs. 4–5). (b) The critical methodological detail that the IV model used pre-incubation + wash, not co-injection (PDF Methods p. 10). (c) The CXCR4 homodimer spacing rationale — 45 Å interpeptide distance matches the homodimer binding-pocket distance (PDF p. 8, ref 29). (d) Signaling pathway specifics — p115 RhoGEF undetectable at 24k vs. 17% at 9k; p85-PI3K 96.5% vs. 44%; p55γ-PI3K uniform ~40% (PDF Fig. 6). (e) The LY2510924 negative control — clinical antagonist failed (PDF p. 5, Supplementary Fig. S9). (f) The distinction between the IV model (31 days, pre-incubation design) and the orthotopic model (27 days, repeated systemic dosing). (g) The SVG Panel A peak discrepancy — the PDF, not the SVG, is authoritative for the uptake optimum. `[PDF+Fig3]`

**Why not Figure 1 first**: Figure 1 (SVG) is study-design context. It tells you *what the authors planned to test* and *what concept they propose*. It contains no outcome data. A left-to-right, Figure-1-first reading reconstructs the authors' workflow rather than the paper's proof structure. `[Fig1]`

---

## Boundary And Follow-up

### What the paper supports

1. **L-DV1-24k suppresses metastasis in two complementary in vivo models.** 5/6 mice tumor-free in both the IV model (31 days, single pre-treatment) and the orthotopic model (27 days, weekly dosing). This is the strongest claim in the paper. `[PDF]`
2. **The anti-metastatic effect is density-specific, not merely DV1-dependent.** L-DV1-9k achieves partial but insufficient metastasis reduction; L-sDV1-24k (single-residue variant, ~730× weaker affinity) achieves partial reduction; LY2510924 (clinical single-molecule antagonist) achieves nothing. Only L-DV1-24k achieves near-complete suppression. `[PDF]`
3. **24k uniquely co-suppresses p115 RhoGEF and p85-PI3K.** The signaling dissection (PDF Fig. 6) shows that only 24k drives both effectors to near-zero, while all other densities leave at least one arm partially active. The p55γ-PI3K uniform ~40% inhibition across all densities serves as an internal negative control — pathway inhibition without metastasis suppression. `[PDF]`
4. **The 45 Å interpeptide spacing at 24k matches the CXCR4 homodimer binding-pocket distance.** This geometric argument (PDF p. 8, ref 29) provides a structural rationale for why 24k — and not 9k (71 Å) or 74k (26 Å) — enables dual-subunit engagement. `[PDF]`
5. **No encapsulated drug is needed.** The liposomes contain no chemotherapeutic; the therapeutic effect comes entirely from surface-mediated signaling modulation (PDF p. 5, 7). `[PDF]`

### What remains uncertain

1. **Whether 24k is truly the global optimum, or merely the best among the five densities tested.** Only 9k, 24k, 39k, 53k, and 74k were synthesized. Densities between 9k and 24k (e.g., 15k, 20k) or between 24k and 39k (e.g., 30k) were never tested. The in vivo models tested an even narrower range: only 9k and 24k in the IV model, and only 24k in the orthotopic model. The possibility that a nearby density (e.g., 20k or 30k) performs equally well or better is not excluded. `[PDF]`

2. **Whether the geometric-match explanation is the actual cause, or a post-hoc correlation.** The 45 Å spacing matches the CXCR4 homodimer distance from the Wu et al. crystal structure (ref 29), but the paper does not independently verify that dual-subunit engagement is occurring. No crosslinking, FRET, or cryo-EM data confirm that two DV1 peptides simultaneously occupy both binding pockets of a single homodimer. The geometric match is consistent with the signaling data but remains an inference. `[PDF]`

3. **Whether the IV-model result reflects durable reprogramming or transient signaling suppression.** The pre-incubation + wash protocol means cells received a single 1 h exposure to L-DV1-24k before injection. That this single exposure prevented metastasis for 31 days implies sustained signaling changes — but the paper does not measure signaling at later time points. The Western blot data (PDF Fig. 6) were collected after 1 h pre-incubation in vitro, not from in vivo tumors. Whether p115 RhoGEF and p85-PI3K remain suppressed days or weeks later is unknown. `[PDF]`

4. **Whether 24k works against high-CXCR4 tumors in vivo.** Both in vivo models used MDA-MB-231-Luc (85 CXCR4/μm²). MDA-MB-436 (334 CXCR4/μm²) was tested only in vitro. The homodimer-geometry argument predicts that 24k should be optimal regardless of receptor density, but this has not been confirmed in a high-CXCR4 in vivo model. `[PDF]`

5. **What 74k actually does.** Its migration inhibition is p115 RhoGEF-independent (PDF p. 8), but the alternative pathway is uncharacterized. Whether 74k would suppress or promote metastasis in vivo is completely unknown — it was never tested. `[PDF]`

6. **Whether uptake and geometry can be decoupled.** Uptake and dual-pathway blockade both peak at 24k. The p55γ result (uniform ~40% across densities, independent of uptake magnitude) hints that geometry drives the differential signaling — but the paper does not decouple them directly. `[PDF+Fig3]`

7. **Durability beyond 27–31 days.** Both models ended at 27–31 days. Whether metastasis suppression persists, or whether CXCR4 downregulation or alternative metastatic pathways emerge under sustained L-DV1-24k pressure, is unaddressed. `[PDF]`

### What experiment would tighten the gap

| Uncertainty | Proposed experiment | What it would resolve |
|---|---|---|
| Is 24k the true optimum? | Synthesize 15k, 20k, 28k, 33k densities; test in the orthotopic model alongside 24k | Whether the optimum is a sharp peak at 24k or a broad plateau around 20–30k |
| Is dual-subunit engagement real? | Crosslink L-DV1-24k to CXCR4 on live cells; resolve by cryo-EM or proximity ligation assay | Whether two DV1 peptides simultaneously occupy both pockets of one homodimer |
| Is the IV-model effect durable reprogramming? | Harvest tumors from IV-model mice at days 7, 14, 31; Western blot for p115 RhoGEF and p85-PI3K | Whether signaling suppression persists in vivo beyond the initial 1 h exposure |
| Does 24k work for high-CXCR4 tumors? | Orthotopic model with MDA-MB-436-Luc (334 CXCR4/μm²) | Whether the geometric optimum holds when receptor density is 4× higher |
| What does 74k do in vivo? | Add L-DV1-74k arm to the IV and orthotopic models | Whether the p115-independent pathway has any anti-metastatic effect, or is neutral/harmful |
| Can uptake and geometry be separated? | Vary PEG length or lipid composition to shift uptake without changing interpeptide spacing (or vice versa) | Whether the anti-metastatic effect tracks with geometry (spacing) or with uptake magnitude |

The single highest-priority experiment is the **finer density sweep (15k–33k) in the orthotopic model**: it would determine whether 24k is a sharp optimum or an approximate one, and whether the homodimer-distance explanation is predictive or coincidental. If 20k and 28k perform equally well, the geometric-match story weakens; if only 24k works, it strengthens considerably. `[PDF]`

---

## One-Line Takeaway

A specific peptide surface density — 24k molecules/μm², matching the CXCR4 homodimer geometry — simultaneously blocks two metastasis-driving signaling arms after a single pre-treatment exposure, suppressing TNBC metastasis in vivo without any encapsulated drug, an outcome that no single-molecule antagonist, no lower density, and no other tested density can replicate.
