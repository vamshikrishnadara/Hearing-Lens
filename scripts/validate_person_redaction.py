"""Report name coverage on fixed fictional development fixtures, never uploads.

Run from the repository root: python -m scripts.validate_person_redaction
"""

from collections import Counter
import json
from pathlib import Path
import re
from time import perf_counter

import pandas as pd
import spacy

from pipeline.redact import _get_person_model, redact_frame


def main():
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "data/samples/person_redaction_cases.json").read_text())
    start = perf_counter()
    result = redact_frame(pd.DataFrame({"comment_text": [case["text"] for case in cases]}))
    results = []
    expected_mentions = 0
    fully_removed = 0
    controls_with_person_marker = 0
    for case, output in zip(cases, result.frame["redacted_comment_text"]):
        residuals = []
        for name, count in Counter(case["names"]).items():
            expected_mentions += count
            # Strict check: partial names left visible count as misses too.
            tokens = re.findall(r"[^\W\d_]+", name, flags=re.UNICODE)
            remaining = min(count, max(
                (len(re.findall(r"\b" + re.escape(token) + r"\b", output, re.IGNORECASE))
                 for token in tokens), default=0
            ))
            fully_removed += count - remaining
            if remaining:
                residuals.append(name)
        if not case["names"] and "[PERSON]" in output:
            controls_with_person_marker += 1
        results.append({"input": case["text"], "output": output, "names_not_fully_removed": residuals})

    sample = pd.read_csv(root / "data/samples/synthetic_chicago_hearing.csv")
    sample_start = perf_counter()
    sample_result = redact_frame(sample)
    sample_seconds = perf_counter() - sample_start
    planted = removed = false_broken = 0
    for source, output in zip(sample["comment_text"], sample_result.frame["redacted_comment_text"]):
        if source.startswith("Broken exterior lighting") and output.startswith("[PERSON] exterior lighting"):
            false_broken += 1
        match = re.search(r"Contact (.+?) at sample\.person\d+@example\.org", source)
        if match:
            planted += 1
            if all(not re.search(r"\b" + re.escape(token) + r"\b", output) for token in match[1].split()):
                removed += 1
    lighting_cases = json.loads(
        (root / "data/samples/lighting_redaction_cases.json").read_text()
    )
    lighting_result = redact_frame(
        pd.DataFrame({"comment_text": [case["text"] for case in lighting_cases]})
    )
    lighting_checks = [
        {"input": case["text"], "expected_output": case["expected_output"],
         "output": output, "matches_expected": output == case["expected_output"]}
        for case, output in zip(lighting_cases, lighting_result.frame["redacted_comment_text"])
    ]
    print(json.dumps({
        "fixture_notice": "All examples are fictional. Small development checks, not a privacy guarantee or population benchmark.",
        "spacy_version": spacy.__version__,
        "model": "en_core_web_sm", "model_version": _get_person_model().meta["version"],
        "case_count": len(cases), "expected_name_mentions": expected_mentions,
        "fully_removed_name_mentions": fully_removed,
        "name_free_controls": sum(not case["names"] for case in cases),
        "controls_with_person_marker": controls_with_person_marker,
        "cases": results,
        "synthetic_sample": {"rows": len(sample), "planted_name_mentions": planted,
                             "fully_removed_name_mentions": removed,
                             "false_positive_Broken_replacements": false_broken,
                             "entity_counts": sample_result.entity_counts,
                             "warm_run_seconds": round(sample_seconds, 3)},
        "lighting_regression_cases": {
            "case_count": len(lighting_checks),
            "matches_expected": sum(case["matches_expected"] for case in lighting_checks),
            "cases": lighting_checks,
        },
        "total_seconds_including_model_load": round(perf_counter() - start, 3),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
