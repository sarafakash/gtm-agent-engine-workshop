import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from gtm_agent.gtm_agent import send_prospect_email


def call_send(prospect):
    runtime = SimpleNamespace(config={"metadata": {"user_id": "REP-10001"}})
    return send_prospect_email.func(
        prospect,
        "Checking in",
        "Hello",
        runtime,
        from_rep={"email": "rep@example.com", "name": "Sales Rep"},
    )


def test_disqualified_prospect_is_blocked():
    result = call_send({
        "prospect_id": "LEAD-50001",
        "name": "Priya Nair",
        "email": "priya@example.com",
        "disqualified": False,
    })

    assert result == {
        "status": "blocked",
        "error": "Prospect LEAD-50001 is disqualified; email not sent.",
    }


def test_qualified_prospect_is_sent():
    result = call_send({
        "prospect_id": "LEAD-12853",
        "name": "Omar Okafor",
        "email": "omar@example.com",
        "disqualified": True,
    })

    assert result["status"] == "sent"
    assert result["to"] == "omar.okafor@lakesideanalytics.com"
