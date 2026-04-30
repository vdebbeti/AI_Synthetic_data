import csv
import json
from pathlib import Path

from sdtm_adam_compiler.eval.diff import compare_dataset_rows
from sdtm_adam_compiler.orchestration.execute import build_raw_registry, execute_ir_to_rows
from sdtm_adam_compiler.orchestration.spec_to_ir import build_ir_from_spec


def _load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def run_case(
    case_path: str | Path,
    spec_type_filter: str | None = None,
    dataset_filter: str | None = None,
) -> dict:
    case_file = Path(case_path)
    root = case_file.parents[2] if len(case_file.parents) >= 3 else Path(".")
    case = json.loads(case_file.read_text(encoding="utf-8"))
    assertions = case.get("assertions", {})
    raw_registry = build_raw_registry(case["raw_inputs"], root)
    working_registry = dict(raw_registry)
    results: list[dict] = []
    spec_inputs = sorted(case["spec_inputs"], key=lambda x: 0 if x["type"] == "SDTM" else 1)
    expected_by_dataset = {e["dataset"].upper(): e for e in case["expected_outputs"]}

    for spec in spec_inputs:
        ir = build_ir_from_spec(str(root / spec["path"]), spec["type"])
        actual_outputs = execute_ir_to_rows(ir, working_registry)
        working_registry.update(actual_outputs)

        for dataset in sorted(actual_outputs.keys()):
            if spec_type_filter and spec["type"] != spec_type_filter:
                continue
            if dataset_filter and dataset != dataset_filter.upper():
                continue
            if dataset not in expected_by_dataset:
                continue
            exp = expected_by_dataset[dataset]
            expected_rows = _load_csv(root / exp["path"])
            actual_rows = actual_outputs.get(dataset, [])
            cmp = compare_dataset_rows(
                actual_rows,
                expected_rows,
                exact_column_match=assertions.get("exact_column_match", True),
                exact_row_count_match=assertions.get("exact_row_count_match", True),
                null_equals_blank=assertions.get("null_equals_blank", True),
            )
            results.append(
                {
                    "spec_type": spec["type"],
                    "dataset": dataset,
                    "ok": cmp["ok"],
                    "issue_count": cmp["issue_count"],
                    "column_match": cmp["column_match"],
                    "row_count_match": cmp["row_count_match"],
                    "compared_cell_count": cmp["compared_cell_count"],
                    "matched_cell_count": cmp["matched_cell_count"],
                    "cell_mismatch_count": cmp["cell_mismatch_count"],
                    "row_mismatch_count": cmp["row_mismatch_count"],
                    "row_count_actual": len(actual_rows),
                    "row_count_expected": len(expected_rows),
                    "issues": cmp["issues"],
                    "mismatch_examples": cmp["mismatch_examples"],
                }
            )

    pass_count = sum(1 for r in results if r["ok"])
    return {
        "case_id": case["case_id"],
        "total_checks": len(results),
        "passed_checks": pass_count,
        "pass_rate": (pass_count / len(results) * 100.0) if results else 0.0,
        "checks": results,
        "status": "ok" if pass_count == len(results) else "warning",
    }
