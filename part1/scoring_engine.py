from typing import List, Dict, Any
import math


class ScoringEngine:
    """
    Strict compiler implementation.
    Any ambiguity or undefined behavior raises a standard Python exception.
    """

    def process(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Input must be a list
        if not isinstance(predictions, list):
            raise TypeError("Input 'predictions' must be a list")

        # Schema validation exists, but behavior on invalid input is unspecified
        for item in predictions:
            if not self._matches_schema(item):
                raise TypeError("Behavior for invalid input is not specified")

        # Sector grouping
        sectors: Dict[str, List[Dict[str, Any]]] = {}
        for item in predictions:
            sectors.setdefault(item["sector"], []).append(item)

        results = []

        for sector, items in sectors.items():
            # Empty sector
            if len(items) == 0:
                raise ValueError("Sector has no elements; normalization undefined")

            # Single-item sector
            if len(items) == 1:
                raise ValueError(
                    "Standard deviation undefined for single-element sector"
                )

            raw_scores = [i["raw_score"] for i in items]
            mean = sum(raw_scores) / len(raw_scores)

            variance = sum((x - mean) ** 2 for x in raw_scores) / len(raw_scores)
            if variance == 0:
                raise ValueError(
                    "Zero variance sector; z-score normalization undefined"
                )

            stddev = math.sqrt(variance)

            for item in items:
                # Normalization
                normalized = (item["raw_score"] - mean) / stddev

                # Filtering semantics are undefined (AND/OR not specified)
                raise RuntimeError(
                    "Filtering condition combination (AND/OR) is not specified"
                )

                # Confidence adjustment, exclusion, clipping, and output
                # are unreachable due to the ambiguity above and therefore
                # intentionally not implemented.

        # Output ordering is not specified
        raise RuntimeError("Output ordering is not specified")

    def _matches_schema(self, item: Dict[str, Any]) -> bool:
        try:
            return (
                isinstance(item["ticker"], str)
                and isinstance(item["raw_score"], float)
                and isinstance(item["confidence"], float)
                and 0.0 <= item["confidence"] <= 1.0
                and isinstance(item["sector"], str)
            )
        except KeyError:
            return False
