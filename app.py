import hashlib
import json
import os
from typing import Any

import requests
import streamlit as st


API_URL = "https://api.typesafe.ai/v1/systemone"

SAMPLE_TICKETS = {
    "Payment failure — urgent": (
        "Our customer payouts have failed for three days. This is blocking payroll "
        "for 40 employees. Please restore service today."
    ),
    "Password reset": (
        "I forgot my password and cannot access the employee portal. Can you help me reset it?"
    ),
    "Possible data exposure": (
        "I accidentally emailed a spreadsheet containing customer phone numbers and account IDs "
        "to an external address. What should I do?"
    ),
    "Product suggestion": (
        "It would be helpful if the dashboard could export filtered reports as CSV files."
    ),
}


def mock_evaluate(ticket: str) -> dict[str, Any]:
    """Deterministic demo responses; no data leaves the application."""
    text = ticket.lower()
    sensitive_terms = ("customer", "phone", "account id", "ssn", "external")
    urgent_terms = ("urgent", "today", "failed", "blocking", "payroll", "outage")
    security_terms = ("exposure", "external", "breach", "leak", "phone numbers")

    sensitive = 0.91 if any(term in text for term in sensitive_terms) else 0.09
    urgent = 0.93 if any(term in text for term in urgent_terms) else 0.18

    if any(term in text for term in security_terms):
        department = "security"
        probs = {"security": 0.91, "payments": 0.03, "access": 0.03, "product": 0.02, "general": 0.01}
    elif any(term in text for term in ("payout", "payment", "payroll")):
        department = "payments"
        probs = {"payments": 0.94, "security": 0.02, "access": 0.01, "product": 0.01, "general": 0.02}
    elif any(term in text for term in ("password", "login", "access")):
        department = "access"
        probs = {"access": 0.92, "security": 0.03, "payments": 0.01, "product": 0.01, "general": 0.03}
    elif any(term in text for term in ("suggest", "feature", "helpful", "dashboard")):
        department = "product"
        probs = {"product": 0.88, "general": 0.07, "access": 0.02, "security": 0.01, "payments": 0.02}
    else:
        department = "general"
        probs = {"general": 0.62, "product": 0.12, "access": 0.10, "security": 0.08, "payments": 0.08}

    confidence = probs[department]
    automation = 0.82 if department in ("access", "product") and sensitive < 0.5 else 0.19
    return {
        "answers": {
            "department": {"choice": department, "probabilities": probs, "confidence": confidence},
            "urgency": {
                "score": 4 if urgent > 0.8 else 1,
                "probabilities": {"0": 0.04, "1": 0.08, "2": 0.12, "3": 0.16, "4": 0.60} if urgent > 0.8 else {"0": 0.18, "1": 0.55, "2": 0.17, "3": 0.07, "4": 0.03},
                "confidence": 0.84,
            },
            "contains_sensitive_data": {"noul": sensitive},
            "safe_to_automate": {"noul": automation},
        },
        "meta": {"mode": "mock", "request_id": hashlib.sha256(ticket.encode()).hexdigest()[:10]},
    }


def build_payload(ticket: str) -> dict[str, Any]:
    return {
        "model": "jev-latest",
        "state": {"ticket": ticket},
        "questions": {
            "department": {
                "type": "choice",
                "instructions": "Which team should own this support ticket?",
                "criteria": {
                    "payments": "Payment processing, billing, payouts, or invoices",
                    "access": "Login, password, permissions, or account access",
                    "security": "Security incidents, privacy, or data exposure",
                    "product": "Feature requests or product feedback",
                    "general": "Anything not covered by the other teams",
                },
            },
            "urgency": {
                "type": "score",
                "instructions": "How operationally urgent is this ticket?",
                "criteria": [
                    "No time pressure or business impact",
                    "Low impact; normal response is appropriate",
                    "Moderate impact requiring timely attention",
                    "High impact requiring rapid attention",
                    "Critical impact or immediate safety, security, or business risk",
                ],
            },
            "contains_sensitive_data": {
                "type": "noul",
                "instructions": "Does the ticket contain or describe sensitive personal, account, or security data?",
            },
            "safe_to_automate": {
                "type": "noul",
                "instructions": "Can this ticket safely follow an automated standard workflow without human judgment?",
            },
        },
    }


