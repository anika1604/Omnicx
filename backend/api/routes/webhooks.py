"""Webhook receivers for external channels (WhatsApp, email, etc.)"""
from fastapi import APIRouter, Request
import hashlib, hmac

router = APIRouter()


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """Twilio / WhatsApp Cloud API webhook."""
    body = await request.json()
    # Parse → forward to chat endpoint
    return {"status": "received"}


@router.post("/email")
async def email_webhook(request: Request):
    """SendGrid inbound parse webhook."""
    body = await request.json()
    return {"status": "received"}
