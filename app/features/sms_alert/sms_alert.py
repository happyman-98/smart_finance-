import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
import pandas as pd

SALARY_BUDGET = 30_000.00         
THRESHOLDS = (0.25, 0.50, 0.75, 1.00)
STATE_FILE = Path("salary_alert_state.json")
CSV_PATH = "../graph/business_expenses_june2026.csv"

def current_salary_spend(csv_path: str) -> float:
    df = pd.read_csv(csv_path)
    return float(df.loc[df["Category"] == "Salaries", "Amount_USD"].sum())


def crossed_thresholds(spend: float, budget: float) -> list[float]:
    pct = spend / budget if budget else 0.0
    return [t for t in THRESHOLDS if pct >= t]


def load_fired() -> set[float]:
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()


def save_fired(fired: set[float]) -> None:
    STATE_FILE.write_text(json.dumps(sorted(fired)))


def get_recipients() -> list[str]:
    recipients = [r.strip() for r in os.getenv("ALERT_TO", "").split(",") if r.strip()]
    if not recipients:
        raise RuntimeError(
            "No recipients configured. Set ALERT_TO to a comma-separated "
            "list of emails, e.g. ALERT_TO=you@example.com,cfo@example.com"
        )
    return recipients


def send_email(subject: str, body: str, recipients: list[str]) -> None:
    host = "smtp.gmail.com"
    port = 587
    user = "study39kartik@gmail.com"
    password = os.environ["SMTP_PASS"]    
    sender = os.getenv("SMTP_FROM", user)

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
    print(f"sent -> {', '.join(recipients)}: {subject}")


def check_and_alert(csv_path: str) -> None:
    recipients = get_recipients()          
    spend = current_salary_spend(csv_path)
    pct = spend / SALARY_BUDGET if SALARY_BUDGET else 0.0
    met = set(crossed_thresholds(spend, SALARY_BUDGET))
    fired = load_fired()

    new = met - fired                     
    for t in sorted(new):
        subject = f"Salary budget alert: {t:.0%} reached"
        body = (
            f"Salary budget alert: {t:.0%} reached.\n"
            f"Spend ${spend:,.2f} of ${SALARY_BUDGET:,.2f} ({pct:.1%})."
        )
        send_email(subject, body, recipients)

    if new:
        save_fired(fired | new)
    else:
        print(f"No new thresholds. Spend ${spend:,.2f} ({pct:.1%}), "
              f"already fired: {sorted(fired) or 'none'}")


if __name__ == "__main__":
    check_and_alert(CSV_PATH)