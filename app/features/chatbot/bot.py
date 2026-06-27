import os
from typing import Iterator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI


DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GUARDRAIL_MODEL = os.environ.get("GEMINI_GUARDRAIL_MODEL", DEFAULT_MODEL)
ENABLE_GUARDRAIL = os.environ.get("ENABLE_GUARDRAIL", "true").lower() == "true"


SYSTEM_PROMPT = """\
You are FinanceDesk, a senior expert advisor whose ONLY domains are finance, \
business, and economics. You have deep fluency across:

- Corporate finance, valuation (DCF, multiples), capital structure, M&A
- Investing and markets: equities, fixed income, FX, commodities, derivatives,
  portfolio theory, risk management
- Accounting and financial statements (GAAP/IFRS) and financial analysis
- Economics: micro, macro, monetary and fiscal policy, market structure
- Business strategy, operations, management, organizational design
- Entrepreneurship, fundraising, unit economics, go-to-market
- Banking, lending, payments, fintech
- Personal finance, budgeting, retirement and tax concepts (general principles)

SCOPE RULES (strict):
1. Answer ONLY questions within finance, business, or economics.
2. If a request is outside these domains, politely decline in ONE sentence and
   steer the user back to finance/business. Do not partially answer off-topic parts.
3. A question is in-scope if its core intent is financial/business/economic, even
   when it touches another field (e.g. how export controls affect chip stocks).

STYLE:
- Be precise; define jargon briefly on first use.
- Show your work for calculations: formula, then numbers, then result.
- Lead with the bottom line, then reasoning and assumptions.
- State assumptions; flag where current/real data would be needed.
- Be honest about uncertainty and knowledge-cutoff limits (prices, rates, and
  regulations change).

NOT FINANCIAL ADVICE:
- You give educational information and analysis, not personalized investment,
  tax, or legal advice. For decisions tied to someone's specific situation, note
  briefly that they should consult a licensed professional - once per answer.
"""

_GUARDRAIL_PROMPT = """\
You are a topic classifier. Decide whether the user's latest message is related \
to finance, business, economics, accounting, investing, markets, banking, \
corporate strategy, management, or entrepreneurship.

A short follow-up ("why?", "explain more") is in-scope if the previous assistant \
turn was in-scope; use the context provided.

Respond with exactly one token: YES if in scope, NO if not. Output nothing else.

{context}User message: {message}"""

REFUSAL_MESSAGE = (
    "I can only help with finance, business, and economics questions. "
    "Is there something in those areas I can dig into for you?"
)


class FinanceBot:
    """A stateful, finance-only chat bot. One instance == one conversation."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        guardrail_model: str = GUARDRAIL_MODEL,
        use_guardrail: bool = ENABLE_GUARDRAIL,
    ) -> None:
        
        self.use_guardrail = use_guardrail
        self._messages: list[BaseMessage] = []

        llm = ChatGoogleGenerativeAI(model=model, temperature=0.3)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder("history"),
                ("human", "{input}"),
            ]
        )
        self._chain = prompt | llm

        guard_llm = ChatGoogleGenerativeAI(
            model=guardrail_model,
            temperature=0.0,
            max_tokens=5,
            thinking_budget=0,
        )
        self._guard = (
            ChatPromptTemplate.from_template(_GUARDRAIL_PROMPT)
            | guard_llm
            | StrOutputParser()
        )

    def _in_scope(self, message: str) -> bool:
        if not self.use_guardrail:
            return True
        context = ""
        if self._messages:
            last = self._messages[-1].content
            context = f"Previous assistant turn: {str(last)[:500]}\n\n"
        try:
            verdict = self._guard.invoke(
                {"context": context, "message": message}
            ).strip().upper()
        except Exception:
            return True 
        if not verdict:
            return True
        return not verdict.startswith("N") 

    def _remember(self, user: str, assistant: str) -> None:
        self._messages.append(HumanMessage(user))
        self._messages.append(AIMessage(assistant))


    def ask(self, message: str) -> str:
        
        if not self._in_scope(message):
            self._remember(message, REFUSAL_MESSAGE)
            return REFUSAL_MESSAGE
        resp = self._chain.invoke({"history": self._messages, "input": message})
        self._remember(message, resp.content)
        return resp.content

    def stream(self, message: str) -> Iterator[str]:

        if not self._in_scope(message):
            self._remember(message, REFUSAL_MESSAGE)
            yield REFUSAL_MESSAGE
            return
        parts: list[str] = []
        for chunk in self._chain.stream({"history": self._messages, "input": message}):
            if chunk.content:
                parts.append(chunk.content)
                yield chunk.content
        self._remember(message, "".join(parts))

    def reset(self) -> None:
        self._messages.clear()