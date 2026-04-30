import csv
import json
from pathlib import Path

from sdtm_adam_compiler.eval.diff import compare_dataset_rows
from sdtm_adam_compiler.eval.executor import try_execute_r, try_execute_sas
from sdtm_adam_compiler.orchestration.execute import build_raw_registry, execute_ir_to_rows
from sdtm_adam_compiler.orchestration.spec_to_ir import build_ir_from_spec
from sdtm_adam_compiler.renderers.r_renderer import render_r
from sdtm_adam_compiler.renderers.sas_renderer import render_sas


def _load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def run_case(
    case_path: str | Path,
    execute_generated_code: bool = False,
    sas_executable: str | None = None,
    rscript_executable: str | None = None,
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
    execution_reports: list[dict] = []

    for spec in spec_inputs:
        ir = build_ir_from_spec(str(root / spec["path"]), spec["type"])
        actual_outputs = execute_ir_to_rows(ir, working_registry)
        working_registry.update(actual_outputs)

        if execute_generated_code:
            eval_dir = root / "tmp_eval"
            eval_dir.mkdir(parents=True, exist_ok=True)
            sas_path = eval_dir / f"{spec['type'].lower()}_generated.sas"
            r_path = eval_dir / f"{spec['type'].lower()}_generated.R"
            sas_path.write_text(render_sas(ir), encoding="utf-8")
            r_path.write_text(render_r(ir), encoding="utf-8")
            execution_reports.append(try_execute_sas(sas_path, eval_dir, sas_executable=sas_executable))
            execution_reports.append(try_execute_r(r_path, eval_dir, rscript_executable=rscript_executable))

        for dataset in sorted(actual_outputs.keys()):
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
                    "row_count_actual": len(actual_rows),
                    "row_count_expected": len(expected_rows),
                    "issues": cmp["issues"],
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
        "execution_reports": execution_reports,
    }
