<!--
narrative.md — the prose half of the audit report.

Copy this into the audit folder and fill it in. `build_report.py` reads the `## key`
sections below and renders them into the LaTeX document; everything else in the report
is generated from findings.json, so the counts can never drift from the narrative.

Supported markdown: paragraphs, `-` bullets, **bold**, *italic*, `code`.
Write in the language the user is speaking. Leave nothing as a placeholder — an
unwritten section renders as a visible "[not written]" marker in the PDF, on purpose.
-->

## verdict

<!-- One page maximum. Written for someone who will read nothing else and may have to
     decide whether to ship. Answer, in this order:
     - Would this repository have failed in front of its users as it stood? Yes/no, why.
     - Does it now? Yes/no, what remains.
     - The single most serious finding, in two sentences.
     - A one-line recommendation: ready / ready with conditions (name them) / not ready
       (name the blockers). -->

## scope

<!-- What was audited and what was not, explicitly. Which phases ran. Which lenses were
     applied. Which tools ran, and which were unavailable in the environment.

     Then the paragraph that makes the audit credible: HOW THE SOFTWARE WAS EXERCISED.
     What was run, with what inputs, against what. Findings that came from running the
     thing carry weight that findings from reading it do not. -->

- **Lenses applied:**
- **Tools run:**
- **Tools unavailable:**
- **How it was exercised:**

## system

<!-- A short technical portrait, two or three paragraphs: architecture, languages,
     dependencies, entry points, and the state of the test suite and CI at Phase 0.
     A reader six months from now needs this to interpret everything else. -->

## gate

<!-- Optional. Prose that belongs above the before/after gate table: whether any gate
     configuration changed and why, the flakiness result, the clean-room build result,
     and the coverage delta on the lines this audit changed.

     If any gate stage was made to pass by weakening it, say so here, plainly. -->

## recommendations

<!-- Ordered by value, not by severity. Prevention over repair: the gate that would have
     caught this class, the test that should exist, the abstraction that makes the defect
     family impossible rather than merely absent today.

     Each recommendation names the defect family it closes. -->

1.
2.
3.
