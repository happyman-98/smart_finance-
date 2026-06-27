# services/chat_service.py
# Drop this into your backend/services/ folder alongside auth_service.py

import os
from typing import Iterator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

DEFAULT_MODEL      = os.environ.get("GEMINI_MODEL",           "gemini-2.5-flash")
GUARDRAIL_MODEL    = os.environ.get("GEMINI_GUARDRAIL_MODEL", DEFAULT_MODEL)
ENABLE_GUARDRAIL   = os.environ.get("ENABLE_GUARDRAIL",       "true").lower() == "true"

# ── System prompt — injected at call time so live user data is always fresh ──
BASE_SYSTEM = """\
You are SmartAssist, a senior personal-finance AI embedded inside FinanceOS.
Your PRIMARY job is to help {name} understand and improve their finances using
the live dashboard data below. You also have deep fluency in general finance,
investing, accounting, economics, and business strategy.

── LIVE DASHBOARD DATA ──────────────────────────────────────────────────────
Net Balance       : {net_balance}
Total Income      : {total_income}
Total Expenses    : {total_expense}
Monthly Income    : {monthly_income}
Monthly Sav. Goal : {monthly_savings_goal}
Spending Breakdown: {by_category}
─────────────────────────────────────────────────────────────────────────────

STYLE:
- Lead with the bottom line, then reasoning.
- Use real numbers from the data above whenever relevant.
- Be concise (≤ 120 words) unless the user asks for detail.
- Define jargon briefly on first use.
- Be warm but professional.

NOT FINANCIAL ADVICE: you provide educational analysis. For decisions tied to
the user's specific legal or tax situation, note once that they should consult
a licensed professional.
"""

_GUARDRAIL_PROMPT = """\
You are a topic classifier. Decide whether the user's latest message is related \
to finance, business, economics, accounting, investing, markets, banking, \
corporate strategy, management, entrepreneurship, personal budgeting, \
account balance, transactions, spending, income, savings, goals, \
OR is a follow-up to the previous assistant turn below.

Also answer YES for any question about the user's own financial data such as \
"what is my balance", "how much did I spend", "show my transactions", etc.

Respond with exactly one token: YES if in scope, NO if not.

{context}User message: {message}"""

REFUSAL_MESSAGE = (
    "I can only help with finance, business, and economics questions. "
    "Is there something in those areas I can dig into for you?"
)


class FinanceBot:
    """One instance per user session (keyed by user_id in the route)."""

    def __init__(
        self,
        model:           str  = DEFAULT_MODEL,
        guardrail_model: str  = GUARDRAIL_MODEL,
        use_guardrail:   bool = ENABLE_GUARDRAIL,
    ) -> None:
        self.use_guardrail = use_guardrail
        self._messages: list[BaseMessage] = []

        llm    = ChatGoogleGenerativeAI(model=model, temperature=0.3)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system}"),          # ← dynamic, injected per-call
            MessagesPlaceholder("history"),
            ("human", "{input}"),
        ])
        self._chain = prompt | llm

        guard_llm    = ChatGoogleGenerativeAI(
            model=guardrail_model, temperature=0.0, max_tokens=5, thinking_budget=0
        )
        self._guard  = (
            ChatPromptTemplate.from_template(_GUARDRAIL_PROMPT)
            | guard_llm
            | StrOutputParser()
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    def _in_scope(self, message: str) -> bool:
        if not self.use_guardrail:
            return True
        context = ""
        if self._messages:
            last    = self._messages[-1].content
            context = f"Previous assistant turn: {str(last)[:500]}\n\n"
        try:
            verdict = self._guard.invoke(
                {"context": context, "message": message}
            ).strip().upper()
        except Exception:
            return True
        return not verdict.startswith("N")

    def _remember(self, user: str, assistant: str) -> None:
        self._messages.append(HumanMessage(user))
        self._messages.append(AIMessage(assistant))

    def _build_system(self, ctx: dict) -> str:
        fmt = lambda v: f"${float(v):,.2f}" if v is not None else "not set"
        cat = ", ".join(f"{k}: ${v:,.2f}" for k, v in (ctx.get("by_category") or {}).items()) or "no data"
        return BASE_SYSTEM.format(
            name                 = ctx.get("name", "User"),
            net_balance          = fmt(ctx.get("net_balance")),
            total_income         = fmt(ctx.get("total_income")),
            total_expense        = fmt(ctx.get("total_expense")),
            monthly_income       = fmt(ctx.get("monthly_income")),
            monthly_savings_goal = fmt(ctx.get("monthly_savings_goal")),
            by_category          = cat,
        )

    # ── public API ───────────────────────────────────────────────────────────

    def stream(self, message: str, ctx: dict) -> Iterator[str]:
        """Stream response chunks. ctx = live dashboard data dict."""
        if not self._in_scope(message):
            self._remember(message, REFUSAL_MESSAGE)
            yield REFUSAL_MESSAGE
            return

        system = self._build_system(ctx)
        parts: list[str] = []
        for chunk in self._chain.stream(
            {"system": system, "history": self._messages, "input": message}
        ):
            if chunk.content:
                parts.append(chunk.content)
                yield chunk.content
        self._remember(message, "".join(parts))

    def reset(self) -> None:
        self._messages.clear()