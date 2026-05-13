# Adapalene Compound Property Sheet (Revised v8)

> **Status**: v8 corrects errors found in v7 by treating v7 as a flawed draft. Specific v7 errors: (a) adamantyl fragment formula stated as "C₁₀H₁₅" without noting this is the substituent not the parent cage; (b) whole-molecule XLogP 7.7 placed in the adamantyl-cage row, implying the cage alone has that logP; (c) "cleared from plasma within 72 h" dropped the "all but one subject" qualifier; (d) Study 2 phrasing "traces below LOQ" was ambiguous — should say "between LOD and LOQ"; (e) §1.10 note conflated retinoid classification (from §1 Highlights) with vitamin A toxicity (from §10); (f) mouse carcinogenicity "no relevant finding reported" was inference from silence, not a directly sourced negative result; (g) §2.1 "cage cannot be modified" was a tautology, not a useful inference; (h) carbomer 940 equated with carbomer homopolymer type C without evidence they are identical; (i) v7 status note praised v6 instead of treating it as flawed; (j) priority ranking conflated problem severity with degree of unknownness; (k) R02 attributed logP dominance to the adamantyl cage without local-file support; (l) missing 12-week re-evaluation timeline from §2. All corrected below.

> **Rule**: Any statement that sounds like a reassuring conclusion, a causal narrative, or a generalization beyond what the local files directly state must be demoted to §2 or flagged inline, even if it feels intuitively correct. All claims in §1 are now re-verified against the PDF page text.

---

## 1. Known Facts (Directly Sourced from Local Files — Observational Only)

### 1.1 Identity
| Field | Value | Source |
|---|---|---|
| Compound | Adapalene | compound_identity.md |
| PubChem CID | 60164 | compound_identity.md |
| Chemical name | 6-[3-(1-adamantyl)-4-methoxyphenyl]-2-naphthoic acid | Label §11 (page 6) |
| Molecular formula | C₂₈H₂₈O₃ | compound_identity.md; PubChem JSON; Label §11 |
| Molecular weight | 412.53 | Label §11 (PubChem JSON rounds to 412.5) |
| SMILES | `COC1=C(C=C(C=C1)C2=CC3=C(C=C2)C=C(C=C3)C(=O)O)C45CC6CC(C4)CC(C6)C5` | PubChem JSON |
| Drug class | Retinoid | Label Highlights, page 1: "DIFFERIN Gel, 0.3%, is a retinoid" |
| NDA | NDA021753 | Label page 15 (SPL marketing information) |
| Initial U.S. Approval | 1996 | Label Highlights, page 1 |
| Label revision date | 12/2023 | Label page 15 |

### 1.2 Physicochemical Properties (Measured / PubChem-Sourced)
| Property | Value | Source |
|---|---|---|
| XLogP | 7.7 | PubChem JSON (whole-molecule value) |
| TPSA | 46.5 Å² | PubChem JSON |
| H-bond donors | 1 | PubChem JSON |
| H-bond acceptors | 3 | PubChem JSON |
| Rotatable bonds | 4 | PubChem JSON |
| Physical form | White to off-white powder | Label §11 |
| Solubility: THF | Soluble | Label §11 |
| Solubility: ethanol | Very slightly soluble | Label §11 |
| Solubility: water | Practically insoluble | Label §11 |

> **v8 correction**: XLogP 7.7 is now explicitly labeled as a whole-molecule value. v7 placed it in the adamantyl-cage row of §1.3, implying the cage alone had that logP.

> **Demotion carried forward**: "Probably not very water soluble" (original draft) understated the label's **practically insoluble** — a hard gate, not a soft trend. See risk R01.

### 1.3 Structural Features (Observational Description Only)

> **v8 correction**: v7 stated the adamantyl fragment formula as "C₁₀H₁₅" without clarifying this is the substituent (one H replaced by bond), not the parent adamantane cage (C₁₀H₁₆). Neither formula appears in local files. This section now describes only what the SMILES directly shows, without asserting fragment formulas.

