from ocr_eval.models.domain import FieldResult, MISSING, _MissingType


def _try_numeric(value):
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace("$", "").strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    return None


def _values_match(expected, actual) -> bool:
    if isinstance(expected, _MissingType) or isinstance(actual, _MissingType):
        return False
    if expected is None and actual is None:
        return True
    if expected is None or actual is None:
        return False

    exp_num = _try_numeric(expected)
    act_num = _try_numeric(actual)
    if exp_num is not None and act_num is not None:
        return abs(exp_num - act_num) < 0.01

    if isinstance(expected, str) and isinstance(actual, str):
        return expected.strip().lower() == actual.strip().lower()

    return expected == actual


def compare_fields(expected: dict, actual: dict, path_prefix: str = "") -> list[FieldResult]:
    results = []
    all_keys = sorted(set(list(expected.keys()) + list(actual.keys())))

    for key in all_keys:
        current_path = f"{path_prefix}.{key}" if path_prefix else key
        exp_val = expected.get(key, MISSING)
        act_val = actual.get(key, MISSING)

        if isinstance(exp_val, dict) and isinstance(act_val, dict):
            results.extend(compare_fields(exp_val, act_val, current_path))
        elif isinstance(exp_val, list) and isinstance(act_val, list):
            max_len = max(len(exp_val), len(act_val))
            for i in range(max_len):
                item_path = f"{current_path}.{i}"
                e = exp_val[i] if i < len(exp_val) else MISSING
                a = act_val[i] if i < len(act_val) else MISSING
                if isinstance(e, dict) and isinstance(a, dict):
                    results.extend(compare_fields(e, a, item_path))
                else:
                    results.append(FieldResult(
                        field_path=item_path, expected_value=e,
                        actual_value=a, match=_values_match(e, a),
                    ))
        else:
            results.append(FieldResult(
                field_path=current_path, expected_value=exp_val,
                actual_value=act_val, match=_values_match(exp_val, act_val),
            ))

    return results
