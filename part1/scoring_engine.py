from typing import List, Dict, Any
import math


class ScoringEngine:
    """    
    Implements exact logic from YAML specification.
    """
    
    def process(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """        
        Args:
            predictions: List of prediction dictionaries matching input schema
            
        Returns:
            List of scored predictions matching output schema
            
        Raises:
            TypeError: If predictions is not a list
            ValueError: If any prediction doesn't match input schema
        """
        # Input validation
        if not isinstance(predictions, list):
            raise TypeError("Input 'predictions' must be a list")
        
        # Handle empty input
        if len(predictions) == 0:
            return []
        
        # Validate all items match schema
        for idx, item in enumerate(predictions):
            if not self._matches_input_schema(item):
                raise ValueError(f"Item at index {idx} does not match input schema")
        
        # Group predictions by sector
        sectors: Dict[str, List[Dict[str, Any]]] = {}
        for item in predictions:
            sector = item["sector"]
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(item)
        
        # Process each sector
        results = []
        for sector, items in sectors.items():
            sector_results = self._process_sector(sector, items)
            results.extend(sector_results)
        
        return results
    
    def _process_sector(self, sector: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """       
        Args:
            sector: Sector name
            items: All predictions in this sector
            
        Returns:
            List of processed predictions for this sector
        """
        # Calculate sector statistics for normalization
        raw_scores = [item["raw_score"] for item in items]
        sector_mean = sum(raw_scores) / len(raw_scores)
        
        # Handle edge case: single item or zero variance
        if len(items) == 1:
            # Single item: standard deviation is undefined
            # Set normalized_score to 0.0 (no deviation from mean)
            sector_stddev = 1.0  # Prevents division by zero
            use_zero_normalization = True
        else:
            # Calculate population standard deviation
            variance = sum((score - sector_mean) ** 2 for score in raw_scores) / len(raw_scores)
            
            if variance == 0:
                # All scores identical: no variation to normalize
                sector_stddev = 1.0  # Prevents division by zero
                use_zero_normalization = True
            else:
                sector_stddev = math.sqrt(variance)
                use_zero_normalization = False
        
        # Process each item in sector
        sector_results = []
        for item in items:
            result = self._process_item(
                item, 
                sector, 
                sector_mean, 
                sector_stddev,
                use_zero_normalization
            )
            sector_results.append(result)
        
        return sector_results
    
    def _process_item(self, item: Dict[str, Any], sector: str,sector_mean: float,sector_stddev: float,use_zero_normalization: bool) -> Dict[str, Any]:
        """       
        Args:
            item: Input prediction
            sector: Sector name
            sector_mean: Mean of raw scores in sector
            sector_stddev: Standard deviation of raw scores in sector
            use_zero_normalization: Whether to force normalized_score to 0.0
            
        Returns:
            Processed prediction matching output schema
        """
        # Step 1: Normalization (z-score)
        if use_zero_normalization:
            normalized_score = 0.0
        else:
            normalized_score = (item["raw_score"] - sector_mean) / sector_stddev
        
        # Step 2: Confidence adjustment
        adjusted_score = normalized_score * item["confidence"]
        
        # Step 3: Filtering
        excluded = False
        exclusion_reason = None
        
        confidence_check = item["confidence"] >= 0.3
        magnitude_check = abs(normalized_score) >= 0.5
        
        # AND logic: both conditions must be true to pass
        if not (confidence_check and magnitude_check):
            excluded = True
            reasons = []
            if not confidence_check:
                reasons.append(f"confidence {item['confidence']} < 0.3")
            if not magnitude_check:
                reasons.append(f"abs(normalized_score) {abs(normalized_score):.4f} < 0.5")
            exclusion_reason = "; ".join(reasons)
        
        # Step 4: Output bounds clipping
        final_score = max(-3.0, min(3.0, adjusted_score))
        
        # Construct output matching schema
        return {
            "ticker": item["ticker"],
            "final_score": final_score,
            "sector": sector,
            "excluded": excluded,
            "exclusion_reason": exclusion_reason
        }
    
    def _matches_input_schema(self, item: Any) -> bool:
        """        
        Input schema:
            - ticker: string
            - raw_score: float
            - confidence: float (0.0 to 1.0)
            - sector: string
        
        Args:
            item: Item to validate
            
        Returns:
            True if item matches schema, False otherwise
        """
        if not isinstance(item, dict):
            return False
        
        # Check all required keys exist
        required_keys = {"ticker", "raw_score", "confidence", "sector"}
        if not required_keys.issubset(item.keys()):
            return False
        
        # Validate types
        try:
            ticker = item["ticker"]
            raw_score = item["raw_score"]
            confidence = item["confidence"]
            sector = item["sector"]
            
            # Type checks
            if not isinstance(ticker, str):
                return False
            if not isinstance(raw_score, (int, float)):
                return False
            if not isinstance(confidence, (int, float)):
                return False
            if not isinstance(sector, str):
                return False
            
            # Confidence bounds check
            if not (0.0 <= confidence <= 1.0):
                return False
            
            return True
            
        except (KeyError, TypeError):
            return False