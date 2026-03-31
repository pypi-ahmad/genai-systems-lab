from shared.llm.gemini import generate_text


MODEL = "gemini-3-flash-preview"


def generate_report(analysis: str) -> str:
    prompt = f"""You are a financial report writer. You are given an analyst's findings about a company's financial data.

## Analyst Findings
{analysis}

Write a concise financial report with exactly these three sections:

### Summary
A brief executive summary of the overall financial position in 2-3 sentences.

### Key Insights
Bullet points of the most important findings. Each bullet must reference a specific metric or trend from the analysis.

### Recommendations
Actionable next steps based on the insights. Be specific and practical.

Rules:
- Use only information from the analyst findings above. Do NOT invent data.
- Keep the report under 300 words.
- Use plain, professional language suitable for stakeholders."""

    return generate_text(prompt, MODEL)