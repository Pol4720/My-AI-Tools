# LaTeX to zero

The target is 0 errors, 0 warnings, 0 overfull boxes, 0 underfull boxes, 0 undefined references, 0
undefined citations — in every language version.

This is reachable. Treat every diagnostic as a real defect with a cause, because it usually is: an overfull
box means something genuinely does not fit and will look wrong in print, and a missing reference means a
cross-reference is broken.

**Never silence a diagnostic to make it go away.** Raising `\hbadness` or wrapping everything in `\sloppy`
hides the message from you while leaving the bad typesetting in the PDF. The one legitimate use of a
tolerance change is a *local* one whose cause you have diagnosed and cannot fix otherwise — a bibliography
in a narrow measure, for instance — and it should carry a comment saying why.

Use `scripts/build_paper.py`, which handles engine detection, pass counts and log parsing.

---

## Getting a correct build

LaTeX needs multiple passes and the count depends on what the document uses.

- Cross-references and citations need at least two passes; three after the bibliography changes.
- `bibtex` runs on the `.aux` file between passes one and two. `biber` is the equivalent for `biblatex`.
- Anything using `\label` inside floats, or packages like `longtable`, `tikz` with `remember picture`, or
  `hyperref` with back-references, may need a third or fourth pass to settle.

`latexmk` handles this automatically and is the right default when available. Otherwise: pdflatex → bibtex
→ pdflatex → pdflatex.

Watch for **non-convergence**: if "Label(s) may have changed" persists after four passes, something is
oscillating — commonly a float whose placement changes the page count, which changes the reference, which
moves the float. Fix the float placement rather than adding passes.

---

## The diagnostics and what causes them

### Overfull hbox

Something is wider than the measure. In order of likelihood:

- **A table wider than its column.** In two-column layouts this is the most common cause by far. Fix by
  promoting to `table*` (spanning both columns), reducing `\tabcolsep`, shortening column headers, dropping
  to `\footnotesize`, or converting a fixed-width column to `tabularx` with an `X` column that absorbs slack.
- **Long inline mathematics.** A formula that cannot break. Move it to display mode.
- **An unbreakable long word** — a URL, a file path, a code identifier. Use `\url{}` for URLs (which breaks
  them properly), `\seqsplit`, or insert `\allowbreak` at natural points. In a change-log or technical
  document full of identifiers, restructuring them into a displayed block is cleaner than fighting the
  line breaker.
- **A wide figure.** Scale to `\columnwidth` or `\textwidth`, or promote to `figure*`.

### Underfull hbox

A line is too loosely spaced, almost always because something unbreakable forced a bad break. The cause is
usually the same as an overfull box nearby — fix that and this resolves too. Underfull boxes with badness
10000 immediately after an overfull box are the same defect reported twice.

### Undefined references and citations

- Undefined reference: the `\label` does not exist, is misspelled, or is defined after use in a way the
  passes did not resolve. Check the label actually exists somewhere.
- Undefined citation: the key is absent from the `.bib`, or `bibtex` did not run, or it ran on a stale
  `.aux`. `scripts/audit_bibliography.py` finds the first case.

**A reference that resolves is not necessarily a reference that resolves correctly.** `\ref{sec:results}`
pointing to `\section*{Results}` — an unnumbered section, commonly used for back-matter like
Acknowledgements or Data Availability — silently resolves to whatever the *previous* numbered element was,
because `\section*` never advances the counter `\ref` reads. The compiler reports zero errors and zero
warnings; the PDF has a cross-reference pointing at the wrong section. This survives every diagnostic in
this document and is caught only by reading the compiled PDF against the source, which is exactly why Phase
4's number-tracing discipline extends to cross-references, not only to numeric literals. If a section needs
to be referenced, it needs a number (`\section{}`, not `\section*{}`) or an explicit anchor
(`\phantomsection\label{...}` from `hyperref`).

### "Missing $ inserted" pointing at `\end{tabularx}`

`tabularx` typesets its body more than once to solve for the width of the `X`
column. Inline mathematics inside an `X` cell can have its math shifts
unbalanced across those trial passes, and the error is reported at the closing
`\end{tabularx}` rather than at the cell responsible — which sends you looking
in the wrong place.

