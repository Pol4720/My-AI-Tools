# Field standards and statistical tripwires

Reviewers check the paper against the conventions of their field, and many of those conventions are
written down. Finding the applicable standard and holding the paper to it converts vague unease into
specific, actionable findings — and it is what separates an audit from an opinion.

## Identifying the applicable standard

Do not guess from a list. Determine the field precisely in Phase 1, then search:

```
"<subfield>" reporting guideline checklist
"<journal name>" author guidelines statistics
"<study type>" reporting standard EQUATOR
```

The EQUATOR Network indexes reporting guidelines across health and life sciences and is the fastest route
when the paper is biomedical. For other fields, the target journal's author guidelines and the flagship
venue's checklist are the authority.

Then read the checklist and walk the paper against it item by item. Items the paper fails are findings.

## Standards that come up often

Treat this as a starting index, not a closed list. Always confirm the current version by search — these
get revised, and citing a superseded version is itself a finding.

| Study type | Standard |
|---|---|
| Randomised trial | CONSORT |
| Observational epidemiology | STROBE |
| Systematic review / meta-analysis | PRISMA |
| Diagnostic or prognostic prediction model | TRIPOD (TRIPOD+AI for machine-learning models) |
| Clinical AI trial | CONSORT-AI / SPIRIT-AI |
| Animal research | ARRIVE |
| Qualitative research | COREQ / SRQR |
| Economic evaluation | CHEERS |
| Modelling study, infectious disease | EPIFORGE |
| Life-science data and code transparency | MDAR framework |

For machine learning specifically, the venue matters more than a single universal standard. Major
conferences require a reproducibility or ethics checklist; find the current one for the target venue and
apply it. The recurring expectations are: compute reported, hyperparameter search described, multiple seeds
with variance, held-out data touched once, dataset provenance and licensing stated, limitations meaningful.

## Statistical tripwires by field

These are the failures that referees in each area are trained to spot. Check whichever apply.

### Machine learning

- Single-seed results, or means with no spread across seeds.
- Baselines run at default settings while the proposed method is tuned. The comparison must be effort-matched.
- Test-set reuse across the paper's development — the reported number is the best of many looks.
- Benchmark contamination: evaluation data present in pretraining corpora. For anything using a pretrained
  model, this must be addressed explicitly.
- Improvements within noise, presented as improvements. If the gap is smaller than the seed variance, it
  is not a result.
- Compute-matched comparison missing: a method that wins because it used more compute has not won.
- Ablations that remove a component and retune nothing, so the drop measures retuning rather than the component.
- Metric choice hiding the failure mode: accuracy on imbalanced data, BLEU where meaning matters, AUC where
  calibration matters.

### Statistics and econometrics

- Multiple comparisons uncorrected, with the reported subset being the significant one.
- p-values near 0.05 reported as decisive, or the dichotomy applied without an effect size.
- Model selection and inference on the same data, with post-selection uncertainty ignored.
- Clustered or repeated-measures data analysed as independent — this understates standard errors, often severely.
- Instrument validity asserted rather than argued; weak-instrument diagnostics absent.
- Parallel trends, common support, or exclusion restrictions assumed without evidence.
- Sensitivity to specification not shown, when many specifications were plausible.

### Epidemiology and public health

- Case definitions, ascertainment and reporting completeness left implicit.
- Denominators that do not match the numerator's population.
- Prevalence and incidence conflated, including in the observation model of a mechanistic study.
- Confounders adjusted for using a list rather than a stated causal structure; mediators or colliders
  included as if they were confounders.
- Ecological inference from aggregate to individual.
- Parameters imported from a different population without a transferability argument.

### Computational and mechanistic modelling

- Parameters fitted to the same data used to validate.
- Structural uncertainty ignored — only parametric uncertainty propagated, when the choice of model
  structure dominates.
- Identifiability never examined: parameters reported with intervals when the data cannot inform them.
  Profile likelihoods or posterior-versus-prior comparison settle this.
- Sensitivity analysis that varies one parameter at a time in a nonlinear system.
- Initial conditions or burn-in chosen to produce the desired behaviour.
- Numerical error unexamined: tolerance, step size, and stability of the integrator affecting results.

### Experimental sciences

- Sample size with no power justification.
- Technical replicates counted as biological replicates, inflating n.
- Batch effects confounded with the condition of interest.
- Exclusion criteria defined after seeing the data.
- Blinding absent where it was feasible, and not discussed.

## Using a standard well

Two failure modes to avoid.

**Mechanical box-ticking.** A paper can satisfy every checklist item and still be wrong. The standard is
a floor, not the audit.

**Standard-shopping.** Do not apply a guideline the paper's design does not fit merely to generate findings.
If the study type is ambiguous, say which standard you applied and why — and if the paper would fail under
one reading and pass under another, that ambiguity is itself worth reporting, because a referee will
resolve it in whichever direction is least convenient.
