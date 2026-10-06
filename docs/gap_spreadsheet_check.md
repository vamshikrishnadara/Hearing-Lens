# Independent spreadsheet calculation check

The October 6 workbook reads the 1,000 fictional source role/tenure categories
and calculates counts, known-row denominators, participation, gaps and ratios
using spreadsheet formulas. It compares those results with a separate snapshot
from `analyze_gaps`. It is development validation, not real population analysis.

All eight rows matched. Counts and flags agreed exactly; numerical differences
rounded to zero at 12 decimal places and were independently within 1e-12.
Ordinary spreadsheet arithmetic has floating-point rounding, so this is not a
claim of bit-for-bit equality of every floating-point value. The existing
`scripts.validate_gaps` check also compares exact rational expectations with the
pipeline's float outputs.

For example, Parent participation is 541 / 1,000 = 0.541. The fictional reference
is 0.4. Gap = 100 × (0.541 − 0.4) = 14.1 percentage points; ratio = 0.541 / 0.4 =
1.3525. It is above the strict 1.25 threshold. The workbook shows each step and
all source categories so a reviewer can reproduce it.

The builder verified that changing a reference changes the calculations and
comparison result, and that a zero reference produces an unavailable ratio.
It then restored the supplied baseline and recalculated. The formula error scan
was clear. Both worksheet layouts were visually checked. Calculation was tested
in the artifact runtime; native Excel recalculation has not been tested.

The workbook is restricted to this fixed, nonmissing, unsuppressed fixture.
It is not a general replacement for the production gap module. The existing
gap tests separately cover missing values, zero baselines, unmatched categories
and small-group/complementary suppression.

## Reproduction

```sh
python -m scripts.prepare_gap_spreadsheet --output /path/to/local/gap-input.json
node scripts/build_gap_spreadsheet.mjs /path/to/local/gap-input.json /path/to/local/output
```

The optional workbook builder requires `@oai/artifact-tool` in the document
runtime. It is not a production Python dependency. In environments without that
package, the inputs and published formulas can be checked in a spreadsheet
application. Existing input/output files are preserved; choose a new destination.
The saved workbook and inspection files remain local outside Git.

**Human review remains pending.** Creating and automatically recalculating this
workbook does not complete the brief's hand-computed spreadsheet check. The
reviewer/date fields are blank. A person still needs to check the arithmetic.