The table compiles and the PDF may even look correct, so this is easy to ship.
Fix by keeping mathematics out of `X` columns: use a fixed `l` or `p{}` column
for any column containing `$...$`, and reserve `X` for plain text.

The same re-scanning explains why `tabularx` dislikes `\verb`, footnotes and
other fragile content in `X` columns.

### Font warnings

Usually a size substitution. Fix by using a font package that provides the size rather than letting LaTeX
scale, or by adjusting the requested size.

### "Marginpar moved" / float warnings

Float placement is over-constrained. Loosen `[htbp]`, or use `\FloatBarrier` from `placeins` to keep floats
in their section rather than fighting each placement.

---

## Multi-language documents

This is where the subtle breakage lives, and it is worth checking deliberately because the failures are
silent or confusing.

### Babel and percent signs in mathematics

Spanish `babel` redefines `\%` in a way that is incompatible with math mode, producing an "Incompatible glue
units" error that names neither the file nor the cause. Write the percent outside mathematics:

```latex
% breaks under spanish babel
$45.2\%$

% correct
$45.2$\,\%
```

### Decimal separators

Spanish, French, German and others use a comma as the decimal separator and a point as the thousands
separator — the reverse of English. A number copied between language versions without conversion is
silently wrong by three orders of magnitude. When numbers are generated from a pipeline, handle the
convention in the generator per language.

`babel`'s `es-nodecimaldot` and the `siunitx` package both manage this properly. When numbers are
generated (see Phase 4's macro-file recommendation), the cleanest approach is to emit every value wrapped
in `\num{}` — `\newcommand{\CoefAll}{\num{0.29}}` — and let `siunitx` render the decimal mark, and even the
separator inside a list of values (`,` in English, `;` in Spanish, since a bare comma there would collide
with the decimal comma), according to the document's declared language. The macro file is then identical
in content across languages; only the rendering differs, and it differs correctly by construction.

### Quotation marks and punctuation

Languages differ in quotation marks (`«»`, `„“`, `""`), in spacing before high punctuation (French requires
a thin space before `:` and `?`), and in dash conventions. `babel` handles most of this if the language
option is set correctly — which is itself worth verifying, since an English document with the Spanish
option produces subtly wrong typography throughout.

### Hyphenation

Each language needs its hyphenation patterns loaded. A document set to the wrong language hyphenates
incorrectly, which shows up as a rash of overfull boxes with no obvious cause.

### Theorem environments and float names

`\newtheorem{theorem}{Theorem}` must be `{Teorema}`, `{Théorème}`, and so on. Similarly, `babel`'s
`es-tabla` option makes floats say "Cuadro" rather than "Tabla" — which convention the paper wants is a
choice, but it must be consistent within a version.

---

## Typography worth fixing

Beyond the diagnostics, the things a copy-editor at a good journal would mark:

- **Reference ranges and dashes.** En dash for numeric ranges (`2019--2024`), em dash or spaced en dash for
  parenthetical breaks, hyphen only for compounds.
- **Non-breaking spaces** before references and between a number and its unit: `Figure~\ref{fig:x}`,
  `5~mg`, `Section~\ref{sec:y}`. This prevents a line break separating them.
- **Units upright, variables italic.** `siunitx` handles this; `\mathrm{}` otherwise. A variable set upright
  or a unit set italic is a real error in physics and engineering venues.
- **Consistent notation.** The same symbol for the same quantity throughout, defined at first use. Check
  the paper does not use both $\hat{y}$ and $y_{\text{pred}}$ for the same thing.
- **Table rules.** `booktabs` (`\toprule`, `\midrule`, `\bottomrule`); no vertical rules; no double rules.
- **Microtypography.** Loading `microtype` improves justification measurably and costs one line.
- **Widows and orphans.** A single line of a paragraph stranded across a page break.

---

## Before declaring done

Confirm, per language version:

- Zero of every diagnostic class.
- The PDF page count is plausible and the document ends where it should.
- Every figure and table is referenced in the text, and every reference resolves.
- The bibliography renders, is in the journal's style, and has no `?` markers.
- Fonts embed — required by most journals; check with `pdffonts` if available.
- No `TODO`, `FIXME`, `XXX`, or placeholder text survives. Grep for them.
- Any `\input` paths resolve from the document's directory, not only from the repository root.
