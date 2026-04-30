def _norm(v: object, null_equals_blank: bool) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    if null_equals_blank and s.upper() == "NULL":
        return ""
    return s


def compare_dataset_rows(
    actual: list[dict],
    expected: list[dict],
    exact_column_match: bool = True,
    exact_row_count_match: bool = True,
    null_equals_blank: bool = True,
) -> dict:
    issues: list[str] = []
    actual_cols = list(actual[0].keys()) if actual else []
    expected_cols = list(expected[0].keys()) if expected else []
    column_match = actual_cols == expected_cols
    row_count_match = len(actual) == len(expected)

    if exact_column_match and actual_cols != expected_cols:
        issues.append(f"column mismatch: actual={actual_cols} expected={expected_cols}")

    if exact_row_count_match and len(actual) != len(expected):
        issues.append(f"row count mismatch: actual={len(actual)} expected={len(expected)}")

    compare_n = min(len(actual), len(expected))
    row_mismatch_count = 0
    cell_mismatch_count = 0
    compared_cell_count = 0
    mismatch_examples: list[dict] = []
    rows_with_mismatch: set[int] = set()
    for i in range(compare_n):
        a = actual[i]
        e = expected[i]
        cols = expected_cols if expected_cols else sorted(set(a.keys()) | set(e.keys()))
        for c in cols:
            av = _norm(a.get(c), null_equals_blank)
            ev = _norm(e.get(c), null_equals_blank)
            compared_cell_count += 1
            if av != ev:
                cell_mismatch_count += 1
                rows_with_mismatch.add(i)
                issues.append(f"row {i + 1}, col {c}: actual='{av}' expected='{ev}'")
                if len(mismatch_examples) < 20:
                    mismatch_examples.append({"row": i + 1, "column": c, "actual": av, "expected": ev})

    row_mismatch_count = len(rows_with_mismatch)
    matched_cell_count = compared_cell_count - cell_mismatch_count

    return {
        "ok": not issues,
        "issue_count": len(issues),
        "column_match": column_match,
        "row_count_match": row_count_match,
        "compared_cell_count": compared_cell_count,
        "matched_cell_count": matched_cell_count,
        "cell_mismatch_count": cell_mismatch_count,
        "row_mismatch_count": row_mismatch_count,
        "issues": issues[:50],
        "mismatch_examples": mismatch_examples,
    }
