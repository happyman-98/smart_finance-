<div align="center">

<img src="assets/logo.png" alt="FinanceOS logo" width="96" height="96" />

# FinanceOS

### Your money, on autopilot — scan receipts, track every rupee, and ask an AI that *actually knows your numbers*.

A full-stack personal-finance platform with a built-in **SmartAssist** AI advisor and **multi-engine receipt OCR**.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.137-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.x-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![LangChain](https://img.shields.io/badge/LangChain-1.x-1C3C3C)](https://www.langchain.com/)
[![SQLite](https://img.shields.io/badge/SQLite-SQLAlchemy-003B57?logo=sqlite&logoColor=white)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#-license)

[Features](#-features) · [Demo](#-quick-demo) · [Quickstart](#-quickstart) · [Architecture](#-architecture) · [API](#-api-reference) · [Roadmap](#-roadmap)

</div>

---

## 🎯 The Problem

People don't budget because budgeting is *tedious*. You have to type in every expense, mentally categorize it, remember to do it, and then squint at spreadsheets to understand what your spending actually means. Most finance apps stop at "here's a pie chart." None of them can answer **"can I afford this?"** in plain English using *your* data.

## ✨ The Solution

**FinanceOS** removes the friction at both ends:

1. **📸 Snap a receipt** → AI extracts merchant, total, tax, and line items automatically.
2. **💬 Ask a question** → SmartAssist answers using your *live* balance, income, and spending breakdown — not generic advice.

No manual entry. No spreadsheet archaeology. Just point, ask, and decide.

---

## 🚀 Features

| | Feature | What it does |
|---|---|---|
| 🤖 | **SmartAssist AI Advisor** | A Gemini-powered chatbot that streams answers grounded in your *live* dashboard data. Includes a topic-guardrail so it stays on finance. |
| 📸 | **Multi-Engine Receipt OCR** | Upload a receipt → structured JSON (merchant, total, date, currency, line items, taxes). Pluggable engines: **Gemini Vision**, **Ollama (local)**, or **Tesseract** — with automatic retries on rate limits. |
| 📊 | **Analytics Dashboard** | Net balance, income vs. expense, spending-by-category, and 12-month trends — computed on the fly. |
| 🎯 | **Savings Goals** | Set targets with deadlines, deposit toward them, and track progress. |
| 🔐 | **Secure Auth** | JWT sessions with bcrypt-hashed passwords (SHA-256 pre-hash to dodge bcrypt's 72-byte limit). |
| 📱 | **SMS Spend Alerts** | Twilio integration warns you when monthly spending crosses a threshold. |
| 💸 | **Transactions** | Full CRUD, scoped per-user, with categories, merchants, and types. |

---

## 🎬 Quick Demo

A seeded demo account ships with realistic data — log in instantly:

```
📧  hello@gmail.com
🔑  demo1234
```

> Run `python backend/seed_demo_data.py` to (re)create it.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI · Uvicorn · SQLAlchemy 2.0 · SQLite |
| **AI / ML** | Google Gemini (`google-genai`) · LangChain (`langchain-google-genai`) · Tesseract OCR · Ollama Vision |
| **Auth** | python-jose (JWT) · passlib · bcrypt |
| **Integrations** | Twilio (SMS) · SMTP (email) |
| **Frontend** | Vanilla HTML5 / CSS3 / JavaScript (zero-build, SSE streaming) |

---

## ⚡ Quickstart

### Prerequisites
- Python **3.12+**
- A [Google Gemini API key](https://aistudio.google.com/apikey) (starts with `AIza…`) — *only needed for the Gemini OCR engine and SmartAssist chat*
- *(Optional)* [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for the offline OCR engine

### 1. Clone & install

```bash
git clone <your-repo-url> finance-os
cd finance-os

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
# Required for SmartAssist chat + Gemini OCR engine
GOOGLE_API_KEY="AIza...your_real_gemini_key..."

# Recommended — used to sign JWTs (set a long random string in production)
SECRET_KEY="change-me-to-a-long-random-secret"

# Optional — SMS alerts
TWILIO_ACCOUNT_SID=""
TWILIO_AUTH_TOKEN=""
TWILIO_PHONE_NUMBER=""

# Optional — email alerts
SMTP_PASS=""
```

> 💡 **No Gemini key?** The **Tesseract** engine runs OCR fully offline — pick it in the upload UI or pass `engine=tesseract`.

### 3. Run the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The DB tables are created automatically on first launch. Interactive API docs live at **http://localhost:8000/docs**.

### 4. Open the frontend

The frontend expects the API at `http://localhost:8000`. Serve the static files:

```bash
cd frontend
python -m http.server 5500
```

Then open **http://localhost:5500/login.html** and log in with the demo account above. 🎉

---

## 🏗 Architecture

```
                ┌─────────────────────────────┐
                │   Frontend (HTML/CSS/JS)     │
                │  login · dashboard · chat    │
                └──────────────┬──────────────┘
                          REST + SSE (Bearer JWT)
                               │
                ┌──────────────▼──────────────┐
                │      FastAPI  (/api/*)       │
                │                              │
                │ auth · transactions · goals  │
                │  analytics · upload · chat   │
                └──┬───────┬───────┬───────┬───┘
                   │       │       │       │
            ┌──────▼─┐ ┌───▼────┐ ┌▼──────┐ ┌▼──────────┐
            │ JWT +  │ │ OCR    │ │Finance│ │SQLAlchemy │
            │ bcrypt │ │ engines│ │ Bot   │ │  → SQLite │
            └────────┘ └───┬────┘ └───┬───┘ └───────────┘
                           │          │
                  Gemini / Ollama /   Gemini via
                     Tesseract        LangChain
```

```
smart_finance-/
├── backend/
│   ├── main.py                 # FastAPI app + router wiring
│   ├── models/
│   │   ├── database.py         # engine, session, Base
│   │   └── schemas.py          # ORM tables + Pydantic models
│   ├── routes/                 # auth · transactions · goals · analytics · upload · chat · alerts
│   ├── services/
│   │   ├── auth_service.py     # hashing, JWT, current-user dependency
│   │   ├── ocr_scanner.py      # Gemini / Ollama / Tesseract engines
│   │   └── chat_service.py     # SmartAssist FinanceBot + guardrail
│   └── seed_demo_data.py       # demo account + sample data
├── frontend/                   # login + dashboard (vanilla JS)
├── app/                        # standalone feature prototypes (CLI bot, charts, SMS)
└── requirements.txt
```

---

## 📡 API Reference

All routes are prefixed with `/api`. Protected routes require an `Authorization: Bearer <token>` header.

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create account → returns JWT + user |
| `POST` | `/auth/login` | Log in → returns JWT + user |
| `PUT` | `/auth/me` | Update monthly income / savings goal |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/transactions/` | List your transactions (newest first) |
| `POST` | `/transactions/` | Create a transaction |
| `DELETE` | `/transactions/{id}` | Delete a transaction |

### Goals
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/goals/` | List savings goals |
| `POST` | `/goals/` | Create a goal |
| `PATCH` | `/goals/{id}/deposit` | Deposit toward a goal |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/analytics/summary` | Net balance, totals, by-category, monthly trends |

### Receipt OCR
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload-receipt` | Upload image (`engine=gemini\|ollama\|tesseract`) → extracted fields |
| `POST` | `/upload-receipt/confirm` | Save a reviewed receipt as a transaction |

### SmartAssist Chat
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat/stream` | Stream an AI answer (Server-Sent Events) grounded in your data |
| `POST` | `/chat/reset` | Clear conversation memory |

---

## 🧠 How SmartAssist Works

Every chat request rebuilds a **live context** from your database — net balance, income, expenses, and spending by category — and injects it into the system prompt. So when you ask *"how much can I save this month?"*, the answer uses **your real numbers**, not a generic template.

A lightweight **guardrail model** classifies each message first: off-topic questions get a polite redirect, keeping the assistant focused on finance. Responses stream token-by-token over SSE for a live-typing feel.

---

## 🗺 Roadmap

- [ ] Recurring transactions & subscription detection
- [ ] Budget envelopes with rollover
- [ ] CSV / bank-statement import
- [ ] ML-based spending forecasts (XGBoost groundwork already in deps)
- [ ] Mobile-first PWA
- [ ] Multi-currency support

---

## ⚠️ Notes & Limitations

- Built for a hackathon — defaults favor demo-ability. Before production: set a strong `SECRET_KEY`, lock down CORS (currently `*`), move chat sessions to Redis, and migrate off SQLite.
- The Gemini engine requires a valid `AIza…` key; the **Tesseract** engine is the offline fallback.

---

## 📄 License

Released under the **MIT License** — free to use, modify, and build upon.

<div align="center">

**Built with ☕ and FastAPI for the hackathon.** ⭐ Star it if FinanceOS made budgeting suck less.

</div>