def jev_evaluate(ticket: str, api_key: str) -> dict[str, Any]:
    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=build_payload(ticket),
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    result.setdefault("meta", {})["mode"] = "live"
    return result


def normalize_answers(result: dict[str, Any]) -> dict[str, Any]:
    return result.get("answers", result)


def decision_policy(answers: dict[str, Any], threshold: float) -> dict[str, Any]:
    route = answers["department"]["choice"]
    confidence = float(answers["department"].get("confidence", 0))
    urgency_score = float(answers["urgency"]["score"])
    urgency_level = min(5, max(1, round(urgency_score) + 1))
    sensitive = float(answers["contains_sensitive_data"]["noul"])
    automatable = float(answers["safe_to_automate"]["noul"])

    reasons = []
    if confidence < threshold:
        reasons.append("routing confidence is below the selected threshold")
    if sensitive >= 0.70:
        reasons.append("sensitive-data probability is high")
    if urgency_score >= 3.5:
        reasons.append("urgency is critical")
    if automatable < 0.70:
        reasons.append("automation suitability is low")

    action = "Human review" if reasons else "Auto-route"
    return {"action": action, "route": route.title(), "urgency_level": urgency_level, "reasons": reasons}


st.set_page_config(page_title="Jev Decision Desk", page_icon="⚡", layout="wide")
st.title("⚡ Jev Decision Desk")
st.caption("Standalone POC · synthetic data only · structured, confidence-aware decisions")

with st.sidebar:
    st.header("Configuration")
    mode = st.radio("Execution mode", ["Mock demo", "Live Jev API"])
    threshold = st.slider("Minimum routing confidence", 0.50, 0.99, 0.80, 0.01)
    api_key = ""
    if mode == "Live Jev API":
        api_key = st.text_input(
            "TypeSafe API key",
            value=os.getenv("TYPESAFE_API_KEY", ""),
            type="password",
            help="Prefer the TYPESAFE_API_KEY environment variable.",
        )
    if mode == "Mock demo":
        st.info("Mock mode uses local rules and never sends ticket text externally.")
    else:
        st.info("Live mode sends the synthetic ticket to the TypeSafe Jev API.")

sample = st.selectbox("Load a synthetic scenario", list(SAMPLE_TICKETS))
ticket = st.text_area("Support ticket", value=SAMPLE_TICKETS[sample], height=150)

if st.button("Evaluate ticket", type="primary", use_container_width=True):
    if not ticket.strip():
        st.warning("Enter a ticket before evaluating it.")
        st.stop()
    try:
        result = mock_evaluate(ticket) if mode == "Mock demo" else jev_evaluate(ticket, api_key)
        answers = normalize_answers(result)
        policy = decision_policy(answers, threshold)

        if policy["action"] == "Auto-route":
            st.success(f"Decision: Auto-route to {policy['route']}")
        else:
            st.warning(f"Decision: Human review · proposed owner: {policy['route']}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Team", policy["route"])
        c2.metric("Route confidence", f"{answers['department'].get('confidence', 0):.0%}")
        c3.metric("Urgency", f"{policy['urgency_level']} / 5")
        c4.metric("Sensitive-data risk", f"{answers['contains_sensitive_data']['noul']:.0%}")

        if policy["reasons"]:
            st.subheader("Why human review was selected")
            for reason in policy["reasons"]:
                st.write(f"• {reason.capitalize()}")

        with st.expander("Decision trace"):
            st.json({"policy": policy, "model_answers": answers, "metadata": result.get("meta", {})})
        with st.expander("API request preview"):
            st.code(json.dumps(build_payload(ticket), indent=2), language="json")
    except requests.HTTPError as exc:
        detail = exc.response.text[:800] if exc.response is not None else str(exc)
        st.error(f"Jev API request failed: {detail}")
    except Exception as exc:
        st.error(f"Unable to evaluate the ticket: {exc}")

st.divider()
st.caption("POC guardrail: model outputs inform the decision; deterministic application policy controls the action.")
