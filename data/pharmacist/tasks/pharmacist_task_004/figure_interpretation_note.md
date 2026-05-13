# Figure Interpretation Note — Figure 5 (Xia et al., J Nanobiotechnol 2022)

**Paper**: Xia et al., "Targeting therapy and tumor microenvironment remodeling of triple-negative breast cancer by ginsenoside Rg3 based liposomes," Journal of Nanobiotechnology (2022) 20:414. DOI: 10.1186/s12951-022-01623-2.

**Figure title (from paper legend, p. 11)**: "Inhibition effect of Rg3 on CAFs formation and activation."

**Filename note**: The file is named `figure_5_in_vivo_efficacy.png`, but Figure 5 in the paper is the CAFs/TGF-β mechanistic figure, not an in vivo tumor-growth efficacy figure. The in vivo tumor-growth curves are in Figure 4 (tumor volume, tumor weight, body weight; legend on p. 10). The filename is a misnomer.

---

## What The Figure Is Proving

*Sources: figure legend (p. 11), Results text (pp. 9–12), Discussion (p. 15), Methods (pp. 18–20).*

Figure 5 proves that Rg3-containing formulations reduce TGF-β output from 4T1 tumor cells, and that the resulting conditioned medium produces less Smad2/3 phosphorylation and less α-SMA expression in fibroblasts — both in vitro (3T3 cells cultured with 4T1 conditioned medium, panels A–D) and in vivo (4T1 orthotopic tumor tissue after systemic IV treatment, panels E–H). The figure establishes a consistent correlative chain across every measured step of the hypothesized pathway:

> **TGF-β secretion** (panels A, E) → **p-Smad2/3** (panels C, G) → **α-SMA expression** (panels B, C, D, F, G) → **activated CAFs abundance** (panel H)

**Epistemic status** [from Results, p. 11]: The authors write "it can be speculated that Rg3 can inhibit the interaction between tumor cells and CAFs by downregulating TGF-β secretion of tumor cells and the subsequent TGF-β/Smad signaling of CAFs." They use "speculated," not "demonstrated." The SB-431542 control in panels B and D provides one piece of causal evidence [from Results, p. 10]: "with the addition of SB-431542, a TGF-β/Smad inhibitor, the expression of α-SMA in 3T3 cells was lowered, indicating that TGF-β was a dominant factor in 4T1-CM that led to CAFs activation." This proves necessity of TGF-β for CAF activation in vitro, not that Rg3's reduction of TGF-β is the sole or direct causal mechanism in vivo.

**In vitro vs. in vivo divergence** [from Results, p. 12]: "Unlike the in vitro results showing that Rg3 and Rg3-Lp have comparable inhibition efficacy of tumor-CAFs interaction, the level of TGF-β concentration and signaling in tumors of Rg3-Lp group was much lower than that in free Rg3 group (Fig. 5E–H) in vivo owing to the enhanced targeting delivery capacity when Rg3 was formulated into liposomes." The explanation (Glut1-mediated tumor targeting) comes from Figure 2 and the Discussion (p. 15), not from Figure 5 itself.

**Critical note on apparent evidence breadth** [analytical observation, not stated in paper]: The figure's eight panels appear to present eight independent lines of evidence, but they actually measure only three biological variables — TGF-β (panels A, E), p-Smad2/3 (panels C, G), and α-SMA (panels B, C, D, F, G, H) — each assessed by multiple methods (ELISA, Western blot, immunofluorescence, q-PCR, flow cytometry). This is convergent measurement of three variables, not eight independent variables. The strength is methodological triangulation; the limitation is that the entire causal chain rests on a single upstream trigger (TGF-β) and a single downstream marker (α-SMA).

---

## Most Decisive Panel

*Sources: figure legend (p. 11), Results (pp. 10–12), Methods (pp. 19–20). Panel layout observation from the image.*

**Panels C and G** (in vitro and in vivo Western blots, respectively) are the most decisive because they are the only panels that display **two adjacent steps of the hypothesized causal chain in the same assay**: the signaling intermediate (p-Smad2/3) and the downstream CAF marker (α-SMA) co-occurring in the same lanes. When p-Smad2/3 drops and α-SMA drops in the same lanes, the pathway linkage is visible within a single gel.

