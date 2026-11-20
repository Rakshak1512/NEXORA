import pytest
import secrets
from app.models.models import OTPChallenge, Profile, Organization, Tenant

def test_saas_multi_tenant_registration_and_otp_flow(client):
    unique_suffix = secrets.token_hex(4)
    email = f"lead.{unique_suffix}@enterprise-corp.com"
    org_name = f"Enterprise Corp {unique_suffix}"

    # 1. Register new organization
    reg_res = client.post("/api/auth/register-org", json={
        "full_name": "Marcus Aurelius",
        "email": email,
        "password": "SecurePassword2026!",
        "organization_name": org_name,
        "industry": "FinTech",
        "org_size": "50-200",
        "country": "Germany",
        "job_title": "Chief Information Security Officer"
    })
    assert reg_res.status_code == 200, reg_res.text
    reg_data = reg_res.json()
    assert reg_data["status"] == "otp_sent"
    assert reg_data["email"] == email

    # 2. Resend rate limit check (immediate resend triggers cooldown)
    resend_res = client.post("/api/auth/resend-otp", json={
        "email": email,
        "purpose": "signup"
    })
    assert resend_res.status_code == 429
    assert "Please wait" in resend_res.json()["detail"]

    # 3. Retrieve challenge from DB directly to get valid code
    from app.database import SessionLocal
    from app.auth.otp import hash_otp
    db = SessionLocal()
    challenge = db.query(OTPChallenge).filter(
        OTPChallenge.email == email,
        OTPChallenge.purpose == "signup",
        OTPChallenge.is_used == False
    ).order_by(OTPChallenge.created_at.desc()).first()
    assert challenge is not None

    # Test invalid code
    bad_verify = client.post("/api/auth/verify-otp", json={
        "email": email,
        "otp": "000000",
        "purpose": "signup"
    })
    assert bad_verify.status_code == 400
    assert "Invalid verification code" in bad_verify.json()["detail"]

    # Generate a matching code for verification
    code = "789123"
    challenge.otp_hash = hash_otp(email, code, "signup")
    db.commit()
    db.close()

    # 4. Verify OTP and automatically provision Workspace
    verify_res = client.post("/api/auth/verify-otp", json={
        "email": email,
        "otp": code,
        "purpose": "signup"
    })
    assert verify_res.status_code == 200, verify_res.text
    vdata = verify_res.json()
    assert vdata["status"] == "verified"
    assert "access_token" in vdata
    token = vdata["access_token"]
    assert vdata["user"]["email"] == email
    assert vdata["user"]["role"] == "Organization Owner"
    org_id = vdata["organization"]["id"]
    assert org_id is not None

    auth_headers = {"Authorization": f"Bearer {token}"}

    # 5. Access organization profile
    org_res = client.get("/api/organization/current", headers=auth_headers)
    assert org_res.status_code == 200
    assert org_res.json()["name"] == org_name
    assert org_res.json()["industry"] == "FinTech"

    # 6. List members (Creator should be Organization Owner)
    members_res = client.get("/api/organization/members", headers=auth_headers)
    assert members_res.status_code == 200
    members = members_res.json()
    assert len(members) >= 1
    assert any(m["email"] == email and m["role"] == "Organization Owner" for m in members)

    # 7. Invite a team member
    colleague_email = f"analyst.{unique_suffix}@enterprise-corp.com"
    invite_res = client.post("/api/organization/members/invite", headers=auth_headers, json={
        "email": colleague_email,
        "full_name": "Helena Vance",
        "role": "Security Analyst",
        "job_title": "Senior SOC Analyst"
    })
    assert invite_res.status_code == 200
    assert invite_res.json()["status"] == "invited"

    # Check updated member list
    members_res2 = client.get("/api/organization/members", headers=auth_headers)
    assert len(members_res2.json()) >= 2

    # 8. Create API Key
    key_res = client.post("/api/developer/keys", headers=auth_headers, json={
        "name": "CI/CD Pipeline Key",
        "permissions": ["read", "write"],
        "expires_in_days": 60
    })
    assert key_res.status_code == 200
    key_data = key_res.json()
    assert "cyn_live_" in key_data["secret_key"]
    assert key_data["key_prefix"].startswith("cyn_live_")
    key_id = key_data["id"]

    # List keys (secret_key is NOT returned on list)
    list_keys_res = client.get("/api/developer/keys", headers=auth_headers)
    assert list_keys_res.status_code == 200
    assert any(k["id"] == key_id and k["secret_key"] is None for k in list_keys_res.json())

    # 9. Create Embeddable Monitoring Widget
    widget_res = client.post("/api/developer/widgets", headers=auth_headers, json={
        "name": "Public Portal Status Widget",
        "widget_type": "health_status",
        "theme": "dark"
    })
    assert widget_res.status_code == 200
    wdata = widget_res.json()
    widget_token = wdata["token"]
    assert "<iframe" in wdata["embed_iframe_code"]

    # 10. Public Readout of Embed Widget (No Auth Header Required!)
    public_res = client.get(f"/api/v1/embed/{widget_token}")
    assert public_res.status_code == 200
    pub_data = public_res.json()
    assert pub_data["organization_name"] == org_name
    assert pub_data["status"] in ["ALL_SYSTEMS_OPERATIONAL", "DEGRADED_PERFORMANCE", "MAJOR_OUTAGE"]
    assert "average_cpu_pct" in pub_data

    # 11. Generate Executive SLA Report
    rep_res = client.post("/api/reports/generate", headers=auth_headers, json={
        "title": "Q4 Observability & SLA Compliance Audit",
        "report_type": "executive_summary",
        "time_range": "last_30_days"
    })
    assert rep_res.status_code == 200
    rdata = rep_res.json()
    assert rdata["title"] == "Q4 Observability & SLA Compliance Audit"
    assert rdata["summary_data"]["privacy_and_security"]["zero_trust_compliance"] == "100%"

    # 12. Check Notifications Inbox
    notif_res = client.get("/api/notifications", headers=auth_headers)
    assert notif_res.status_code == 200
    notifs = notif_res.json()
    assert len(notifs) >= 1
    assert "CYNERA" in notifs[0]["title"]

    # Mark all read
    read_res = client.post("/api/notifications/read-all", headers=auth_headers)
    assert read_res.status_code == 200
