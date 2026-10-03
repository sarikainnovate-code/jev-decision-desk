from app import decision_policy, mock_evaluate, normalize_answers


def test_sensitive_ticket_requires_review():
    result = mock_evaluate("I emailed customer phone numbers to an external address.")
    decision = decision_policy(normalize_answers(result), 0.80)
    assert decision["action"] == "Human review"
    assert decision["route"] == "Security"


def test_password_reset_can_auto_route():
    result = mock_evaluate("I forgot my password and cannot access the portal.")
    decision = decision_policy(normalize_answers(result), 0.80)
    assert decision["action"] == "Auto-route"
    assert decision["route"] == "Access"
