"""Stripe router - Checkout, Portal, Webhooks"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import os
import stripe
import json
from pathlib import Path

router = APIRouter(prefix="/api/stripe", tags=["stripe"])

# Config
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
# Price IDs (set in Railway env)
PRICE_DJ_STARTER = os.getenv("STRIPE_PRICE_DJ_STARTER", "price_dj_starter")
PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "price_pro")

TRIAL_FILE = Path("/Users/indradev_work/Downloads/MassLoopai/massloop-be/data/trials.json")


class CheckoutRequest(BaseModel):
    price_id: str = PRICE_DJ_STARTER
    success_url: str = "https://massloop-fe-production.up.railway.app/success"
    cancel_url: str = "https://massloop-fe-production.up.railway.app/"


@router.post("/checkout")
def create_checkout_session(req: CheckoutRequest):
    """Create a Stripe Checkout Session for subscription."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured")
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": req.price_id, "quantity": 1}],
            success_url=req.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=req.cancel_url,
        )
        return {"url": session.url, "session_id": session.id}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/portal")
def customer_portlet(customer_id: str):
    """Create a Stripe Customer Portal session."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured")
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url="https://massloop-fe-production.up.railway.app",
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks: checkout.session.completed = mark paid."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(400, f"Webhook signature failed: {e}")

    event_type = event.get("type", "")
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        customer_id = session.get("customer", "")
        subscription_id = session.get("subscription", "")
        _save_payment(customer_id, subscription_id)

    return {"status": "ok"}


def _save_payment(customer_id: str, subscription_id: str):
    """Persist payment record."""
    TRIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if TRIAL_FILE.exists():
        try:
            data = json.load(open(TRIAL_FILE))
        except Exception:
            pass
    data[customer_id] = {
        "subscription_id": subscription_id,
        "paid": True,
        "tier": "dj_starter",
    }
    with open(TRIAL_FILE, "w") as f:
        json.dump(data, f, indent=2)


def is_paid(customer_id: str) -> bool:
    """Check if user has paid subscription."""
    if not TRIAL_FILE.exists():
        return False
    try:
        data = json.load(open(TRIAL_FILE))
        return data.get(customer_id, {}).get("paid", False)
    except Exception:
        return False
