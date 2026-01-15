import pytest
from guardrails import Guardrail


class TestStaticCheckImports:
    """Test detection of forbidden imports."""
    
    def test_forbidden_random_import_detected(self):
        """Test that 'import random' is detected."""
        code = "import random"
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is False
        assert len(result["violations"]) == 1
        assert "random" in result["violations"][0]
        assert "determinism" in result["violations"][0].lower()
    
    def test_forbidden_uuid_import_detected(self):
        """Test that 'import uuid' is detected."""
        code = "import uuid"
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is False
        assert "uuid" in result["violations"][0]
    
    def test_forbidden_requests_import_detected(self):
        """Test that 'import requests' is detected."""
        code = "import requests"
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is False
        assert "requests" in result["violations"][0]
        assert "external api" in result["violations"][0].lower()
    
    def test_forbidden_from_import_detected(self):
        """Test that 'from random import choice' is detected."""
        code = "from random import choice"
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is False
        assert "random" in result["violations"][0]
    
    def test_allowed_math_import_passes(self):
        """Test that allowed imports like 'import math' pass."""
        code = "import math"
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is True
        assert len(result["violations"]) == 0
    
    def test_allowed_typing_import_passes(self):
        """Test that 'from typing import List' passes."""
        code = "from typing import List, Dict"
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is True
    
    def test_multiple_forbidden_imports_detected(self):
        """Test multiple violations are all detected."""
        code = """
            import random
            import requests
            import uuid
            """
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is False
        assert len(result["violations"]) == 3


class TestStaticCheckRandomOperations:
    """Test detection of non-deterministic operations."""
    
    def test_random_random_call_detected(self):
        """Test that random.random() call is detected."""
        code = """
            import random
            x = random.random()
            """
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        # Should have both import violation and operation violation
        assert result["valid"] is False
        violations_text = " ".join(result["violations"])
        assert "random" in violations_text.lower()
    
    def test_random_choice_call_detected(self):
        """Test that random.choice() call is detected."""
        code = """
            import random
            x = random.choice([1, 2, 3])
            """
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is False
        assert any("choice" in v for v in result["violations"])
    
    def test_deterministic_code_passes(self):
        """Test that deterministic code passes."""
        code = """
            import math
            x = 4
            y = x * 2
            """
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is True


class TestStaticCheckExternalAPICalls:
    """Test detection of external API calls."""
    
    def test_requests_get_detected(self):
        """Test that requests.get() is detected."""
        code = """
            import requests
            response = requests.get("https://api.example.com")
            """
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is False
        violations_text = " ".join(result["violations"])
        assert "requests" in violations_text.lower()
        assert "api" in violations_text.lower() or "external" in violations_text.lower()
    
    def test_urllib_detected(self):
        """Test that urllib usage is detected."""
        code = """
            import urllib
            urllib.request.urlopen("http://youtube.com")
            """
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is False


class TestStaticCheckConditionals:
    """Test detection of suspicious conditional logic."""
    
    def test_hardcoded_numeric_conditional_flagged(self):
        """Test that conditionals with hardcoded numbers are flagged."""
        code = """
            if x > 100:
                do_something()
            """
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is False
        assert any("conditional" in v.lower() or "hardcoded" in v.lower() for v in result["violations"])
    
    def test_none_check_passes(self):
        """Test that None checks don't trigger false positives."""
        code = """
            if x is None:
                return []
            """
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        # None checks are allowed
        assert result["valid"] is True or not any("none" in v.lower() for v in result["violations"])
    
    def test_boolean_check_passes(self):
        """Test that boolean checks pass."""
        code = """
            if is_valid:
                process()
            """
        guardrail = Guardrail()
        result = guardrail.static_check(code)
        
        assert result["valid"] is True


