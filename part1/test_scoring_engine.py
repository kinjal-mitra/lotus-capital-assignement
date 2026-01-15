import pytest
from scoring_engine import ScoringEngine


def test_invalid_input_schema_raises_type_error():
    engine = ScoringEngine()
    data = [{"ticker": "A", "raw_score": "bad", "confidence": 0.9, "sector": "tech"}]
    with pytest.raises(TypeError):
        engine.process(data)


def test_single_element_sector_raises_value_error():
    engine = ScoringEngine()
    data = [{"ticker": "A", "raw_score": 1.0, "confidence": 0.9, "sector": "tech"}]
    with pytest.raises(ValueError):
        engine.process(data)


def test_zero_variance_sector_raises_value_error():
    engine = ScoringEngine()
    data = [
        {"ticker": "A", "raw_score": 1.0, "confidence": 0.9, "sector": "tech"},
        {"ticker": "B", "raw_score": 1.0, "confidence": 0.8, "sector": "tech"},
    ]
    with pytest.raises(ValueError):
        engine.process(data)


def test_filtering_logic_ambiguity_raises_runtime_error():
    engine = ScoringEngine()
    data = [
        {"ticker": "A", "raw_score": 1.0, "confidence": 0.9, "sector": "tech"},
        {"ticker": "B", "raw_score": 2.0, "confidence": 0.8, "sector": "tech"},
    ]
    with pytest.raises(RuntimeError):
        engine.process(data)