- **Panel C** [legend, p. 11]: "Western blot detection of α-SMA, p-Smad2/3 and GADPH on 3T3 cells treated with different conditioned 4T1 medium." The Results (p. 10) specify 8 conditioned media: 4T1-CM, 4T1-CM@DTX, 4T1-CM@C-Lp/DTX, 4T1-CM@Nanoxel-PM, 4T1-CM@Rg3, 4T1-CM@Rg3-Lp, 4T1-CM@Rg3/DTX, 4T1-CM@Rg3-Lp/DTX. So panel C has 8 lanes.
- **Panel G** [legend, p. 11]: "Western blot detection of p-Smad2/3, α-SMA, β-actin and GADPH in tumors after treatment with PBS, DTX, C-Lp/DTX, Nanoxel-PM, Rg3, Rg3-Lp, Rg3/DTX and Rg3-Lp/DTX, respectively." So panel G has 8 lanes and 4 protein bands (2 variable: p-Smad2/3, α-SMA; 2 loading controls: β-actin, GAPDH).

**What the visual confirms**: In the image, panels C and G each show two variable-intensity bands that co-vary (both strong or both weak in the same lanes), plus consistent loading-control bands. This co-variation is directly visible without the legend. All other blots (panel B) show only one variable band.

**Panel H** [legend, p. 11]: "Flow cytometry analysis of activated CAFs in tumor." This is the most important **outcome** panel — it shows fewer CAFs exist after Rg3-Lp and Rg3-Lp/DTX treatment — but it does not reveal the mechanism. H tells you *that* fewer CAFs exist; C and G tell you *why*. Moreover [Methods, p. 20]: "CAFs staining (α-SMA) for FACS analysis" — so panel H defines "activated CAFs" by α-SMA positivity, the same marker measured in panels B, C, D, F, and G by different methods. Without the Methods section, a reader might assume CAFs are identified by a distinct marker (e.g., FAP or PDGFRα).

**Recommended reading order**: C → G → H → A → E → B → D → F. Start with the panels that show pathway linkage (C, G), then the functional outcome (H), then the upstream trigger (A, E), then the single-step confirmations (B, D, F).

---

## What The Visual Alone Shows

*Source: direct observation of `figure_5_in_vivo_efficacy.png` (1200 × 1094 px, downscaled from 1961 × 1787 in the PDF). No paper text used in this section.*

The figure image contains eight labeled panels (A–H) arranged in approximately three rows:

- **Row 1** (top): Panel A (bar chart, left), Panel B (Western blot, center-left), Panel C (Western blot, right half)
- **Row 2** (middle): Panel D (fluorescence microscopy grid, spanning most of the width), Panel E (bar chart, right)
- **Row 3** (bottom): Panel F (bar chart, left), Panel G (Western blot, center-left), Panel H (bar chart, right half)

### What is directly readable from the image

1. **Consistent directional pattern**: In all four bar charts (A, E, F, H), the left-side bars are taller and the right-side bars are shorter. In all three Western blots (B, C, G), band intensity is stronger in left lanes and weaker in right lanes. In the fluorescence grid (D), green signal is bright in left-side conditions and dim/absent in right-side conditions. This consistent left-to-right decrease across every panel and every assay type is the single strongest visual observation.

2. **Co-varying bands in C and G**: Panels C and G each show two bands whose intensity varies across lanes in the same direction (both strong or both weak together), plus one or two bands of constant intensity (loading controls). Panel B shows only one variable band plus one constant band. This co-variation in C and G — visible without any legend — hints that two related proteins are being measured together.

3. **Panel letter labels**: The letters A–H are legible, establishing panel identity.

4. **Asterisk significance markers**: Asterisks (*) and brackets are visible above certain bars in panels A, E, F, H, indicating statistical comparisons were performed.

5. **Error bars**: Present on all bar charts, indicating replicate measurements.