| Feature | What the local files show | What they do NOT show |
|---|---|---|
| Adamantyl cage | SMILES contains a tricyclic saturated hydrocarbon substituent with no O or N atoms (the `C45CC6CC(C4)CC(C6)C5` fragment) | Which structural feature contributes most to logP 7.7 — the whole-molecule XLogP cannot be decomposed from local files. Demoted to §2.1. |
| Naphthoic acid | SMILES contains one –COOH group (`C(=O)O`); PubChem H-bond donor count = 1 | Whether this is the "sole ionizable group" — interpretive (H-bond donor count = 1 is consistent with but does not prove sole ionizability, since non-acidic donors exist). Demoted to §2.1. |
| Methoxy group | SMILES contains one –OCH₃ on the phenyl linker (`COC1=C(...)`) | Whether it is "not a formulation lever" — not in local files. Demoted to §2.1. |
| Overall scaffold | C₂₈H₂₈O₃ with one –COOH and one –OCH₃ as the only oxygen-containing groups | Whether "solubilization must target the acid" — formulation strategy claim not in local files. Demoted to §2.2. |

### 1.4 Marketed Formulation (Differin Gel 0.3%)
| Attribute | Detail | Source |
|---|---|---|
| Dosage form | Off-white aqueous gel (§3); topical aqueous gel (§11) | Label §3 (page 3), §11 (page 6) |
| Strength | 0.3% (3 mg/g) | Label §3, §11 |
| Excipients | Carbomer 940, edetate disodium, methylparaben, poloxamer 124, propylene glycol, purified water, sodium hydroxide; may contain hydrochloric acid for pH adjustment | Label §11 (page 6); SPL inactive ingredients (page 14) also lists "Carbomer Homopolymer Type C" |
| Carbomer identity note | Label §11 says "carbomer 940"; SPL data says "Carbomer Homopolymer Type C." Whether these are identical or the SPL term is a broader classification is not stated in local files. | Label §11 vs page 14 |
| pH | Not stated in label | — |
| Storage | 20–25°C (68–77°F); excursions 15–30°C (59–86°F); protect from freezing | Label §16 (page 9) |
| Pack (current) | 45 g pump (NDC 0299-5918-25); marketing 09/15/2009–02/01/2027 | Label page 15 |
| Pack (discontinued) | 45 g tube (NDC 0299-5918-45), 15 g tube (NDC 0299-5918-15), 2 g tube (NDC 0299-5918-02) — all ended 01/01/2018 | Label page 15 |
| MRHD | 2 g applied daily | Label §8.1 (page 5) |
| Application density | Approximately 2 mg/cm² (Study 1: face + chest + back) | Label §12.3 (page 7) |
| Re-evaluation timeline | If therapeutic results not noticed after 12 weeks, therapy should be re-evaluated | Label §2 (page 2) |

> **v8 addition**: Carbomer identity note — the two names may or may not be synonymous. This matters if a new formulation specifies one vs the other.

> **v8 addition**: 12-week re-evaluation timeline from §2. Any new formulation must show results within this window.

> **Demotion carried forward**: "Formulation route probably close to solved" — one specific vehicle proves solubility **can be** solved in one case, not that it is **generically** solved. See risk R01.

> **Known-fact gap carried forward**: Target pH not stated. The claim that pH simultaneously constrains solubility, gel structure, and preservative efficacy is an inference. Demoted to §2.4.

### 1.5 Irritation Profile — Physician-Assessed (Directly Sourced from Label §6.1, Table 1)
| Reaction | Mild | Moderate | Severe |
|---|---|---|---|
| Erythema | 66 (26.1%) | 33 (13.0%) | 1 (0.4%) |
| Scaling | 110 (43.5%) | 47 (18.6%) | 3 (1.2%) |
| Dryness | 113 (44.7%) | 43 (17.0%) | 2 (0.8%) |
| Burning/stinging | 72 (28.5%) | 36 (14.2%) | 9 (3.6%) |

