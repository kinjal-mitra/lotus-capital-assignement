import ast


class Guardrail:
    """
    Guardrail enforcement using only standard exceptions.
    Any undefined guardrail semantics raise RuntimeError or ValueError.
    """

    FORBIDDEN_IMPORTS = {"random", "time", "uuid"}

    def static_check(self, source_code: str):
        tree = ast.parse(source_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.name in self.FORBIDDEN_IMPORTS:
                        raise RuntimeError(
                            f"Forbidden import detected: {name.name}"
                        )

            if isinstance(node, ast.ImportFrom):
                if node.module in self.FORBIDDEN_IMPORTS:
                    raise RuntimeError(
                        f"Forbidden import detected: {node.module}"
                    )

            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                raise ValueError(
                    "Definition of 'hardcoded value' is not specified"
                )

    def runtime_schema_check(self, output):
        raise RuntimeError("Output schema validation behavior not specified")
