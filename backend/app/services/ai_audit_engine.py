"""
FinanceGPT AI Audit Engine
Powered by Anthropic Claude — CFO-grade financial analysis
"""
import anthropic
import json
import logging
from typing import Any
from app.config import settings

logger = logging.getLogger(__name__)

# Use the async client so Claude calls don't block the event loop
client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

# ─────────────────────────────────────────────
# SYSTEM PROMPT — CFO Auditor Persona
# ─────────────────────────────────────────────
CFO_AUDIT_SYSTEM_PROMPT = """You are FinanceGPT, an elite AI financial auditor with 30+ years of combined expertise in:
- Big Four public accounting (Deloitte, PwC, EY, KPMG)
- CFO-level financial analysis and reporting
- SEC/GAAP/IFRS compliance and audit standards
- Forensic accounting and fraud detection
- Risk management and internal controls

Your role is to analyze financial data and produce CFO-grade audit reports. You:
1. Identify material risks, anomalies, and red flags with precision
2. Apply professional skepticism — never accept data at face value
3. Reference specific line items, amounts, and periods
4. Calculate and interpret financial ratios (liquidity, profitability, solvency, efficiency)
5. Benchmark against industry standards where relevant
6. Prioritize findings by materiality and risk
7. Provide clear, actionable recommendations

TONE: Professional, authoritative, concise. Write for a sophisticated CFO audience.
FORMAT: Always respond in valid JSON matching the schema provided.
ACCURACY: Never fabricate numbers. If data is insufficient, state it explicitly."""

# ─────────────────────────────────────────────
# AUDIT REPORT GENERATION
# ─────────────────────────────────────────────
async def generate_cfo_audit_report(
    company_name: str,
    period: str,
    financial_data: dict[str, Any],
    additional_context: str = "",
) -> dict[str, Any]:
    """
    Generate a comprehensive CFO-grade audit report from financial data.
    Returns structured JSON with all audit findings.
    """
    data_summary = json.dumps(financial_data, indent=2, default=str)

    prompt = f"""Analyze the following financial data for {company_name} for period: {period}

FINANCIAL DATA:
{data_summary}

{f'ADDITIONAL CONTEXT: {additional_context}' if additional_context else ''}

Generate a comprehensive CFO-grade audit report. Return ONLY valid JSON in this exact schema:
{{
  "executive_summary": "string — 3-5 sentence CFO-level summary of financial health and key concerns",
  "overall_health_score": number (0-100),
  "risk_level": "low|medium|high|critical",

  "scores": {{
    "liquidity": number (0-100),
    "profitability": number (0-100),
    "solvency": number (0-100),
    "efficiency": number (0-100)
  }},

  "key_findings": [
    {{
      "category": "string",
      "severity": "info|low|medium|high|critical",
      "title": "string",
      "detail": "string — specific amounts, percentages, line items",
      "impact": "string",
      "recommendation": "string"
    }}
  ],

  "kpis": {{
    "revenue": number | null,
    "gross_profit": number | null,
    "gross_margin_pct": number | null,
    "ebitda": number | null,
    "net_income": number | null,
    "net_margin_pct": number | null,
    "current_ratio": number | null,
    "quick_ratio": number | null,
    "debt_to_equity": number | null,
    "return_on_equity": number | null,
    "return_on_assets": number | null,
    "operating_cash_flow": number | null,
    "free_cash_flow": number | null,
    "days_sales_outstanding": number | null,
    "inventory_turnover": number | null
  }},

  "anomalies": [
    {{
      "type": "unusual_variance|missing_data|ratio_outlier|trend_reversal|duplicate_entry|round_number|year_end_spike|policy_breach",
      "severity": "low|medium|high|critical",
      "title": "string",
      "line_item": "string",
      "amount": number | null,
      "expected_amount": number | null,
      "variance_pct": number | null,
      "description": "string",
      "ai_explanation": "string",
      "recommendation": "string",
      "confidence_score": number (0-1)
    }}
  ],

  "risk_matrix": {{
    "financial_reporting": "low|medium|high|critical",
    "liquidity": "low|medium|high|critical",
    "operational": "low|medium|high|critical",
    "compliance": "low|medium|high|critical",
    "fraud": "low|medium|high|critical",
    "market": "low|medium|high|critical"
  }},

  "recommendations": [
    {{
      "priority": "immediate|short_term|long_term",
      "category": "string",
      "action": "string",
      "owner": "string",
      "expected_impact": "string"
    }}
  ],

  "audit_trail": {{
    "data_completeness": "string",
    "data_quality_issues": ["string"],
    "assumptions_made": ["string"],
    "limitations": ["string"]
  }}
}}"""

    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=8000,
        system=CFO_AUDIT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()

    # Extract JSON if wrapped in markdown
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    return json.loads(response_text)