- Source: Label §6.1, Table 1 (page 4). N=253 (subjects with ≥1 post-baseline evaluation; total enrolled N=258).
- Label §5.3 and §6.1 state: most reactions occurred in the first four weeks and usually lessened with continued use. ("Usually" is the label's own soft qualifier, not a statistical claim.)
- Severe burning/stinging: 3.6% (9/253). See risk R07.
- One-year open-label safety trial (N=551): pattern of adverse reactions similar to 12-week controlled study (Label §6.1, page 4).
- Label §5.3 (page 3): depending on severity, patients should use a moisturizer, reduce frequency, or discontinue.

### 1.5b Irritation Profile — Patient-Reported (Directly Sourced from Label §6.1, Table 2)

> **v4 error corrected (carried forward)**: v4 misread Table 2 by assigning the "Related* Adverse Reactions" total row (57/22.1% and 6/4.5%) to "Dry Skin" and shifting all subsequent rows down. Correct alignment verified against PDF page 4 text.

| Row | Differin Gel 0.3% (N=258) | Vehicle Gel (N=134) |
|---|---|---|
| **Related* Adverse Reactions (total)** | 57 (22.1%) | 6 (4.5%) |
| Dry Skin | 36 (14%) | 2 (1.5%) |
| Skin Discomfort | 15 (5.8%) | 0 (0%) |
| Desquamation | 4 (1.6%) | 0 (0%) |

- Source: Label §6.1, Table 2 (page 4). "Related*" = investigator-defined as Possibly, Probably, or Definitely Related.
- Additional adverse reactions <1%: acne flare, contact dermatitis, eyelid edema, conjunctivitis, erythema, pruritus, skin discoloration, rash, eczema (Label §6.1, page 4).

### 1.6 Post-Marketing Adverse Reactions (Directly Sourced from Label §6.2)
- Immune system: angioedema, face edema, lip swelling
- Skin: application site pain
- Label states: frequency cannot be reliably estimated; causal relationship cannot always be established (voluntary reporting from uncertain population size). Source: Label §6.2 (page 5).

### 1.7 UV Sensitivity & Environmental Exposure (Observational Only)
- Label §5.2 (page 3): exposure to sunlight, including sunlamps, should be minimized during use. Patients with high sun exposure or inherent sun sensitivity should exercise caution. Sunscreen and protective clothing recommended when exposure cannot be avoided.
- Label §5.3 (page 3): weather extremes (wind, cold) may also be irritating.
- These are label warnings directed at patients. The label does not state whether adapalene itself photodegrades.

> **Demotion carried forward**: "(patient-level photosensitivity)" is an interpretive classification not in the label. Whether adapalene photodegrades is also not stated. Both demoted to §2.5.

### 1.8 Concomitant-Product Constraints (Directly Sourced from Label)
- §5.3 (page 3): concomitant use of other potentially irritating topical products should be approached with caution. Specifically named: medicated or abrasive soaps and cleansers, soaps and cosmetics with strong drying effect, products with high concentrations of alcohol, astringents, spices, or lime.
- §17 point 3 (page 9): moisturizers may be used; products containing alpha hydroxy or glycolic acids should be avoided.
- §5.3 (page 3): wax depilation should be avoided on treated skin.
- §17 point 4 (page 9): should not be applied to cuts, abrasions, eczematous, or sunburned skin.

### 1.9 Pharmacology & PK (Observational Only)
- Label §12.1 (page 7): adapalene binds to specific retinoic acid nuclear receptors but does not bind to cytosolic receptor protein. Modulates cellular differentiation, keratinization, and inflammatory processes. Label states: significance for acne treatment mechanism is unknown.
- Label §12.2 (page 7): clinical pharmacodynamic studies have not been conducted for Differin Gel.
- **Study 1** (Label §12.3, pages 7–8): 16 acne subjects, 2 g/day applied to face + chest + back (~2 mg/cm²), once daily for 10 days. 15/16 had quantifiable levels (LOQ = 0.1 ng/mL). Mean Cmax = 0.553 ± 0.466 ng/mL (Day 10). Mean AUC₀₋₂₄ₕ = 8.37 ± 8.46 ng·h/mL (15/16 subjects, Day 10). Terminal t½ = 7–51 h (mean 17.2 ± 10.2 h, 15/16 subjects). "Adapalene was rapidly cleared from plasma and was not detected 72 hours after the last application for all but one subject." Exposure of potential circulating metabolites was not measured. Excretion appears to be primarily biliary.
- **Study 2** (Label §12.3, pages 7–8): 78 subjects with moderate to moderately severe acne; Differin 0.3% or Adapalene 0.1% applied to face (± trunk), once daily for 12 weeks; average daily usage 1 g/day. 209 plasma samples analyzed. Adapalene concentrations below LOD (0.15 ng/mL) in all samples except three. The three samples had traces above LOD but below LOQ (0.25 ng/mL) — i.e., between 0.15 and 0.25 ng/mL. Sample 1: male, 0.3% gel, face + trunk for 8 weeks then face only, Week 12. Samples 2–3: female, 0.1% gel, face only, Weeks 2 and 12.
- Contraindication: known hypersensitivity to adapalene or any excipient (§4, page 3).

> **v8 correction**: v7 said "cleared from plasma within 72 h" in the status note, dropping the "all but one subject" qualifier. Now quoted verbatim. v7 also said "three traces below LOQ" which was ambiguous; now says "above LOD but below LOQ (between 0.15 and 0.25 ng/mL)."

> **Demotion carried forward**: "Confirms minimal systemic absorption at typical usage" overstates what below-LOQ means. A lower LOQ might detect more traces. Demoted to §2.5.

### 1.10 Overdosage (Directly Sourced from Label §10)
- "Chronic ingestion of the drug may lead to the same side effects as those associated with excessive oral intake of vitamin A." Source: Label §10 (page 6).

> **v8 correction**: v7 note said "This classifies adapalene as a retinoid with vitamin A-class systemic toxicity upon oral exposure." This conflated two separate label statements: (a) "retinoid" comes from §1 Highlights (page 1), not §10; (b) §10 says chronic ingestion leads to vitamin A-type side effects. These are two separate facts. The retinoid classification is in §1.1 above; §10 addresses only oral overdosage toxicity.

### 1.11 Teratogenicity (Directly Sourced from Label §8.1, §13.1)
- **Human data**: insufficient to establish drug-associated risk of major birth defects, miscarriage, or other adverse outcomes (§8.1, page 5).
- **Oral adapalene in rats**: no malformations at 0.15–5.0 mg/kg/day (up to 8× MRHD based on mg/m²). Malformations at ≥25 mg/kg/day (40× MRHD): cleft palate, microphthalmia, encephalocele, skeletal abnormalities (§8.1, page 5).
- **Oral adapalene in rabbits**: malformations at ≥25 mg/kg/day (81× MRHD): umbilical hernia, exophthalmos, kidney and skeletal abnormalities (§8.1, page 5).
- **Dermal adapalene in rats and rabbits**: up to 6.0 mg/kg/day (9.7× and 19.5× MRHD respectively) — no fetotoxicity; only minimal increases in supernumerary ribs in both species; delayed ossification in rabbits (§8.1, page 5).
- **Lactation**: adapalene present in rat milk with oral administration; no human data. Label advises use on smallest area for shortest duration while breastfeeding (§8.2, page 6).

### 1.12 Clinical Efficacy Benchmark (Directly Sourced from Label §14, Table 3)
| Endpoint | Differin 0.3% (N=258) | Adapalene 0.1% (N=261) | Vehicle (N=134) |
|---|---|---|---|
| IGA Success ("Clear"/"Almost Clear") | 53 (21%) | 41 (16%) | 12 (9%) |
| Inflammatory lesions: baseline → mean absolute (%) reduction | 27.7 → 14.4 (51.6%) | 28.1 → 13.9 (49.7%) | 27.2 → 11.2 (40.7%) |
| Non-inflammatory lesions: baseline → mean absolute (%) reduction | 39.4 → 16.3 (39.7%) | 41.0 → 15.2 (35.2%) | 40.0 → 10.3 (27.2%) |
| Total lesions: baseline → mean absolute (%) reduction | 67.1 → 30.6 (45.3%) | 69.1 → 29.0 (41.8%) | 67.2 → 21.4 (33.7%) |

- 12-week, multi-center, controlled trial; N=653 total; ages 12–52; mild to moderate acne vulgaris (§14, pages 8–9).
- All female subjects of child-bearing potential required negative urine pregnancy test and highly effective contraception. Pregnant, nursing, or planning-to-become-pregnant females excluded.
- Demographics: Caucasian 72%, Hispanic 12%, African-American 10%, Asian 3%, other 2%; male 49.5%, female 50.5%.

### 1.13 Carcinogenicity & Genotoxicity (Directly Sourced from Label §13.1)
- No carcinogenicity, genotoxicity, or impairment of fertility studies were conducted with DIFFERIN Gel itself (§13.1, page 8).
- **Topical mouse study**: adapalene at 0.4, 1.3, and 4.0 mg/kg/day (1.2, 3.9, and 12 mg/m²/day); highest dose = 3.2× MRHD. The label does not report a finding for this study — it reports only the rat finding below.
- **Oral rat study**: adapalene at 0.15, 0.5, and 1.5 mg/kg/day (0.9, 3.0, and 9.0 mg/m²/day); highest dose = 2.4× MRHD. Increased incidence of benign and malignant pheochromocytomas in adrenal medulla of male rats.
- Adapalene not mutagenic/genotoxic in vitro (Ames, CHO, mouse lymphoma TK) or in vivo (mouse micronucleus).
- No impairment of fertility at 20 mg/kg/day (32× MRHD) in rats (F₀ males and females; F₁ offspring).

> **v8 correction**: v7 said "no relevant finding reported" for the mouse carcinogenicity study. The label simply does not report a finding for mice — it only reports the rat pheochromocytoma finding. Absence of a reported finding is not the same as a reported negative finding. This distinction matters for safety assessment.

---

## 2. Inferred But Not Yet Confirmed (All Interpretive Conclusions Live Here)

> Every statement below is an interpretation, judgment, or strategy conclusion — not a directly sourced fact. None can be treated as a formulation-design input without verification. Each maps to a risk row in `formulation_risk_table.csv`.

### 2.1 Structural Interpretations
| Inference | Basis | Confidence | Risk Row | What Would Confirm |
|---|---|---|---|---|
| The adamantyl cage is the primary contributor to the high logP | Large saturated hydrocarbon with no heteroatoms; general medicinal chemistry knowledge | Moderate (not from local files) | R02 | Fragment-based logP calculation or measured logP of adamantane alone |
| Naphthoic acid –COOH is the sole ionizable group | SMILES shows only one –COOH; H-bond donor count = 1 is consistent (but H-bond donors include non-ionizable groups like –OH, –NH) | Moderate–High | R03 | Measured pKa or ionization curve |
| pKa ≈ 4–5 | General chemistry of aromatic carboxylic acids; no measured value in local files | Moderate | R03, R05 | Measured pKa |
| Methoxy group is "not a formulation lever" | Fixed structural feature; –OCH₃ is not ionizable and has limited solubilizing capacity | Moderate (general chemistry, not from local files) | — | Solubility study comparing methoxy vs hydroxyl analog |

> **v8 correction**: v7 listed "Adamantyl cage 'cannot be modified' for formulation purposes" as an inference. This is a tautology (modifying the API structure creates a different compound by definition) and has been removed. The useful inference is about logP contribution, now stated above.

### 2.2 Solubility & Partitioning Interpretations
| Inference | Basis | Confidence | Risk Row | What Would Confirm |
|---|---|---|---|---|
| Aqueous solubility < 1 µg/mL | "Practically insoluble" (label) + logP 7.7 (PubChem); no numerical value in local files | Moderate | R04 | Measured equilibrium solubility in water at 25°C |
| LogD at pH 5.5–7 ≈ 5–6 | LogP 7.7 minus ~2 units for single-acid ionization at pH > pKa; neither logD nor pKa measured | Low–Moderate | R05 | Measured logD at pH 5.5 and 7.0 |
| Solubilization must target the –COOH or use non-aqueous approaches | Only one polar/ionizable anchor on a large hydrophobic scaffold | Moderate (formulation strategy inference) | R01–R04 | Solubility studies across pH range and vehicle types |
| 0.3% may be near solubility ceiling in Differin vehicle | Only 0.1% and 0.3% marketed; no higher strength exists | Low | R04 | Solubility limit measurement in Differin vehicle |

### 2.3 Irritation Interpretations
| Inference | Basis | Confidence | Risk Row | What Would Confirm |
|---|---|---|---|---|
| Irritation is primarily drug-driven relative to the Differin vehicle | Table 2: Differin total "Related" = 22.1% vs vehicle total = 4.5% | Moderate–High | R08 | Comparative irritation data across different vehicles at same 0.3% |
| **Scope limitation**: this conclusion applies only to the one vehicle pair tested | Only one vehicle pair in the trial | High (logically necessary) | R08 | Multi-vehicle comparative study |
| Vehicle must mitigate, not worsen, irritation | Formulation strategy inference from §6.1 data | High (as strategy) | R06, R09 | Vehicle irritation screening data |
| Concomitant-product constraints limit the excipient palette for solubilization | §5.3 prohibits alcohol, astringents, drying agents; §17 prohibits AHA/glycolic acids; solubilizers for practically insoluble APIs tend to be irritating (general formulation knowledge) | Moderate | R09 | Excipient irritation screening + solubility screening overlap |

### 2.4 Excipient Role & pH Interpretations
| Inference | Basis | Confidence | Risk Row | What Would Confirm |
|---|---|---|---|---|
| Carbomer 940 = gelling agent | Standard pharmaceutical role; label does not state excipient functions | High (general pharma knowledge) | R12 | Manufacturer specification or formulation textbook |
| Poloxamer 124 = surfactant/solubilizer | Standard role; practically insoluble API requires solubilizer | High (general pharma knowledge) | R13 | Solubility study with/without poloxamer 124 |
| Propylene glycol = cosolvent + humectant | Standard role in topical gels | High (general pharma knowledge) | R13 | Solubility study with/without PG |
| Edetate disodium = chelating agent / preservative booster | Standard role in topical formulations | High (general pharma knowledge) | R12 | Manufacturer specification |
| pH simultaneously constrains solubility, gel structure, and preservative efficacy | Carbomer gels require neutralization for viscosity (general knowledge); methylparaben has pH-dependent efficacy (general knowledge); adapalene ionization depends on pH (from pKa inference) | Moderate (three separate general-knowledge claims chained together) | R03, R12 | pH-solubility profile + pH-viscosity profile + pH-preservative efficacy data |

> **v8 note**: Every "High confidence" entry in this table is based on general pharmaceutical knowledge, not local files. The label lists excipients but never states their functions. "High confidence" means the role assignment is standard practice, not that it is locally sourced.

### 2.5 Stability, PK & Safety Interpretations
| Inference | Basis | Confidence | Risk Row | What Would Confirm |
|---|---|---|---|---|
| UV warning is primarily patient-level (photosensitivity), not stability-level (photodegradation) | Label §5.2 warns about sunlight exposure to skin; does not mention product degradation | Moderate | R10, R11 | ICH Q1B photostability study |
| Adapalene may be photolabile | Retinoids as a class tend to photodegrade (general knowledge); label has UV warning | Low | R11 | ICH Q1B photostability study |
| Systemic absorption is minimal at typical usage | Study 2: 3/209 traces between LOD and LOQ at 1 g/day | Moderate | R15 | PK study with lower LOQ |
| Dermal teratogenicity safety margin is "sufficient" | Dermal NOAEL 9.7–19.5× MRHD vs oral teratogenic dose 40–81× MRHD | Moderate (judgment, not stated in label) | R18 | Human pregnancy registry data; PK at higher application areas |
| Freeze-thaw cycling disrupts gel structure | "Protect from freezing" in label; carbomer gels are known to be freeze-sensitive (general knowledge) | High (as general knowledge) | R16 | Freeze-thaw cycling study with viscosity/appearance endpoints |
| Polymorphism may affect dissolution | No polymorph data in local files; complex crystal behavior possible (general knowledge) | Unknown | R14 | XRPD, DSC, polymorph screening |
| Mouse carcinogenicity study was negative | Label reports rat pheochromocytoma finding but does not report a mouse finding | Low (inference from silence) | — | Access to full study report |

---

## 3. Formulation-Relevant Property Priorities

> **v8 correction**: v7 ranked by "downstream impact" but conflated problem severity with degree of unknownness. v8 separates these: Priority reflects how much the unknown blocks formulation design progress, not how severe the problem would be if it materialized.

| Priority | Property | What is known | What is unknown (and why it blocks progress) | Risk Rows |
|---|---|---|---|---|
| 1 | pKa | Nothing — no measured or label-stated value | Without pKa, cannot calculate ionization fraction at any pH → cannot design pH-solubility strategy, cannot estimate logD, cannot model skin flux. **This single missing number blocks three downstream calculations.** | R03, R05 |
| 2 | Numerical aqueous solubility | Qualitative: "practically insoluble" | Without a number, cannot determine whether a proposed vehicle can hold 3 mg/g, cannot calculate supersaturation ratio, cannot size the solubilization challenge quantitatively | R01, R04 |
| 3 | LogD at skin-relevant pH | Nothing — logP 7.7 is neutral form only | Without logD, permeation modeling is guesswork; release-rate targets cannot be set | R05 |
| 4 | Vehicle pH | Not stated in label | Cannot reverse-engineer the Differin formulation; cannot assess whether a new pH would collapse gel, kill preservative, or precipitate API | R12 |
| 5 | Irritation mechanism (drug vs vehicle vs interaction) | One vehicle comparison (Table 2) | Cannot predict whether a different vehicle at 0.3% would produce better or worse irritation rates | R06, R07, R08, R09 |
| 6 | Photostability | Label has UV warning; no photodegradation data | Cannot finalize packaging or shelf-life specifications | R10, R11 |
| 7 | Polymorph landscape | Nothing | Cannot assess risk of form conversion in new vehicle | R14 |
| 8 | Freeze sensitivity mechanism | "Protect from freezing" stated | Cannot predict whether a non-carbomer vehicle would also be freeze-sensitive | R16 |

> **Removed (carried forward)**: TPSA (46.5 Å²). Veber's 75 Å² oral-absorption threshold is a category error for topical formulation.

---

## 4. Error Records (All Versions)

### 4a. Original Draft Errors
| Claim | Status | Reason | Risk Row |
|---|---|---|---|
| "Probably not very water soluble" | Understated | Label says practically insoluble — hard gate | R01 |
| "Skin-friendly by default" | Contradicted | Label §6.1 shows 26–45% mild irritation | R06 |
| "Formulation route close to solved" | Misleading overgeneralization | One vehicle proves solvable in one case | R01 |
| "All issues solved by same hydrophobicity trend" | False overgeneralization | Three separate risk domains | R01–R11 |

### 4b. v4 Errors (Table 2 Misalignment)
| v4 Error | Correction | Evidence |
|---|---|---|
| Assigned "Related* total" row to "Dry Skin" | "Related* total" is a summary row; Dry Skin = 36 (14%) / Vehicle 2 (1.5%) | PDF page 4 text alignment |
| Differin Dry Skin = 22.1% (57) | 22.1% (57) is the total "Related" row, not Dry Skin | Corrected alignment |
| Vehicle Dry Skin = 3.0% (4) | Vehicle Dry Skin = 1.5% (2) | Corrected alignment |
| Vehicle Skin Discomfort = 4.5% (6) | Vehicle Skin Discomfort = 0% (0) | Corrected alignment |
| Vehicle Desquamation = 1.5% (2) | Vehicle Desquamation = 0% (0) | Corrected alignment |

### 4c. v5 Errors (Tempting Claims in §1)
| v5 Claim | Why not a directly sourced fact | Now lives in |
|---|---|---|
| "This confirms irritation is overwhelmingly drug-driven" | One vehicle comparison; "overwhelmingly" is unsupported | §2.3 — scope-limited |
| "Vehicle-only rates are very low" | "Very low" is judgment; numbers are 0–1.5% | §1.5b (numbers only) |
| "Vehicle must mitigate not worsen irritation" | Strategy conclusion | §2.3 |
| "(patient-level photosensitivity)" | Label doesn't classify UV warning type | §2.5 |
| "Confirms minimal systemic absorption" | Below-LOQ ≠ confirmed minimal | §2.5 |
| "pH simultaneously constrains..." | Cross-constraint inference | §2.4 |
| "Hydrophobic bulk cannot be modified" | Synthetic chemistry claim | Removed (tautology) |
| "Solubilization must target the acid" | Strategy inference | §2.2 |

### 4d. v7 Errors (Corrected in v8)
| v7 Error | What was wrong | Correction |
|---|---|---|
| §1.3: "C₁₀H₁₅ tricyclic hydrocarbon" | Fragment formula not in local files; conflates substituent (C₁₀H₁₅) with parent cage (C₁₀H₁₆) | Describe SMILES fragment without asserting formula |
| §1.3: XLogP 7.7 in adamantyl row | Whole-molecule logP placed in cage row implies cage has that logP | Moved to §1.2 with "whole-molecule" label; cage row now says logP cannot be decomposed from local files |
| §1.9 status note: "cleared from plasma within 72 h" | Dropped "all but one subject" qualifier | Now quotes label verbatim |
| §1.9: "three traces below LOQ" | Ambiguous — could mean below LOD too | Now says "above LOD but below LOQ (between 0.15 and 0.25 ng/mL)" |
| §1.10 note: "classifies adapalene as a retinoid" | Conflated §1 Highlights (retinoid) with §10 (vitamin A toxicity) | Separated: retinoid in §1.1; §10 addresses only overdosage |
| §1.13: "no relevant finding reported" for mouse study | Inference from silence, not a reported negative | Now says "label does not report a finding for this study" |
| §2.1: "cage cannot be modified" | Tautology (modifying API = different compound by definition) | Replaced with logP contribution inference |
| §1.4: "Carbomer 940 (carbomer homopolymer type C)" | Equated two names without evidence of identity | Now noted as separate names from different label sections; equivalence not confirmed |
| Status note: "v6 was already well-structured" | Praised prior version instead of treating as flawed | Removed |
| §3 priority ranking | Conflated problem severity with degree of unknownness | Restructured: priority = how much the unknown blocks design progress |
| R02: "Adamantyl cage dominates logP" | Not stated in local files | Moved to §2.1 as inference with "Moderate (not from local files)" confidence |
| Missing: 12-week re-evaluation timeline | Label §2 states this directly; formulation-relevant | Added to §1.4 |
| Missing: mouse carcinogenicity silence vs negative | v7 treated silence as negative finding | Added to §2.5 as low-confidence inference |
