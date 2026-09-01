import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for generating executive reasoning, freight market narratives,
    and board recommendation briefs using Groq LLM API.
    """
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.client = None
        
        if self.api_key:
            try:
                from groq import Groq
                # Initialize Groq client securely from environment variable
                self.client = Groq(api_key=self.api_key)
                logger.info(f"Groq LLM Service initialized with model: {self.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")
                self.client = None
        else:
            logger.info("GROQ_API_KEY not configured. Running in deterministic heuristic mode.")

    def is_available(self) -> bool:
        return self.client is not None

    def generate_decision_narrative(
        self,
        recommendation: str,
        commodity: str,
        parcel_tonnage: float,
        origin_port_name: str,
        dest_port_name: str,
        recommended_vessel: str,
        current_spot: float,
        target_rate: float,
        expected_savings: float,
        savings_pct: float,
        optimal_day: int,
        confidence_pct: float
    ) -> str:
        """
        Generates a crisp 2-3 sentence executive rationale for the chartering decision.
        """
        if not self.is_available():
            if recommendation == "WAIT":
                return (
                    f"Forecast indicates freight rate dip towards ${target_rate:.2f}/MT within {optimal_day} days. "
                    f"Recommended action: Delay booking to Day {optimal_day} to capture projected net savings of "
                    f"${expected_savings:,.0f} USD ({savings_pct:.1f}% reduction) after inventory holding costs."
                )
            else:
                return (
                    f"Spot market rate at ${current_spot:.2f}/MT is favorable against impending upward pressure. "
                    f"Recommended action: Lock in spot charter immediately to hedge against rising freight rates "
                    f"for {recommended_vessel} on the {origin_port_name} to {dest_port_name} corridor."
                )

        try:
            prompt = f"""
You are the Chief Shipping & Chartering AI Advisor for Steel Authority of India Limited (SAIL), Ministry of Steel.
Generate a concise, professional 2-3 sentence executive recommendation summary for a bulk charter procurement decision:

- Action: {recommendation} (Target Booking Day: Day {optimal_day})
- Commodity: {commodity} ({parcel_tonnage:,.0f} MT)
- Route: {origin_port_name} to {dest_port_name}
- Recommended Vessel: {recommended_vessel}
- Spot Freight Rate: ${current_spot:.2f} / MT
- Target Booking Rate: ${target_rate:.2f} / MT
- Expected Net Savings: ${expected_savings:,.0f} USD ({savings_pct:.1f}% reduction)
- Model Confidence: {confidence_pct:.1f}%

Write an authoritative, procurement-grade explanation explaining why this decision is optimal, factoring in freight market trends, vessel draft feasibility, and inventory holding cost buffer. Do not use markdown bullet points. Keep it under 60 words.
"""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional maritime chartering decision engine for Indian Steel."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.2
            )
            narrative = response.choices[0].message.content.strip()
            return narrative if narrative else (
                f"Delaying charter booking to Day {optimal_day} captures downward sub-index movement, "
                f"yielding ${expected_savings:,.0f} USD ({savings_pct:.1f}%) in net landed freight savings."
            )
        except Exception as e:
            logger.warning(f"Groq narrative generation failed: {e}. Falling back to standard heuristic.")
            if recommendation == "WAIT":
                return (
                    f"Forecast indicates freight rate dip towards ${target_rate:.2f}/MT within {optimal_day} days. "
                    f"Delay booking to Day {optimal_day} to capture projected net savings of "
                    f"${expected_savings:,.0f} USD ({savings_pct:.1f}% reduction)."
                )
            else:
                return (
                    f"Lock in spot charter today at ${current_spot:.2f}/MT for {recommended_vessel} "
                    f"to mitigate anticipated upward freight movement."
                )

llm_service = LLMService()
