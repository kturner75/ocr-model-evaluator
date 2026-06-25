import jsonschema


def validate_extraction(extracted: dict, schema: dict) -> tuple[bool, list[str]]:
    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for error in sorted(validator.iter_errors(extracted), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.path) or "(root)"
        errors.append(f"{path}: {error.message}")
    return (len(errors) == 0, errors)