6. **Approximate lane/bar counts**: Panels A, E, F, H each show approximately 8 bars. Panels C and G each show approximately 8 lanes. Panel B shows approximately 5–11 lanes (ambiguous at this resolution). Panel D shows a grid of approximately 8–13 fluorescence images.

### What is NOT readable from the image

1. **Y-axis labels and units**: Illegible. A reader cannot determine what is being measured in any bar chart.
2. **X-axis group labels**: Illegible. A reader cannot determine which treatment group corresponds to which bar or lane.
3. **Protein name labels on blots**: At 1200 px width, the left-edge labels on panels C and G are at the threshold of legibility — "α-SMA" and "p-Smad2/3" may be partially discernible at maximum zoom, but this is uncertain and unreliable.
4. **Whether data is in vitro or in vivo**: Nothing in the image distinguishes panels A–D (in vitro) from panels E–H (in vivo).
5. **Cell type or tissue source**: Not indicated visually.
6. **The conditioned-medium experimental design**: Completely invisible.
7. **Causal direction**: The visual shows correlation (everything decreases left-to-right) but cannot establish which variable causes which.
8. **Scale of effect**: Numerical y-axis values are unreadable, so the magnitude of differences cannot be quantified from the image.

### Summary

The image proves that a consistent directional effect exists across eight panels using at least four different assay types (bar charts, Western blots, fluorescence microscopy, and what appears to be flow cytometry). Panels C and G uniquely show two co-varying bands, suggesting a pathway relationship. Everything else — what is measured, what the groups are, the experimental design, the causal interpretation — requires the paper text.

---

## What Requires Paper Context

*Each item below is information that cannot be recovered from the figure image and must come from the paper legend, results text, or methods. Source page numbers are given for each claim.*

### Essential for basic comprehension

1. **The two-step conditioned-medium design (panels A–D)** [Methods, p. 18–19; Results, p. 10]: This is the single most critical gap. The in vitro panels do not show 3T3 fibroblasts treated directly with drugs. The actual design is: (step 1) treat 4T1 tumor cells with one of 8 formulations (DTX 5 μg/mL for ELISA, 0.5 μg/mL for WB); (step 2) collect the conditioned medium (CM) from those treated 4T1 cells after 24 h; (step 3) expose 3T3 fibroblasts to that CM and measure their response. This "tumor educates fibroblasts via secreted factors" design is completely invisible from the figure. Without it, a reader would assume the drugs were applied directly to fibroblasts — which would make the lower α-SMA in Rg3 groups ambiguous (is Rg3 acting on fibroblasts directly, or on tumor cells to change what they secrete?). The two-step design proves Rg3 acts on the tumor side (reducing TGF-β secretion), not directly on fibroblasts.

2. **What each panel measures** [legend, p. 11]:
   - A = TGF-β concentration in 4T1-CM by ELISA (in vitro, n = 3)
   - B = α-SMA and GAPDH Western blot on 3T3 cells after treatment with TGF-β (20 ng/ml), TGF-β/SB-431542, PBS, different conditioned 4T1 medium, and 4T1-CM/SB-431542
   - C = α-SMA, p-Smad2/3, and GAPDH Western blot on 3T3 cells treated with different conditioned 4T1 medium
   - D = IF observation of α-SMA in 3T3 cells after treatment with TGF-β (20 ng/ml), TGF-β/SB-431542, PBS, 4T1-CM, 4T1-CM/SB-431542, and different conditioned 4T1 medium
   - E = TGF-β concentration in tumor tissues by ELISA (in vivo, n = 3)
   - F = α-SMA gene expression by q-PCR in tumor tissues (in vivo, n = 3)
   - G = p-Smad2/3, α-SMA, β-actin, and GAPDH Western blot in tumor tissue (in vivo)
   - H = Flow cytometry analysis of activated CAFs in tumor (in vivo, n = 3)

3. **The in vitro vs. in vivo split** [Results, pp. 9–12; Methods, p. 19]: Panels A–D are in vitro (3T3 fibroblasts + 4T1 conditioned medium in culture); panels E–H are in vivo (tumor tissue from 4T1-bearing BALB/c mice after systemic IV treatment, 10 mg/kg DTX every 4 days for 20 days). This split is invisible in the figure and is essential for understanding the Rg3-Lp vs. free Rg3 divergence.

