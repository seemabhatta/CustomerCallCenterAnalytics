"""
Prediction Validator - Validates predictions against actual outcomes.

Implements feedback loop to improve prediction accuracy and pattern confidence.
"""
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

from .predictive_knowledge_extractor import get_predictive_knowledge_extractor
from .knowledge_types import Prediction

logger = logging.getLogger(__name__)


class PredictionValidator:
    """
    Validates predictions against actual outcomes.

    Provides feedback loop to improve system prediction accuracy.
    """

    def __init__(self):
        self.knowledge_extractor = get_predictive_knowledge_extractor()

    async def validate_prediction_outcome(self,
                                        prediction_id: str,
                                        actual_outcome: bool,
                                        outcome_context: Dict[str, Any]) -> None:
        """
        Validate a prediction with actual outcome.

        Args:
            prediction_id: ID of the prediction to validate
            actual_outcome: Whether the prediction came true
            outcome_context: Context about the actual outcome

        Raises:
            Exception: When validation fails (NO FALLBACK)
        """
        # NO FALLBACK: If prediction validation fails, operation fails
        await self.knowledge_extractor.validate_prediction(prediction_id, actual_outcome)

        # Log validation for learning
        logger.info(f"✅ Validated prediction {prediction_id}: {'SUCCESS' if actual_outcome else 'FAILED'}")
        logger.info(f"   Context: {outcome_context}")

    async def validate_customer_risk_prediction(self,
                                              customer_id: str,
                                              predicted_risk: str,
                                              actual_outcome: str) -> None:
        """
        Validate customer risk predictions against actual outcomes.

        Args:
            customer_id: Customer whose risk was predicted
            predicted_risk: What was predicted (e.g., 'delinquency', 'churn')
            actual_outcome: What actually happened
        """
        # Get predictions for this customer
        predictions = await self.knowledge_extractor.get_predictions_for_entity("Customer", customer_id)

        # Find matching risk predictions
        for prediction in predictions:
            if predicted_risk.lower() in prediction.predicted_event.lower():
                outcome_matches = actual_outcome.lower() in prediction.predicted_event.lower()
                await self.validate_prediction_outcome(
                    prediction.prediction_id,
                    outcome_matches,
                    {
                        'customer_id': customer_id,
                        'predicted_risk': predicted_risk,
                        'actual_outcome': actual_outcome,
                        'validation_type': 'customer_risk'
                    }
                )

    async def validate_advisor_performance_prediction(self,
                                                    advisor_id: str,
                                                    predicted_improvement: str,
                                                    actual_performance: Dict[str, Any]) -> None:
        """
        Validate advisor performance predictions.

        Args:
            advisor_id: Advisor whose performance was predicted
            predicted_improvement: What improvement was predicted
            actual_performance: Actual performance metrics
        """
        predictions = await self.knowledge_extractor.get_predictions_for_entity("Advisor", advisor_id)

        for prediction in predictions:
            if predicted_improvement.lower() in prediction.predicted_event.lower():
                # Determine if prediction came true based on performance metrics
                outcome = self._evaluate_advisor_performance_outcome(prediction, actual_performance)
                await self.validate_prediction_outcome(
                    prediction.prediction_id,
                    outcome,
                    {
                        'advisor_id': advisor_id,
                        'predicted_improvement': predicted_improvement,
                        'actual_performance': actual_performance,
                        'validation_type': 'advisor_performance'
                    }
                )

    def _evaluate_advisor_performance_outcome(self,
                                            prediction: Prediction,
                                            actual_performance: Dict[str, Any]) -> bool:
        """
        Evaluate if advisor performance prediction came true.

        Args:
            prediction: The prediction that was made
            actual_performance: Actual performance metrics

        Returns:
            True if prediction was accurate
        """
        # Simple evaluation logic - can be enhanced
        predicted_event = prediction.predicted_event.lower()

        if 'improvement' in predicted_event:
            # Check if any performance metrics improved
            return any(score > 0.7 for score in actual_performance.values() if isinstance(score, (int, float)))

        if 'coaching' in predicted_event:
            # Check if coaching was actually needed/provided
            return actual_performance.get('coaching_sessions', 0) > 0

        return False

    async def update_pattern_with_outcome(self,
                                        pattern_id: str,
                                        outcome_data: Dict[str, Any]) -> None:
        """
        Update a pattern with new outcome evidence.

        Args:
            pattern_id: Pattern to update
            outcome_data: Data about the actual outcome
        """
        # NO FALLBACK: If pattern update fails, operation fails
        await self.knowledge_extractor.update_pattern_evidence(pattern_id, outcome_data)
        logger.info(f"📊 Updated pattern {pattern_id} with outcome evidence")

    async def batch_validate_expired_predictions(self) -> Dict[str, Any]:
        """
        Validate predictions that have expired without outcomes.

        Returns:
            Summary of validation results
        """
        # This would typically query the database for expired predictions
        # For now, return summary structure
        logger.info("🔄 Running batch validation of expired predictions")

        return {
            'validated_count': 0,
            'successful_predictions': 0,
            'failed_predictions': 0,
            'accuracy_rate': 0.0,
            'validation_timestamp': datetime.utcnow().isoformat()
        }


# Global instance
_prediction_validator = None

def get_prediction_validator() -> PredictionValidator:
    """Get the global prediction validator instance."""
    global _prediction_validator
    if _prediction_validator is None:
        _prediction_validator = PredictionValidator()
    return _prediction_validator