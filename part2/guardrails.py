import ast
from typing import Any, Dict, List, Set


class Guardrail:
    """
    Validation layer that ensures generated code never violates logic boundaries.
    """
    
    # Imports that introduce non-determinism
    FORBIDDEN_NONDETERMINISTIC_IMPORTS = {"random", "uuid"}
    
    # Imports that make external calls
    FORBIDDEN_EXTERNAL_IMPORTS = {"requests", "urllib", "http", "httpx", "aiohttp"}
    
    # All forbidden imports combined
    FORBIDDEN_IMPORTS = FORBIDDEN_NONDETERMINISTIC_IMPORTS | FORBIDDEN_EXTERNAL_IMPORTS
    
    # Allowed mathematical/data processing imports
    ALLOWED_IMPORTS = {"math", "typing", "collections", "itertools", "functools", "dataclasses"}
    
    def static_check(self, source_code: str) -> Dict[str, Any]:
        """
        Perform analysis on code to detect prohibited patterns.
        
        Args:
            source_code: Python code to analyze
            
        Returns:
            Dictionary with validation results:
            
        Raises:
            SyntaxError: If source code is invalid Python
        """
        violations = []
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise SyntaxError(f"Invalid Python syntax: {e}")
        
        # Check for forbidden imports
        import_violations = self._check_imports(tree)
        violations.extend(import_violations)
        
        # Check for random operations
        random_violations = self._check_random_operations(tree)
        violations.extend(random_violations)
        
        # Check for external API calls
        api_violations = self._check_external_api_calls(tree)
        violations.extend(api_violations)
        
        # Check for conditional logic outside spec
        conditional_violations = self._check_suspicious_conditionals(tree)
        violations.extend(conditional_violations)
        
        return {
            "valid": len(violations) == 0,
            "violations": violations
        }
    
    def _check_imports(self, tree: ast.AST) -> List[str]:
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.FORBIDDEN_IMPORTS:
                        violations.append(
                            f"Forbidden import detected: 'import {alias.name}' "
                            f"(violates determinism/external API restrictions)"
                        )
            
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.FORBIDDEN_IMPORTS:
                    violations.append(
                        f"Forbidden import detected: 'from {node.module} import ...' "
                        f"(violates determinism/external API restrictions)"
                    )
        
        return violations
    
    def _check_random_operations(self, tree: ast.AST) -> List[str]:
        violations = []
        
        for node in ast.walk(tree):
            # Check for calls to random module functions
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # random.random(), random.choice(), etc.
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == 'random':
                        violations.append(
                            f"Non-deterministic operation detected: random.{node.func.attr}() "
                            f"(violates determinism requirement)"
                        )
                elif isinstance(node.func, ast.Name):
                    # Direct calls to random functions if imported with 'from random import ...'
                    suspicious_names = {'random', 'randint', 'choice', 'shuffle', 'sample', 'uniform'}
                    if node.func.id in suspicious_names:
                        violations.append(
                            f"Potentially non-deterministic operation detected: {node.func.id}() "
                            f"(verify this is not from random module)"
                        )
        
        return violations
    
    def _check_external_api_calls(self, tree: ast.AST) -> List[str]:
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for requests.get(), requests.post(), etc.
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id in {'requests', 'urllib', 'http', 'httpx'}:
                            violations.append(
                                f"External API call detected: {node.func.value.id}.{node.func.attr}() "
                                f"(violates no external API calls restriction)"
                            )
                
                # Check for direct function calls that suggest HTTP operations
                elif isinstance(node.func, ast.Name):
                    if node.func.id in {'urlopen', 'get', 'post', 'put', 'delete', 'patch'}:
                        violations.append(
                            f"Potentially external API call detected: {node.func.id}() "
                            f"(verify this is not an HTTP operation)"
                        )
        
        return violations
    
    def _check_suspicious_conditionals(self, tree: ast.AST) -> List[str]:
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp)):
                # Check if condition contains hardcoded numeric comparisons that aren't part of common patterns (like None checks, type checks)
                if self._contains_suspicious_hardcoded_logic(node):
                    violations.append(
                        f"Suspicious conditional logic detected with hardcoded values "
                        f"(verify this is specified in logic spec)"
                    )
        
        return violations
    
    def _contains_suspicious_hardcoded_logic(self, node: ast.AST) -> bool:
        if isinstance(node, ast.If):
            test = node.test
        elif isinstance(node, ast.IfExp):
            test = node.test
        else:
            return False
        
        # Look for numeric constants in comparisons
        for subnode in ast.walk(test):
            if isinstance(subnode, ast.Compare):
                # Check if comparing against numeric literal
                for comparator in subnode.comparators:
                    if isinstance(comparator, ast.Constant):
                        if isinstance(comparator.value, (int, float)):
                            # Found numeric constant in comparison
                            return True
        
        return False
    
    def runtime_schema_check(self, data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data against a schema specification at runtime.
        
        Args:
            data: Data to validate (typically a dict or list of dicts)
            schema: Schema specification defining expected structure and types
        
        Returns:
            Dictionary with validation results
        """
        violations = []
        
        # Validate container type
        expected_type = schema.get("type")
        if expected_type == "list":
            if not isinstance(data, list):
                violations.append(f"Expected list, got {type(data).__name__}")
                return {"valid": False, "violations": violations}
            
            # Validate each item in list
            for idx, item in enumerate(data):
                item_violations = self._validate_dict_against_schema(item, schema.get("fields", {}), f"item[{idx}]")
                violations.extend(item_violations)
        
        elif expected_type == "dict":
            item_violations = self._validate_dict_against_schema(data, schema.get("fields", {}), "data")
            violations.extend(item_violations)
        
        else:
            violations.append(f"Unknown schema type: {expected_type}")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations
        }
    
    def _validate_dict_against_schema(self, data: Dict, fields: Dict[str, Any], prefix: str) -> List[str]:
        """
        Validate a dictionary against field specifications.
        
        Args:
            data: Dictionary to validate
            fields: Field specifications
            prefix: Prefix for error messages
            
        Returns:
            List of violation messages
        """
        violations = []
        
        if not isinstance(data, dict):
            violations.append(f"{prefix}: Expected dict, got {type(data).__name__}")
            return violations
        
        # Check required fields
        for field_name, field_spec in fields.items():
            if field_spec.get("required", True):
                if field_name not in data:
                    violations.append(f"{prefix}: Missing required field '{field_name}'")
                    continue
            else:
                if field_name not in data:
                    continue 
            
            # Validate field type
            expected_type = field_spec.get("type")
            actual_value = data[field_name]
            
            type_valid = self._check_type(actual_value, expected_type)
            if not type_valid:
                violations.append(
                    f"{prefix}.{field_name}: Expected type '{expected_type}', "
                    f"got {type(actual_value).__name__}"
                )
                continue
            
            # Validate range if specified
            if "range" in field_spec and isinstance(actual_value, (int, float)):
                range_spec = field_spec["range"]
                min_val, max_val = range_spec[0], range_spec[1]
                if not (min_val <= actual_value <= max_val):
                    violations.append(
                        f"{prefix}.{field_name}: Value {actual_value} outside range [{min_val}, {max_val}]"
                    )
        
        # Check for unexpected fields (not in schema)
        expected_fields = set(fields.keys())
        actual_fields = set(data.keys())
        unexpected = actual_fields - expected_fields
        
        if unexpected:
            violations.append(
                f"{prefix}: Unexpected fields found: {', '.join(unexpected)}"
            )
        
        return violations
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        type_map = {
            "string": str,
            "float": (float, int),
            "int": int,
            "boolean": bool,
            "bool": bool
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            return False
        
        return isinstance(value, expected_python_type)
    
    def check_no_hardcoded_values(self, source_code: str, allowed_constants: Set[Any] = None) -> Dict[str, Any]:
        """
        Check for hardcoded values that aren't part of the spec.
        """
        if allowed_constants is None:
            allowed_constants = set()
        
        violations = []
        tree = ast.parse(source_code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                value = node.value
                
                # Skip string constants (variable names, messages, etc.)
                if isinstance(value, str):
                    continue
                
                # Skip None, True, False (common Python constants)
                if value in {None, True, False}:
                    continue
                
                # Check if this constant is allowed by spec
                if isinstance(value, (int, float)):
                    if value not in allowed_constants:
                        violations.append(
                            f"Hardcoded value detected: {value} "
                            f"(not in allowed constants: {allowed_constants})"
                        )
        
        return {
            "valid": len(violations) == 0,
            "violations": violations
        }