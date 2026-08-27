"""AI Service: the *only* place an LLM is called.

Produces a structured, enum-constrained recommendation. It never acts directly —
the Policy Engine (policy_engine.py) always gets the final say. If no API key is
configured, falls back to a deterministic rule-based mock so the pipeline is
demoable and testable without network access.

Uses Groq's OpenAI-compatible chat completions API with JSON-object response
mode for structured output.
"""

import json
from dataclasses import dataclass, field

from app.config import get_settings
from app.models.recovery_attempt import RecommendedAction
from groq import BadRequestError

settings = get_settings()

ALLOWED_ACTIONS = [a.value for a in RecommendedAction]

SYSTEM_PROMPT = f"""You are the reasoning component of a payment recovery agent.

Given context about a failed payment, recommend exactly one best next action.

You MUST return valid JSON and nothing else.

Return this exact JSON structure:

{{
  "recommended_action": "...",
  "confidence": 0.0,
  "reason": "...",
  "risk_flags": []
}}

The "recommended_action" MUST be exactly one of:
{ALLOWED_ACTIONS}

"confidence" MUST be a number between 0 and 1.

"reason" MUST be a short string.

"risk_flags" MUST be an array of strings.

Do not include markdown, code fences, explanations, or any text outside the JSON.

You only recommend an action. A downstream policy engine decides whether the action is allowed.
"""


@dataclass
class AIDecision:
    recommended_action: RecommendedAction
    confidence: float
    reason: str
    risk_flags: list[str] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "recommended_action": self.recommended_action.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "risk_flags": self.risk_flags,
        }


def _rule_based_fallback(context: dict) -> AIDecision:
    """Deterministic mock used when GROQ_API_KEY is not set."""
    attempt_number = context["attempt_history"]["attempt_count"] + 1
    amount = context["payment"]["amount"]

    if amount < settings.cost_to_recover_threshold:
        return AIDecision(
            recommended_action=RecommendedAction.STOP,
            confidence=0.95,
            reason="Amount is below the cost-to-recover threshold.",
            risk_flags=["low_value"],
        )

    if attempt_number > settings.max_recovery_attempts:
        return AIDecision(
            recommended_action=RecommendedAction.STOP,
            confidence=0.9,
            reason="Maximum recovery attempts already made.",
            risk_flags=["exhausted_attempts"],
        )

    if attempt_number == 1:
        return AIDecision(
            recommended_action=RecommendedAction.RETRY_PAYMENT,
            confidence=0.7,
            reason="First failure — a simple retry link is the least intrusive next step.",
            risk_flags=[],
        )

    if attempt_number == 2:
        return AIDecision(
            recommended_action=RecommendedAction.SEND_EMAIL,
            confidence=0.65,
            reason="Retry link unused — nudge via email with context on why payment failed.",
            risk_flags=["repeat_failure"],
        )

    return AIDecision(
        recommended_action=RecommendedAction.ESCALATE_MANUAL,
        confidence=0.55,
        reason="Multiple automated attempts failed — escalate for manual follow-up.",
        risk_flags=["repeat_failure", "needs_human"],
    )


def _call_llm(context: dict) -> AIDecision:
    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.ai_model,
        max_tokens=300,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(context)},
        ],
    )
    raw_text = response.choices[0].message.content
    data = json.loads(raw_text)

    action = data["recommended_action"]
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"LLM returned an out-of-enum action: {action}")

    return AIDecision(
        recommended_action=RecommendedAction(action),
        confidence=float(data.get("confidence", 0.5)),
        reason=str(data.get("reason", "")),
        risk_flags=list(data.get("risk_flags", [])),
    )


def get_recommended_action(context: dict) -> AIDecision:
    """Context assembly result -> structured AI recommendation.

    `context` is expected to carry: payment, customer, attempt_history
    (see recovery_engine.build_context).
    """
    if not settings.groq_api_key:
        return _rule_based_fallback(context)

    try:
        return _call_llm(context)
    except (json.JSONDecodeError, ValueError, KeyError, IndexError,BadRequestError):
        # Malformed/out-of-schema LLM output must never reach business logic —
        # fail safe to the deterministic path rather than guessing.
        
        return _rule_based_fallback(context)
