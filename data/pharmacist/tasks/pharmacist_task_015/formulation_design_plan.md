# Revised API-X Topical Gel Formulation Design Plan

## Screening Basis
This plan screens the three candidate routes using local API information and risk flags first. Benchmark observations are brought in only where they are worth imitating in round one. Two borrowing points are worth imitating: (a) the sequencing principle ("first solve uniformity, then balance gel base and pH") — aligns with Risk #1 and directly supports the decision to defer Route C [Benchmark + Risk #1]; (b) ethanol and PG as common cosolvent candidates — both are named in the API profile with known solubility data [Benchmark + API]. The Benchmark comparator logic ("alternative routes may all appear in early route notes") is not worth imitating in round one because the Benchmark itself says "their relative value depends on the current project goal and the unresolved risks" — and the current unresolved risk points to solubilization first, making the alternative-gel-base comparator less valuable in round one; furthermore, the Routes file explicitly cautions against introducing a different base too early [Benchmark + Routes + Risk]. Specific product-level borrowing (e.g., exact solvent ratios, film-forming timing) is not worth imitating in round one because the Benchmark file itself says applicability depends on project stage and information completeness [Benchmark].

---

## A. Known Facts

All items below are stated directly in the source files. No inference or extrapolation is added.

**From the API profile:**
- API code name: API-X [API]
- Target delivery site: superficial skin layers and shallow dermis [API]
- Appearance: off-white powder [API]
- Water solubility: very low, about < 0.05 mg/mL [API]
- Solubility in ethanol: moderate [API]
- Solubility in propylene glycol: relatively good [API]
- Estimated logP: 3.1 [API]
- pKa: weakly basic, about 8.4 [API]
- Known issues: precipitation risk after standing; high ethanol ratio raises irritation concerns [API]
- Initial constraints: gel dosage form; system should not be too irritating; next step should compare 2–3 candidate formulation routes [API]
- Practical tension: strong neutralization or an aggressive solvent push may improve one part of the system while making pH control, feel, or precipitation behavior harder to manage together [API]

**From the candidate routes file:**
- Three candidate directions are provided: (1) carbomer-based baseline gel, (2) lower-irritation co-solvent route, (3) alternative-gel-base route [Routes]
- Direction 1: gel formation is straightforward, but the balance between cosolubilization and precipitation still needs to be judged separately; pH handling and gel-formation behavior will need to be watched separately [Routes]
- Direction 2: this may better fit the preference for a milder system, but that does not automatically mean it solves API uniformity; if the solvent push is too conservative, precipitation or poor uniformity may reappear before the screen even reaches stability testing [Routes]
- Direction 3: it can be kept as a later comparison idea, but the current information is not enough to decide its priority directly; it may be attractive if carbomer handling becomes limiting, but introducing a different base too early may blur whether the real first-round issue is solubilization or polymer choice [Routes]
- The Routes file intentionally does not provide a ready-made ranking; relative priority must be judged by combining API properties, benchmark borrowing points, and project preferences [Routes]

**From the risk flags:**
- Risk #1: extremely low water solubility makes precipitation risk the core first-round problem [Risk]
- Risk #2: higher ethanol ratio improves solubility but increases irritation risk [Risk]
- Risk #3: weakly basic pKa means pH adjustment must account for both gel-formation conditions and API stability [Risk]
- Risk #4: long-term stability, target release rate, and the need for film formation are all still undecided [Risk]
- Risk #5: the current priority is to decide what must be judged first and what can be judged later [Risk]
- Risk #6: too many route changes at once make it hard to tell whether the first-round problem came from solvent choice, gel base, or pH handling [Risk]

**From the benchmark notes:**
- Common practices in existing topical gel cases:
  - first use a cosolvent system to solve API uniformity
  - then balance the gel base and the pH window
  - typical concerns include appearance, viscosity, precipitation, release, and stability
  - simple baseline gels still appear in some early semisolid screens even when later development may become more complex [Benchmark]
- For relatively hydrophobic APIs:
  - ethanol and propylene glycol are both common cosolvent candidates
  - if local irritation is a real constraint, the solvent system needs additional tradeoff analysis
  - a solvent-rich route may improve clarity or initial dissolution yet still be unattractive if it worsens irritation or later precipitation after standing [Benchmark]
- Systems that include a film-forming idea:
  - may provide extra functionality in some cases
  - but whether to introduce that now depends on the project stage and how complete the known information is
  - this layer is not always introduced at the same stage across different projects [Benchmark]
