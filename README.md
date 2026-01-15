## Overview

This submission implements a strict, compiler-style interpretation of the provided YAML specifications.
In the system whenever the specification does not define behavior precisely, execution halts with a Python error.

16 tests failed, 46 passed.

---

### Part 1: ScoringEngine — Detected Errors

The following errors are raised during execution because the specification does not define required behavior:

- Invalid Input Handling Undefined

- The spec defines input types but does not specify behavior when:

- A field is missing

- A field has the wrong type

- confidence is outside the allowed range

Result: TypeError is raised when invalid input is encountered.

- Empty Sector

- Sector-wise normalization is requested, but behavior for a sector with zero predictions is undefined.

Result: ValueError is raised.

- Single-Element Sector

- Z-score normalization requires a standard deviation, which is undefined for a single data point.

Result: ValueError is raised.

- Zero Variance Sector

- Z-score normalization divides by standard deviation, which becomes zero in this case.

Result: ValueError is raised.

- Filtering Logic Ambiguity

- The filtering conditions do not specify whether they are combined using AND or OR.

Result: RuntimeError is raised before filtering can be applied.

- Output Clipping Order Undefined

- The spec does not define whether clipping occurs before or after exclusion.

Result: Execution cannot proceed past earlier ambiguities.

- Output Ordering Undefined

- Deterministic output ordering is claimed but not specified.

Result: RuntimeError is raised before output emission.

--- 

## Part 2: Guardrails — Detected Errors

The guardrail system enforces only what is explicitly defined. Where definitions are missing, errors are raised.

- Forbidden Imports

- Use of random, time, or uuid is explicitly disallowed.

Result: RuntimeError is raised if detected via AST analysis.

- Hardcoded Values Definition Missing

- The rule no_hardcoded_values: true is present, but the term “hardcoded value” is not defined.

Result: Any numeric literal triggers a ValueError.

- Runtime Output Schema Validation Undefined

- Output schema validation behavior is not specified.

Result: RuntimeError is raised if runtime validation is attempted.

---

### Relationship to Part 3

- Part 1 and Part 2 raise errors during execution due to ambiguities.

- Part 3 documents why such ambiguities exist and why they prevent deterministic implementation.
---