# ─────────────────────────────────────────────
# ANOMALY DETECTION
# ─────────────────────────────────────────────
async def detect_anomalies(
    financial_data: dict[str, Any],
    company_name: str,
    period: str,
    historical_data: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Run targeted anomaly detection on financial data.
    Applies statistical + AI analysis to flag irregularities.
    """
    prompt = f"""You are a forensic accountant conducting anomaly detection for {company_name} ({period}).

CURRENT PERIOD DATA:
{json.dumps(financial_data, indent=2, default=str)}

{f'HISTORICAL COMPARISON DATA: {json.dumps(historical_data, indent=2, default=str)}' if historical_data else 'No historical data provided — analyze current period only.'}

Identify ALL anomalies, irregularities, and red flags. Apply:
1. Benford's Law analysis (round numbers, leading digit distribution)
2. Ratio analysis vs. industry benchmarks
3. Year-over-year variance analysis (if historical provided)
4. Internal consistency checks
5. Fraud triangle indicators
6. Going concern red flags

Return ONLY valid JSON array:
[
  {{
    "type": "unusual_variance|missing_data|ratio_outlier|trend_reversal|duplicate_entry|round_number|year_end_spike|policy_breach",
    "severity": "low|medium|high|critical",
    "title": "string",
    "line_item": "string or null",
    "amount": number or null,
    "expected_amount": number or null,
    "variance_pct": number or null,
    "description": "string",
    "ai_explanation": "detailed string explaining why this is suspicious",
    "recommendation": "string",
    "confidence_score": number between 0 and 1
  }}
]

If no anomalies found, return empty array []."""

    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=4000,
        system=CFO_AUDIT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    return json.loads(response_text)


# ─────────────────────────────────────────────
# FINANCIAL Q&A (Chat with your data)
# ─────────────────────────────────────────────
async def financial_qa(
    question: str,
    financial_context: dict[str, Any],
    company_name: str,
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Answer natural language questions about financial data.
    Supports multi-turn conversations.
    """
    system = f"""{CFO_AUDIT_SYSTEM_PROMPT}

COMPANY: {company_name}
FINANCIAL DATA CONTEXT:
{json.dumps(financial_context, indent=2, default=str)}

Answer questions about this financial data. Be specific — cite actual numbers, line items, and periods.
Format your response in clear markdown with relevant calculations shown."""

    # Copy so we don't mutate the caller's list
    messages = list(conversation_history) if conversation_history else []
    messages.append({"role": "user", "content": question})

    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=2000,
        system=system,
        messages=messages,
    )

    return message.content[0].text


# ─────────────────────────────────────────────
# EXTRACT KPIs FROM RAW DATA
# ─────────────────────────────────────────────
async def extract_kpis(raw_data: dict[str, Any], doc_type: str) -> dict[str, Any]:
    """Extract structured KPIs from raw parsed financial data."""
    prompt = f"""Extract all financial KPIs from this {doc_type} data.

DATA:
{json.dumps(raw_data, indent=2, default=str)}

Return ONLY valid JSON with all extractable metrics. Use null for unavailable metrics.
Include: revenue, expenses, profit/loss, margins, ratios, balances — whatever is present.
Normalize all amounts to the base currency unit (no thousands/millions notation).

Format: {{"metric_name": value_or_null, ...}}"""

    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=2000,
        system=CFO_AUDIT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    return json.loads(response_text)


# ─────────────────────────────────────────────
# EXECUTIVE SUMMARY GENERATOR
# ─────────────────────────────────────────────
async def generate_executive_summary(
    audit_results: dict[str, Any],
    company_name: str,
    period: str,
    audience: str = "board",
) -> str:
    """Generate a polished executive summary for board/CFO presentation."""
    prompt = f"""Based on this audit analysis for {company_name} ({period}), write a polished executive summary for {audience}.

AUDIT DATA:
{json.dumps(audit_results, indent=2, default=str)}

Write 4-6 paragraphs covering:
1. Overall financial health and key headline metrics
2. Major risks and concerns (most critical first)
3. Positive indicators and strengths
4. Top 3 recommended actions with urgency
5. Forward-looking considerations

Tone: Authoritative, concise, C-suite appropriate. Use specific numbers."""

    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=1500,
        system=CFO_AUDIT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