- Comparator logic:
  - different teams retain different kinds of comparator routes
  - baseline, milder, or alternative routes may all appear in early route notes, but their relative value depends on the current project goal and the unresolved risks [Benchmark]

---

## B. Open Information Gaps

All items below are explicitly flagged as undecided or unconfirmed in the source files. No gap is invented.

- Long-term stability: not yet confirmed [API]
- Exact dose requirement: not yet confirmed [API]
- Target release rate: not yet confirmed [API]
- Whether a film-forming function is needed: undecided [API] [Risk #4]
- How narrow or wide the acceptable pH window really is once the gel base is fixed: not yet confirmed [API]
- The exact ethanol:PG ratio that balances cosolubilization against precipitation in a carbomer gel: the Routes file says this "needs to be judged separately" and does not specify a ratio [Routes]
- The specific polymer for the alternative-gel-base route: the Routes file only says "alternative gel base" and does not name a specific polymer [Routes]
- Relative priority of the three candidate directions: the Routes file intentionally does not provide a ranking and says this must be judged by combining API properties, benchmark borrowing points, and project preferences [Routes]

---

## C. Provisional Assumptions

All items below are decisions or working hypotheses made for this design round. Each is traceable to the source reasoning that supports it, but none is a confirmed fact.

1. **Precipitation is the primary screening criterion for round one.** Reasoning: Risk #1 states precipitation is the core first-round problem; Risk #5 says decide what must be judged first. Mildness and alternative gel bases are secondary or deferred. [Risk #1 + Risk #5]

2. **Two routes active in round one (baseline + backup), one route deferred.** Reasoning: the API profile says compare 2–3 routes — two active routes is within range [API]; the Routes file says Route C "can be kept as a later comparison idea" and "current information is not enough to decide its priority directly" [Routes]; Risk #5 says decide what must be judged first (precipitation/solubilization) and what can be judged later (gel-base choice) [Risk]. [API + Routes + Risk]

3. **Route A (carbomer baseline) is the baseline, not Route B (lower-irritation).** Reasoning: the Routes file says Direction 2's conservative solvent push may fail on precipitation — the very problem flagged as core. Treating the milder route as primary would risk failing on the core problem first. Direction 1 is the simplest standard approach and directly tests precipitation. [Routes + Risk #1 + Risk #2]

4. **Route B (lower-irritation co-solvent) is the backup, testing mildness as a secondary constraint.** Reasoning: it fits the project constraint on mildness (API: "system should not be too irritating") but the Routes file warns it does not automatically solve API uniformity. It is worth testing, but not as the primary driver. [API + Routes + Risk #2]

5. **Route C (alternative gel base) is deferred, not active in round one.** Reasoning: the Routes file explicitly says (a) "current information is not enough to decide its priority directly" and (b) "introducing a different base too early may blur whether the real first-round issue is solubilization or polymer choice" [Routes]; the core first-round problem is precipitation (solubilization) [Risk #1]; Risk #5 says decide what must be judged first (solubilization) and what can be judged later (gel-base choice) [Risk]; the Benchmark comparator logic says "their relative value depends on the current project goal and the unresolved risks" — the current unresolved risk points to solubilization first, making the alternative-gel-base comparator less valuable in round one [Benchmark + Risk]. Route C may be considered later if carbomer handling becomes limiting, per the Routes note ("it may be attractive if carbomer handling becomes limiting") [Routes]. Note: C's solvent strategy is not specified by the Routes file, so this plan cannot assume C addresses precipitation the same way as A or differently from A — this is another reason the Routes file says "current information is not enough to decide its priority directly." [Routes + Risk + Benchmark]

6. **Film-forming is not a candidate route in this round.** Reasoning: the Routes file provides only three directions (no direction 4); the API profile and Risk #4 say whether film-forming is needed is undecided; the Benchmark file says whether to introduce it depends on project stage and information completeness. It is an open gap, not a route. [Routes + API + Risk #4 + Benchmark]

7. **The ethanol:PG ratio in each route is not specified in this plan.** Reasoning: no source file prescribes a ratio; the Routes file says the balance needs to be judged separately. Specifying a ratio here would be an invention detached from the inputs. The ratio is set during formulation, guided by the directional tradeoff described in the API profile and Risk #2. [Routes + API + Risk #2]

8. **Route B's solvent strategy is inferred from the route name and API solubility data, not stated by the Routes file.** The Routes file calls Direction 2 "a lower-irritation co-solvent route" and warns "if the solvent push is too conservative, precipitation or poor uniformity may reappear." It does not specify the solvent composition. The inference that B uses a lower ethanol fraction and relies more on PG comes from combining the route name ("lower-irritation") with the API solubility data (PG solubility relatively good, ethanol solubility moderate) and Risk #2 (higher ethanol improves solubility but increases irritation). This inference is provisional; the actual solvent composition is set during formulation. No cosolvent beyond ethanol and PG is named in any source file. [Routes + API + Risk #2]

---

## D. Candidate Routes

### Route A: Carbomer-based baseline gel — Baseline
- Source description: "a carbomer-based baseline gel route" [Routes]
- Source notes: gel formation is straightforward; cosolubilization-precipitation balance needs judging separately; pH handling and gel-formation behavior need watching separately [Routes]
- Solvent strategy: ethanol and PG as cosolvents (both named in API profile with solubility data); exact ratio not specified by any source, to be set during formulation [API + Routes]
- Gel base: carbomer [Routes]
- Round-one role: baseline (Provisional Assumption #3)
- Key evaluation: precipitation after standing, API uniformity [API + Risk #1]
- Secondary concern: pH handling and gel-formation behavior [Risk #3 + Routes]

### Route B: Lower-irritation co-solvent route — Backup
- Source description: "a lower-irritation co-solvent route" [Routes]
- Source notes: may better fit mildness preference, but does not automatically solve API uniformity; conservative solvent push may cause precipitation to reappear [Routes]
- Solvent strategy: inferred as lower ethanol fraction relative to Route A, relying more on PG (Provisional Assumption #8); the Routes file does not specify the solvent composition for Direction 2 — it only says "a lower-irritation co-solvent route" and warns about conservative solvent push. No cosolvent beyond ethanol and PG is named in any source file. [API + Routes + Risk #2]
- Gel base: carbomer (same as Route A) [Routes]
- Round-one role: backup (Provisional Assumption #4)
- Key evaluation: precipitation after standing, API uniformity (same primary endpoints as A) [API + Risk #1]
- Secondary readout: mildness/irritation [API + Risk #2]
- Source-stated risk: conservative solvent push may cause precipitation to reappear [Routes + Risk #1]

### Route C: Alternative-gel-base route — Deferred
- Source description: "an alternative-gel-base route" [Routes]
- Source notes: can be kept as a later comparison idea; current information not enough to decide priority; may blur whether first-round issue is solubilization or polymer choice; may be attractive if carbomer handling becomes limiting [Routes]
- Gel base: alternative (specific polymer not named in any source file) [Routes]
- Solvent strategy: not specified by the Routes file for this direction [Routes]
- Round-one role: deferred (Provisional Assumption #5)
- When to consider: the Routes file says "it may be attractive if carbomer handling becomes limiting" — this is the only activation condition stated by the source [Routes]
- Key evaluation when considered: gel-base/pH handling behavior, plus precipitation and uniformity [Risk #3 + Routes]

---

## E. First-Round Priority

1. Route A (baseline) — directly tests the core precipitation problem with the simplest standard approach
2. Route B (backup) — tests whether mildness can coexist with adequate solubilization
3. Route C (deferred) — not active in round one; to be considered later if carbomer handling becomes limiting (per Routes note)

---

## F. Readout Clarity

A and B use the same gel base (carbomer) but differ in solvent strategy. Risk #6 cautions that too many route changes at once make it hard to tell whether the problem came from solvent choice, gel base, or pH handling. By keeping A and B on the same gel base and deferring C, the first-round design limits the active variable to solvent strategy. This does not guarantee clean attribution — other confounding variables may exist — but it follows the direction given by Risk #6. [Risk #6]

---

## G. Fallback If Both Active Routes Fail On Precipitation

If Route A and Route B both fail on precipitation, the core problem is solubilization (Risk #1), not mildness or gel-base choice — because B (same gel base, different solvent ratio) also failed.

Per Risk #5, solubilization must be judged first before moving to gel-base questions. Per Risk #6, do not introduce additional variables (different gel base) until the solubilization question is resolved. Route C remains deferred per the Routes file ("can be kept as a later comparison idea"). [Risk #5 + Risk #6 + Routes]

No source file describes a specific fallback procedure. The only source-grounded guidance is the prioritization principle (Risk #5: judge first things first) and the variable-control principle (Risk #6: don't mix too many changes). What specific solvent adjustments or additional cosolvents to try would depend on new solubility data not available in the current source files. [Risk]