### Essential for critical evaluation

4. **The SB-431542 control in panels B and D** [Results, p. 10; Methods, p. 18]: SB-431542 is a TGF-β receptor inhibitor (MCE, USA). Its inclusion proves TGF-β is a "dominant factor in 4T1-CM that led to CAFs activation" (Results, p. 10). Without the paper text, a reader seeing panel B cannot understand why certain lanes show reduced α-SMA alongside the TGF-β-stimulated lanes.

5. **The causal narrative and its epistemic status** [Results, p. 11; Discussion, p. 15]: The figure shows each step of the cascade separately, but the causal story connecting them comes from the paper text. The authors use "speculated" (p. 11). The Discussion (p. 15) says "TGF-β secreted by 4T1 cells was essential for facilitating the conversion of normal fibroblasts into CAFs" — "essential" here means necessary (TGF-β is needed), not sufficient (TGF-β alone is enough), and the evidence is in vitro only.

6. **What "activated CAFs" means in panel H** [Methods, p. 20]: "CAFs staining (α-SMA) for FACS analysis." Panel H's "activated CAFs" are defined by α-SMA positivity — the same marker measured in panels B, C, D, F, and G by different methods. Without the Methods, a reader might assume CAFs are identified by a distinct marker.

### Needed for full quantitative interpretation

7. **Treatment group abbreviations** [Abbreviations, p. 20; Results, p. 10]: The x-axis labels use nested notation. The 8 in vivo groups are: PBS, DTX, C-Lp/DTX, Nanoxel-PM, Rg3, Rg3-Lp, Rg3/DTX, Rg3-Lp/DTX. The 8 in vitro CM groups are: 4T1-CM (pretreated with PBS), 4T1-CM@DTX, 4T1-CM@C-Lp/DTX, 4T1-CM@Nanoxel-PM, 4T1-CM@Rg3, 4T1-CM@Rg3-Lp, 4T1-CM@Rg3/DTX, 4T1-CM@Rg3-Lp/DTX.

8. **Quantitative magnitudes** [Results, pp. 9, 12]:
   - In vitro (panel A, p. 9): "The TGF-β concentration in Rg3-Lp/DTX group was only half of that in C-Lp/DTX group."
   - In vivo (panels E–F, p. 12): "The neoplastic TGF-β concentration in Rg3-Lp and Rg3-Lp/DTX group was nearly half of that in C-Lp/DTX group and consequently, the α-SMA gene expression of tumor tissues in Rg3-Lp and Rg3-Lp/DTX group was decreased to one-third of that in C-Lp/DTX group."

9. **Why Rg3-Lp outperforms free Rg3 in vivo** [Results, p. 12; Discussion, p. 15]: The explanation (Glut1-mediated tumor targeting, established in Figure 2) comes from outside Figure 5. The figure shows the result but not the reason.

### Minor note

10. **Typo in the paper**: The figure legend and several paper sections write "GADPH" instead of the correct "GAPDH" (glyceraldehyde-3-phosphate dehydrogenase). This is a typographical error in the published paper, not a different protein. The WB Methods (p. 19) correctly lists "anti-GAPDH (30202ES40, Yeasen)."

---

## Retell Sentence

Rg3-containing formulations make 4T1 tumor cells secrete less TGF-β into their surrounding medium [paper context: ELISA, panels A and E], so fibroblasts exposed to that medium show less Smad2/3 phosphorylation and less α-SMA expression [paper context: WB panels C and G; visual: co-varying bands] — and in vivo, Rg3-liposomes deliver this CAFs-suppression effect to the actual tumor far more effectively than free Rg3 [paper context: Glut1 targeting from Figure 2] because the liposome targets Glut1 on tumor cells; but the entire eight-panel figure ultimately measures only three biological variables (TGF-β, p-Smad2/3, α-SMA) by multiple methods [analytical observation], the visual alone shows only a consistent directional decrease across all panels without identifying what is measured or why, and the causal chain connecting the variables remains "speculated" [authors' word, p. 11], not directly demonstrated.
