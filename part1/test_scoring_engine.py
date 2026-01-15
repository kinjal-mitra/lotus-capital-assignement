import pytest
import math
from scoring_engine import ScoringEngine


class TestScoringEngineNormalCases:
    
    def test_basic_two_sector_processing(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "AAPL", "raw_score": 2.0, "confidence": 0.8, "sector": "tech"},
            {"ticker": "GOOGL", "raw_score": 3.0, "confidence": 0.9, "sector": "tech"},
            {"ticker": "JPM", "raw_score": 1.5, "confidence": 0.7, "sector": "finance"},
            {"ticker": "BAC", "raw_score": 2.5, "confidence": 0.6, "sector": "finance"},
        ]
        
        results = engine.process(data)
        
        assert len(results) == 4
        assert all("final_score" in r for r in results)
        assert all("excluded" in r for r in results)
        assert all("sector" in r for r in results)
    
    def test_normalization_calculation_exact(self):
        engine = ScoringEngine()
        # Scores: 1, 2, 3 -> mean=2, variance=2/3, stddev=sqrt(2/3)~0.8165
        data = [
            {"ticker": "A", "raw_score": 1.0, "confidence": 1.0, "sector": "tech"},
            {"ticker": "B", "raw_score": 2.0, "confidence": 1.0, "sector": "tech"},
            {"ticker": "C", "raw_score": 3.0, "confidence": 1.0, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        # Calculate expected values
        mean = 2.0
        variance = ((1.0-2.0)**2 + (2.0-2.0)**2 + (3.0-2.0)**2) / 3
        stddev = math.sqrt(variance)
        
        # normalized_score for A: (1-2)/stddev = -1/stddev ~ -1.2247
        # With confidence=1.0, final_score = normalized_score (before clipping)
        expected_a = (1.0 - mean) / stddev
        expected_b = (2.0 - mean) / stddev  # 0
        expected_c = (3.0 - mean) / stddev
        
        result_a = next(r for r in results if r["ticker"] == "A")
        result_b = next(r for r in results if r["ticker"] == "B")
        result_c = next(r for r in results if r["ticker"] == "C")
        
        assert abs(result_a["final_score"] - expected_a) < 0.0001
        assert abs(result_b["final_score"] - expected_b) < 0.0001
        assert abs(result_c["final_score"] - expected_c) < 0.0001
    
    def test_confidence_adjustment_applied(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "A", "raw_score": 1.0, "confidence": 1.0, "sector": "tech"},
            {"ticker": "B", "raw_score": 3.0, "confidence": 0.5, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        result_a = next(r for r in results if r["ticker"] == "A")
        result_b = next(r for r in results if r["ticker"] == "B")
        
        # Both have same absolute normalized score magnitude (symmetric around mean=2)
        # But B has 0.5 confidence, so final_score magnitude should be halved
        score_a_magnitude = abs(result_a["final_score"])
        score_b_magnitude = abs(result_b["final_score"])
        
        # B's score should be approximately half of A's (both are ~1.2247, so B ~ 0.6124)
        assert abs(score_b_magnitude - score_a_magnitude * 0.5) < 0.0001
    
    def test_filtering_excludes_low_confidence(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "A", "raw_score": 1.0, "confidence": 0.2, "sector": "tech"},
            {"ticker": "B", "raw_score": 3.0, "confidence": 0.5, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        result_a = next(r for r in results if r["ticker"] == "A")
        result_b = next(r for r in results if r["ticker"] == "B")
        
        assert result_a["excluded"] is True
        assert "confidence" in result_a["exclusion_reason"]
        assert result_b["excluded"] is False
        assert result_b["exclusion_reason"] is None
    
    def test_filtering_excludes_low_magnitude(self):
        engine = ScoringEngine()
        # Create scores very close together so normalized scores are small
        data = [
            {"ticker": "A", "raw_score": 1.98, "confidence": 0.9, "sector": "tech"},
            {"ticker": "B", "raw_score": 2.00, "confidence": 0.9, "sector": "tech"},
            {"ticker": "C", "raw_score": 2.02, "confidence": 0.9, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        # All normalized scores will be very small (< 0.5 magnitude)
        assert all(r["excluded"] for r in results)
        assert all("normalized_score" in r["exclusion_reason"] for r in results)
    
    def test_filtering_and_logic_both_conditions_must_pass(self):
        engine = ScoringEngine()
        data = [
            # Passes confidence, fails magnitude
            {"ticker": "A", "raw_score": 2.0, "confidence": 0.9, "sector": "tech"},
            # Fails confidence, would pass magnitude
            {"ticker": "B", "raw_score": 1.0, "confidence": 0.2, "sector": "tech"},
            {"ticker": "C", "raw_score": 3.0, "confidence": 0.2, "sector": "tech"},
            # Passes both
            {"ticker": "D", "raw_score": 1.0, "confidence": 0.9, "sector": "tech"},
            {"ticker": "E", "raw_score": 3.0, "confidence": 0.9, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        result_map = {r["ticker"]: r for r in results}
        
        # A: high confidence but normalized~0, should be excluded
        assert result_map["A"]["excluded"] is True
        
        # B,C: low confidence, should be excluded regardless of magnitude
        assert result_map["B"]["excluded"] is True
        assert result_map["C"]["excluded"] is True
        
        # D,E: both conditions pass, should NOT be excluded
        assert result_map["D"]["excluded"] is False
        assert result_map["E"]["excluded"] is False
    
    def test_output_clipping_at_bounds(self):
        engine = ScoringEngine()
        # Create extreme scores to trigger clipping
        data = [
            {"ticker": "A", "raw_score": -1000.0, "confidence": 1.0, "sector": "tech"},
            {"ticker": "B", "raw_score": 1000.0, "confidence": 1.0, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        # All scores must be within bounds
        assert all(-3.0 <= r["final_score"] <= 3.0 for r in results)
        
        # Both should hit the boundaries
        result_a = next(r for r in results if r["ticker"] == "A")
        result_b = next(r for r in results if r["ticker"] == "B")
        
        assert result_a["final_score"] == -3.0
        assert result_b["final_score"] == 3.0
    
    def test_clipping_with_confidence_adjustment(self):
        engine = ScoringEngine()
        # Extreme score with low confidence
        data = [
            {"ticker": "A", "raw_score": -1000.0, "confidence": 0.5, "sector": "tech"},
            {"ticker": "B", "raw_score": 1000.0, "confidence": 0.5, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        result_a = next(r for r in results if r["ticker"] == "A")
        result_b = next(r for r in results if r["ticker"] == "B")
        
        # Even with confidence=0.5, extreme normalized scores should still clip at + or -3.0
        assert result_a["final_score"] == -3.0
        assert result_b["final_score"] == 3.0


class TestScoringEngineEdgeCases:    
    def test_empty_input_returns_empty_list(self):
        engine = ScoringEngine()
        results = engine.process([])
        assert results == []
    
    def test_single_prediction_single_sector(self):
        engine = ScoringEngine()
        data = [{"ticker": "AAPL", "raw_score": 5.0, "confidence": 0.8, "sector": "tech"}]
        
        results = engine.process(data)
        
        assert len(results) == 1
        assert results[0]["ticker"] == "AAPL"
        # Single item: normalized_score = 0, so final = 0 * 0.8 = 0
        assert results[0]["final_score"] == 0.0
        # Should be excluded (magnitude < 0.5)
        assert results[0]["excluded"] is True
    
    def test_zero_variance_sector_all_identical(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "A", "raw_score": 5.0, "confidence": 0.8, "sector": "tech"},
            {"ticker": "B", "raw_score": 5.0, "confidence": 0.9, "sector": "tech"},
            {"ticker": "C", "raw_score": 5.0, "confidence": 0.7, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        assert len(results) == 3
        # All should have final_score = 0 (normalized=0 * confidence)
        assert all(r["final_score"] == 0.0 for r in results)
        # All should be excluded (magnitude = 0 < 0.5)
        assert all(r["excluded"] for r in results)
    
    def test_confidence_exactly_at_threshold_030(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "A", "raw_score": 1.0, "confidence": 0.3, "sector": "tech"},
            {"ticker": "B", "raw_score": 3.0, "confidence": 0.3, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        # Confidence >= 0.3 passes confidence check
        # Check that confidence alone doesn't exclude
        for r in results:
            if r["excluded"] and r["exclusion_reason"]:
                assert "confidence" not in r["exclusion_reason"] or "0.3" not in r["exclusion_reason"]
    
    def test_confidence_just_below_threshold(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "A", "raw_score": 1.0, "confidence": 0.29, "sector": "tech"},
            {"ticker": "B", "raw_score": 3.0, "confidence": 0.29, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        # Both should be excluded due to confidence
        assert all(r["excluded"] for r in results)
        assert all("confidence" in r["exclusion_reason"] for r in results)
    
    def test_normalized_score_exactly_at_magnitude_threshold(self):
        engine = ScoringEngine()
        
        # For exact 0.5, we need raw = mean + or - 0.5*stddev
        data = [
            {"ticker": "A", "raw_score": 8.0, "confidence": 0.5, "sector": "tech"},
            {"ticker": "B", "raw_score": 10.0, "confidence": 0.5, "sector": "tech"},
            {"ticker": "C", "raw_score": 12.0, "confidence": 0.5, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        # Mean=10, variance=8/3, stddev~1.633
        # A: (8-10)/1.633 (magnitude > 0.5) -> not excluded
        # B: (10-10)/1.633 (magnitude < 0.5) -> excluded
        # C: (12-10)/1.633 (magnitude > 0.5) -> not excluded
        
        result_map = {r["ticker"]: r for r in results}
        assert result_map["A"]["excluded"] is False  # Magnitude passes
        assert result_map["B"]["excluded"] is True   # Magnitude fails
        assert result_map["C"]["excluded"] is False  # Magnitude passes
    
    def test_multiple_sectors_independent_normalization(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "A", "raw_score": 10.0, "confidence": 0.9, "sector": "tech"},
            {"ticker": "B", "raw_score": 20.0, "confidence": 0.9, "sector": "tech"},
            {"ticker": "C", "raw_score": 100.0, "confidence": 0.9, "sector": "finance"},
            {"ticker": "D", "raw_score": 200.0, "confidence": 0.9, "sector": "finance"},
        ]
        
        results = engine.process(data)
        
        result_map = {r["ticker"]: r for r in results}
        
        # Tech: mean=15, A gets negative normalized, B gets positive
        # Finance: mean=150, C gets negative normalized, D gets positive
        assert result_map["A"]["final_score"] < 0
        assert result_map["B"]["final_score"] > 0
        assert result_map["C"]["final_score"] < 0
        assert result_map["D"]["final_score"] > 0
        
        # Magnitudes should be similar within sectors
        tech_magnitude = abs(result_map["A"]["final_score"])
        finance_magnitude = abs(result_map["C"]["final_score"])
        
        assert abs(tech_magnitude - abs(result_map["B"]["final_score"])) < 0.01
        assert abs(finance_magnitude - abs(result_map["D"]["final_score"])) < 0.01


class TestScoringEngineInvalidInputs:
    
    def test_non_list_input_raises_type_error(self):
        engine = ScoringEngine()
        with pytest.raises(TypeError, match="must be a list"):
            engine.process("not a list")
    
    def test_dict_input_raises_type_error(self):
        engine = ScoringEngine()
        with pytest.raises(TypeError, match="must be a list"):
            engine.process({"ticker": "A", "raw_score": 1.0})
    
    def test_none_input_raises_type_error(self):
        engine = ScoringEngine()
        with pytest.raises(TypeError, match="must be a list"):
            engine.process(None)
    
    def test_invalid_schema_missing_ticker_raises_value_error(self):
        engine = ScoringEngine()
        data = [{"raw_score": 1.0, "confidence": 0.5, "sector": "tech"}]
        
        with pytest.raises(ValueError, match="schema"):
            engine.process(data)
    
    def test_invalid_schema_missing_raw_score_raises_value_error(self):
        engine = ScoringEngine()
        data = [{"ticker": "A", "confidence": 0.5, "sector": "tech"}]
        
        with pytest.raises(ValueError, match="schema"):
            engine.process(data)
    
    def test_invalid_schema_missing_confidence_raises_value_error(self):
        engine = ScoringEngine()
        data = [{"ticker": "A", "raw_score": 1.0, "sector": "tech"}]
        
        with pytest.raises(ValueError, match="schema"):
            engine.process(data)
    
    def test_invalid_schema_missing_sector_raises_value_error(self):
        engine = ScoringEngine()
        data = [{"ticker": "A", "raw_score": 1.0, "confidence": 0.5}]
        
        with pytest.raises(ValueError, match="schema"):
            engine.process(data)
    
    def test_invalid_schema_ticker_wrong_type_raises_value_error(self):
        engine = ScoringEngine()
        data = [{"ticker": 123, "raw_score": 1.0, "confidence": 0.5, "sector": "tech"}]
        
        with pytest.raises(ValueError, match="schema"):
            engine.process(data)
    
    def test_invalid_schema_raw_score_wrong_type_raises_value_error(self):
        engine = ScoringEngine()
        data = [{"ticker": "A", "raw_score": "bad", "confidence": 0.5, "sector": "tech"}]
        
        with pytest.raises(ValueError, match="schema"):
            engine.process(data)
    
    def test_invalid_schema_confidence_wrong_type_raises_value_error(self):
        engine = ScoringEngine()
        data = [{"ticker": "A", "raw_score": 1.0, "confidence": "bad", "sector": "tech"}]
        
        with pytest.raises(ValueError, match="schema"):
            engine.process(data)
    
    def test_invalid_schema_sector_wrong_type_raises_value_error(self):
        engine = ScoringEngine()
        data = [{"ticker": "A", "raw_score": 1.0, "confidence": 0.5, "sector": 123}]
        
        with pytest.raises(ValueError, match="schema"):
            engine.process(data)
    
    def test_confidence_above_range_raises_value_error(self):
        engine = ScoringEngine()
        data = [{"ticker": "A", "raw_score": 1.0, "confidence": 1.5, "sector": "tech"}]
        
        with pytest.raises(ValueError, match="schema"):
            engine.process(data)
    
    def test_confidence_below_range_raises_value_error(self):
        engine = ScoringEngine()
        data = [{"ticker": "A", "raw_score": 1.0, "confidence": -0.1, "sector": "tech"}]
        
        with pytest.raises(ValueError, match="schema"):
            engine.process(data)
    
    def test_confidence_exactly_zero_is_valid(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "A", "raw_score": 1.0, "confidence": 0.0, "sector": "tech"},
            {"ticker": "B", "raw_score": 2.0, "confidence": 0.0, "sector": "tech"},
        ]
        
        # Should not raise, but will be excluded (confidence < 0.3)
        results = engine.process(data)
        assert all(r["excluded"] for r in results)
    
    def test_confidence_exactly_one_is_valid(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "A", "raw_score": 1.0, "confidence": 1.0, "sector": "tech"},
            {"ticker": "B", "raw_score": 2.0, "confidence": 1.0, "sector": "tech"},
        ]
        
        # Should not raise
        results = engine.process(data)
        assert len(results) == 2


class TestScoringEngineOutputSchema:
    
    def test_output_has_all_required_fields(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "A", "raw_score": 1.0, "confidence": 0.8, "sector": "tech"},
            {"ticker": "B", "raw_score": 2.0, "confidence": 0.9, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        required_fields = {"ticker", "final_score", "sector", "excluded", "exclusion_reason"}
        for result in results:
            assert set(result.keys()) == required_fields
    
    def test_output_field_types_correct(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "A", "raw_score": 1.0, "confidence": 0.8, "sector": "tech"},
            {"ticker": "B", "raw_score": 3.0, "confidence": 0.1, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        for result in results:
            assert isinstance(result["ticker"], str)
            assert isinstance(result["final_score"], float)
            assert isinstance(result["sector"], str)
            assert isinstance(result["excluded"], bool)
            assert result["exclusion_reason"] is None or isinstance(result["exclusion_reason"], str)
    
    def test_excluded_false_has_null_exclusion_reason(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "A", "raw_score": 1.0, "confidence": 0.9, "sector": "tech"},
            {"ticker": "B", "raw_score": 3.0, "confidence": 0.9, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        for result in results:
            if not result["excluded"]:
                assert result["exclusion_reason"] is None
    
    def test_excluded_true_has_non_null_exclusion_reason(self):
        engine = ScoringEngine()
        data = [
            {"ticker": "A", "raw_score": 2.0, "confidence": 0.1, "sector": "tech"},
        ]
        
        results = engine.process(data)
        
        result = results[0]
        assert result["excluded"] is True
        assert result["exclusion_reason"] is not None
        assert isinstance(result["exclusion_reason"], str)
        assert len(result["exclusion_reason"]) > 0
    
    def test_final_score_is_float_not_int(self):
        engine = ScoringEngine()
        data = [{"ticker": "A", "raw_score": 5.0, "confidence": 0.8, "sector": "tech"}]
        
        results = engine.process(data)
        
        # Single item: final_score should be 0.0 (float)
        assert isinstance(results[0]["final_score"], float)
        assert results[0]["final_score"] == 0.0