class TestRuntimeSchemaCheck:
    """Test runtime schema validation."""
    
    def test_valid_list_schema_passes(self):
        """Test valid data against list schema."""
        guardrail = Guardrail()
        
        data = [
            {"ticker": "AAPL", "score": 1.5},
            {"ticker": "GOOGL", "score": 2.3}
        ]
        
        schema = {
            "type": "list",
            "fields": {
                "ticker": {"type": "string", "required": True},
                "score": {"type": "float", "required": True}
            }
        }
        
        result = guardrail.runtime_schema_check(data, schema)
        
        assert result["valid"] is True
        assert len(result["violations"]) == 0
    
    def test_missing_required_field_detected(self):
        """Test that missing required field is detected."""
        guardrail = Guardrail()
        
        data = [
            {"ticker": "AAPL"}  # Missing 'score'
        ]
        
        schema = {
            "type": "list",
            "fields": {
                "ticker": {"type": "string", "required": True},
                "score": {"type": "float", "required": True}
            }
        }
        
        result = guardrail.runtime_schema_check(data, schema)
        
        assert result["valid"] is False
        assert any("score" in v for v in result["violations"])
    
    def test_wrong_type_detected(self):
        """Test that wrong field type is detected."""
        guardrail = Guardrail()
        
        data = [
            {"ticker": 123, "score": 1.5}  # ticker should be string
        ]
        
        schema = {
            "type": "list",
            "fields": {
                "ticker": {"type": "string", "required": True},
                "score": {"type": "float", "required": True}
            }
        }
        
        result = guardrail.runtime_schema_check(data, schema)
        
        assert result["valid"] is False
        assert any("type" in v.lower() and "ticker" in v for v in result["violations"])
    
    def test_value_outside_range_detected(self):
        """Test that values outside specified range are detected."""
        guardrail = Guardrail()
        
        data = [
            {"confidence": 1.5}  # Outside [0.0, 1.0]
        ]
        
        schema = {
            "type": "list",
            "fields": {
                "confidence": {
                    "type": "float",
                    "required": True,
                    "range": [0.0, 1.0]
                }
            }
        }
        
        result = guardrail.runtime_schema_check(data, schema)
        
        assert result["valid"] is False
        assert any("range" in v.lower() for v in result["violations"])
    
    def test_unexpected_field_detected(self):
        """Test that unexpected fields are detected."""
        guardrail = Guardrail()
        
        data = [
            {"ticker": "AAPL", "score": 1.5, "extra": "unexpected"}
        ]
        
        schema = {
            "type": "list",
            "fields": {
                "ticker": {"type": "string", "required": True},
                "score": {"type": "float", "required": True}
            }
        }
        
        result = guardrail.runtime_schema_check(data, schema)
        
        assert result["valid"] is False
        assert any("unexpected" in v.lower() or "extra" in v for v in result["violations"])
    
    def test_wrong_container_type_detected(self):
        """Test that wrong container type is detected."""
        guardrail = Guardrail()
        
        data = {"ticker": "AAPL"}  # Should be a list
        
        schema = {
            "type": "list",
            "fields": {
                "ticker": {"type": "string", "required": True}
            }
        }
        
        result = guardrail.runtime_schema_check(data, schema)
        
        assert result["valid"] is False
        assert any("list" in v.lower() for v in result["violations"])
    
    def test_optional_field_missing_passes(self):
        """Test that optional missing fields pass validation."""
        guardrail = Guardrail()
        
        data = [
            {"ticker": "AAPL"}  # 'score' is optional
        ]
        
        schema = {
            "type": "list",
            "fields": {
                "ticker": {"type": "string", "required": True},
                "score": {"type": "float", "required": False}
            }
        }
        
        result = guardrail.runtime_schema_check(data, schema)
        
        assert result["valid"] is True


class TestCheckNoHardcodedValues:
    """Test detection of hardcoded values."""
    
    def test_allowed_constants_pass(self):
        """Test that constants from spec are allowed."""
        code = """
            if confidence >= 0.3:
                pass
            """
        guardrail = Guardrail()
        allowed = {0.3, 0.5, -3.0, 3.0}
        result = guardrail.check_no_hardcoded_values(code, allowed)
        
        assert result["valid"] is True
    
    def test_disallowed_constants_detected(self):
        """Test that constants not in spec are detected."""
        code = """
            if score > 100:  # 100 not in spec
                pass
            """
        guardrail = Guardrail()
        allowed = {0.3, 0.5, -3.0, 3.0}
        result = guardrail.check_no_hardcoded_values(code, allowed)
        
        assert result["valid"] is False
        assert any("100" in v for v in result["violations"])
    
    def test_string_constants_ignored(self):
        """Test that string constants are not flagged."""
        code = """
            message = "Hello World"
            """
        guardrail = Guardrail()
        result = guardrail.check_no_hardcoded_values(code, set())
        
        assert result["valid"] is True
    
    def test_none_true_false_ignored(self):
        """Test that None, True, False are not flagged."""
        code = """
            if x is None:
                return True
            else:
                return False
            """
        guardrail = Guardrail()
        result = guardrail.check_no_hardcoded_values(code, set())
        
        assert result["valid"] is True


class TestInvalidSyntax:
    """Test handling of invalid Python syntax."""
    
    def test_invalid_syntax_raises_syntax_error(self):
        """Test that invalid Python raises SyntaxError."""
        code = "if x > 5"  # Missing colon
        guardrail = Guardrail()
        
        with pytest.raises(SyntaxError):
            guardrail.static_check(code)