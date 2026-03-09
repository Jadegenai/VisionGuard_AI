"""Optional OpenAI integration for safety compliance summaries."""

from config.settings import settings


def generate_safety_summary(violations: list[dict]) -> str:
    """Use OpenAI to generate a natural-language safety compliance summary.

    Falls back to a simple template if OpenAI is not configured.
    """
    if not violations:
        return "No violations recorded today. All workers are PPE-compliant."

    # Build a text description of violations
    lines = []
    for v in violations:
        lines.append(
            f"- {v['violation_type']} at {v['timestamp']} ({v.get('location', 'Workshop')})"
        )
    violation_text = "\n".join(lines)

    if not settings.OPENAI_API_KEY:
        return _simple_summary(violations, violation_text)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a workplace safety officer. Summarise the PPE "
                        "violations below in 3-4 sentences. Be concise, professional, "
                        "and suggest corrective actions."
                    ),
                },
                {"role": "user", "content": violation_text},
            ],
            max_tokens=200,
        )
        return response.choices[0].message.content
    except Exception as e:
        return _simple_summary(violations, violation_text) + f"\n(AI summary unavailable: {e})"


def _simple_summary(violations, violation_text):
    total = len(violations)
    return (
        f"Safety Summary: {total} PPE violation(s) detected today.\n\n"
        f"Details:\n{violation_text}\n\n"
        "Action Required: Please ensure all workers wear mandatory PPE at all times."
    )
