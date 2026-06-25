from ocr_eval.models.domain import FieldResult, MISSING


def compute_accuracy(field_results: list[FieldResult]) -> float:
    if not field_results:
        return 0.0
    return sum(1 for f in field_results if f.match) / len(field_results)


def generate_diff_report(field_results: list[FieldResult]) -> str:
    total = len(field_results)
    matched = sum(1 for f in field_results if f.match)
    mismatched = total - matched
    accuracy = compute_accuracy(field_results)

    lines = [
        "Field Comparison Report",
        "=" * 40,
        f"Total Fields: {total}",
        f"Matched: {matched}",
        f"Mismatched: {mismatched}",
        f"Accuracy: {accuracy:.1%}",
        "",
    ]

    matches = [f for f in field_results if f.match]
    mismatches = [f for f in field_results if not f.match]

    if matches:
        lines.append("MATCHES:")
        for f in matches:
            lines.append(f"  [OK] {f.field_path}: {_fmt(f.expected_value)}")
        lines.append("")

    if mismatches:
        lines.append("MISMATCHES:")
        for f in mismatches:
            lines.append(f"  [XX] {f.field_path}:")
            lines.append(f"       Expected: {_fmt(f.expected_value)}")
            lines.append(f"       Actual:   {_fmt(f.actual_value)}")
        lines.append("")

    return "\n".join(lines)


def _fmt(value) -> str:
    if value is MISSING:
        return "<missing>"
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)
