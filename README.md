# Jev Decision Desk

A standalone proof of concept showing how Jev can act as a structured decision layer for support-ticket routing. It uses fictional data and is not connected to any existing project.

## Architecture

```text
Synthetic ticket
      ↓
Jev System One API
      ↓
Choice + Score + Noul decisions
      ↓
Deterministic confidence and safety policy
      ↓
Auto-route or human review
```

The model evaluates narrowly scoped decisions. Application code—not generated prose—controls the final action.

## What the demo shows

- Fixed-option routing to Payments, Access, Security, Product, or General
- Urgency scoring from 1–5
- Probabilities for sensitive data and safe automation
- A deterministic policy that auto-routes only when confidence and safety conditions pass
- A visible decision trace and API-request preview
- Mock mode requiring no credentials
- Live mode using the TypeSafe System One API and `jev-latest`

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Enable the real Jev API

Create an API key with TypeSafe AI, then store it in an environment variable.

macOS/Linux:

```bash
export TYPESAFE_API_KEY="your-key"
streamlit run app.py
```

Windows PowerShell:

```powershell
$env:TYPESAFE_API_KEY="your-key"
streamlit run app.py
```

Select **Live Jev API** in the sidebar. Do not commit the key to source control.

## Security

- Use only synthetic data for this public demonstration.
- Never commit API keys; `.env` and Streamlit secrets are ignored.
- The key entered in the UI is masked and retained only for the running app session.
- Review TypeSafe's data-handling terms before using organizational data.

## Demo script

1. Start in Mock demo mode and select **Password reset**.
2. Evaluate it and explain that Jev-style outputs are typed decisions, not generated prose.
3. Select **Possible data exposure** and evaluate again.
4. Show that application policy forces human review because sensitivity is high and automation suitability is low.
5. Change the confidence threshold and demonstrate that business policy remains controlled by code.
6. Open **Decision trace** and **API request preview** to show auditability.

## Important note

Mock mode is a deterministic simulation for demonstrating the workflow. Live mode calls the TypeSafe System One endpoint using `jev-latest`. Validate the current API schema and your organization's security requirements before production use.
