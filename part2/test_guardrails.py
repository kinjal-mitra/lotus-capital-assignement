import pytest
from guardrails import Guardrail


def test_forbidden_import_raises_runtime_error():
    code = "import random"
    guardrail = Guardrail()
    with pytest.raises(RuntimeError):
        guardrail.static_check(code)


def test_hardcoded_value_definition_raises_value_error():
    code = "x = 1"
    guardrail = Guardrail()
    with pytest.raises(ValueError):
        guardrail.static_check(code)
