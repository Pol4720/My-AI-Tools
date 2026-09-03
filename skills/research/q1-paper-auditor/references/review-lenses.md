# Review lenses

One reading finds one class of problem. The mind that checks arithmetic is not the mind that notices a
missing baseline, and neither is the mind that spots an abstract overstating its own results. So read the
paper several times, each time as a different referee who cares about one thing and is faintly irritated
by everything else.

Run these in parallel with subagents when available. Give each lens the paper plus its brief below, and
tell it to return findings with severity, evidence and root cause. Then merge and deduplicate.

The lenses overlap slightly on purpose. When two independent lenses land on the same defect, that is strong
evidence it is real and not an artefact of how one reviewer happened to read.

---

## Lens 1 — The methodologist

*Cares about:* whether the study design can support the conclusion at all. Indifferent to prose.

The core question is not "did they do the analysis correctly" but "does this analysis answer this question".
A flawless computation on the wrong design is still worthless.

Hunt for:

- **Conclusion outrunning design.** Causal language on observational data. "Improves" from a correlational
  result. Generalisation from one dataset, one site, one seed.
- **The comparison that is missing.** Every paper claiming an improvement needs the right comparator.
  Ask what a sceptic would demand: an ablation, a simpler baseline, the obvious alternative method, a
  control group, the previous state of the art at its best-tuned rather than default settings.
- **Assumptions never stated.** Independence, stationarity, exchangeability, linearity, correct
  specification, missing-at-random, no interference between units. Find where each is required and check
  whether the paper says so. Unstated assumptions are where papers break.
- **Circularity.** Model selection on the test set. Features derived from the outcome. Hyperparameters
  tuned on the data used to report the result. A threshold chosen to make the result significant.
- **The units question.** Does the denominator mean what the paper needs it to mean? Per-patient vs
  per-sample, per-token vs per-sequence, per-household vs per-capita. Wrong denominators silently rescale
  every result downstream.
- **Scope creep between sections.** The introduction promises something broader than the methods deliver
  and the conclusion claims the broader thing back again.

## Lens 2 — The domain expert

*Cares about:* whether this is right, novel, and properly situated for people who work in this exact area.

This lens requires the web research from Phase 2. Do not run it from memory.

Hunt for:

- **Superseded comparisons.** Baselines that were current three years ago. Datasets the field has
  abandoned as saturated or contaminated. Metrics known to be misleading in this subfield.
- **Related work that misses the obvious.** The paper a referee will name in the first paragraph of their
  report. Search for it deliberately: the paper's own keywords plus "survey", plus the year, plus the
  competing method names.
- **Novelty that is not novel.** Check whether the contribution already exists under different terminology.
  Fields rename the same idea constantly.
- **Domain-specific implausibility.** Parameter values outside physical or biological range. Effect sizes
  that would be extraordinary if true. Rates that imply impossible totals. A number that a practitioner
  would immediately know is wrong.
- **Misapplied domain conventions.** Using a metric the way an adjacent field uses it, where this field
  means something else by the same word.
- **Citations that do not support the claim.** Fetch the load-bearing ones and check. This is common,
  serious, and easy to verify.

## Lens 3 — The statistician and reproducibility referee

*Cares about:* whether the numbers mean what the paper says, and whether anyone could get them again.

Hunt for:

- **Uncertainty missing or wrong.** Point estimates with no interval. Intervals with no stated method.
  Standard error where standard deviation is meant. Uncertainty that ignores the dominant source — often
  the one the authors could not quantify and therefore left out.
- **Multiplicity.** Many comparisons, no correction, and the reported ones are the significant ones.
  Count how many tests the analysis implies versus how many are reported.
- **Underpowered claims of no effect.** "No significant difference" reported as equivalence.
- **Seeds and runs.** For anything stochastic: how many runs, what varies across them, is the spread
  reported. A single seed is not a result.
- **Test-set discipline.** How many times was the test set touched? Is the reported number the best of
  several attempts?
- **Code that does not match the text.** Read the implementation. Check that the loss, the estimator, the
  update, the filter, the denominator are what the methods section describes. This is the highest-yield
  check in the entire audit and almost nobody does it.
- **Numbers that cannot be traced.** Anything in the prose with no path back to data, code output, or a
  citation is either a typo or a fabrication, and you cannot tell which without checking.
- **Determinism.** Fixed seeds, pinned versions, stated hardware where it matters. Could the authors
  themselves reproduce this next year?

## Lens 4 — The adversarial replicator

*Cares about:* breaking it. This lens assumes the result is an artefact and tries to prove it.

This is a different posture from Lens 3: not "is the statistic correct" but "what mundane explanation
would produce this result without the claimed mechanism".

Hunt for:

- **Leakage.** Between train and test, across time in a temporal split, across groups when units are
  correlated, through preprocessing fitted on everything.
- **The trivial explanation.** Would a constant predictor score this well? Does class imbalance explain
  the accuracy? Is the effect just regression to the mean, or a seasonal trend, or a change in measurement
  rather than in the thing measured?
- **Selection.** How did units enter the sample? Who dropped out, and would they have differed? Survivorship
  in any longitudinal or historical dataset.
- **Confounding the paper did not adjust for**, and — the subtler failure — variables it adjusted for that
  it should not have, such as a mediator or a collider.
- **Boundary behaviour.** What happens at the extremes of the parameter range, at zero, at threshold
  values? Results that hold only in a narrow interior are fragile.
- **Suspicious cleanliness.** Results too consistent, effects too round, curves too smooth, every ablation
  supporting the story. Real data is messier than this.

## Lens 5 — The editor

*Cares about:* whether this is publishable as a piece of writing, and whether the abstract is honest.

Hunt for:

- **Abstract–body divergence.** The abstract's numbers must appear in the body and match. Its claims must
  be the body's claims, no stronger. This diverges constantly, because the abstract is written first and
  revised last.
- **Title overclaiming.** The title promises what the paper does not deliver.
- **Structure fighting the argument.** Results that belong in methods, methods hidden in an appendix that
  the results depend on, a discussion that reintroduces results, conclusions containing new findings.
- **The limitations section as ritual.** Generic limitations that would apply to any paper, while the real
  ones — the ones this lens list has surfaced — go unmentioned. A limitations section that does not scare
  the authors slightly is not doing its job.
- **Unreadable density.** Sentences carrying three clauses of qualification. Notation introduced after use.
  Acronyms never expanded. Tables that require the caption to be decoded and captions that do not do it.
- **Figures that do not stand alone.** Missing axis labels, units, sample sizes, or a legend. Colour as the
  only channel distinguishing series. Log axes not labelled as such.
- **Reproducibility and ethics furniture.** Data availability, code availability, funding, competing
  interests, ethics approval, author contributions. Journals desk-reject for these, and a competing-interest
  statement that hides an obvious conflict is worse than none.

---

## Merging findings

After the lenses report:

1. **Deduplicate by root cause, not by symptom.** Three lenses reporting three inconsistent tables may be
   reporting one bug. Trace to the cause and merge.
2. **Promote by convergence.** A finding two independent lenses reached is more likely real; weight it up.
3. **Demote what you cannot evidence.** A suspicion with no file, line, or number behind it is not yet a
   finding. Either go verify it or drop it. Speculative findings pollute the report and waste the authors' time.
4. **Order by severity, then by blast radius.** Among equally severe findings, the one that invalidates
   most other results goes first, because fixing it may resolve the others.
