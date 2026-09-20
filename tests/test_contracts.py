from pydantic import ValidationError

from app.schemas.api import CampaignLaunchRequest, EmailSendRequest, RouteCallRequest


def test_campaign_limits_are_bounded():
    request = CampaignLaunchRequest(limit=20, delay_sec=30)
    assert request.limit == 20


def test_route_call_requires_e164_number():
    try:
        RouteCallRequest(target_phone="020 1234 5678")
    except ValidationError:
        return
    raise AssertionError("national-format number unexpectedly passed E.164 validation")


def test_route_call_normalizes_e164_number():
    request = RouteCallRequest(target_phone="+44 20 1234 5678")
    assert request.target_phone == "+442012345678"


def test_email_subject_rejects_header_injection():
    try:
        EmailSendRequest(
            lead_id=1,
            to_email="owner@example.test",
            subject="Hello\nBcc: attacker@example.test",
            body="Body",
        )
    except ValidationError:
        return
    raise AssertionError("email header injection unexpectedly passed validation")
