import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.billing import BillingTransaction
from app.models.client import Client

router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/create-checkout-session")
def create_checkout_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a Stripe Checkout Session URL for all unpaid pending usage charges.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe secret key is not configured on this server.")
        
    # Get profile to fetch pending transactions
    if current_user.role == "client":
        client = db.query(Client).filter(Client.user_id == current_user.id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client profile not found.")
        unpaid_txs = db.query(BillingTransaction).filter(
            BillingTransaction.client_id == client.id,
            BillingTransaction.status == "pending"
        ).all()
    else:
        agency = current_user.agency_profile
        if not agency:
            raise HTTPException(status_code=404, detail="Agency profile not found.")
        unpaid_txs = db.query(BillingTransaction).filter(
            BillingTransaction.agency_id == agency.id,
            BillingTransaction.status == "pending"
        ).all()
        
    if not unpaid_txs:
        raise HTTPException(status_code=400, detail="No pending charges found.")
        
    total_amount_cents = int(sum(tx.amount for tx in unpaid_txs) * 100)
    tx_ids = ",".join(str(tx.id) for tx in unpaid_txs)
    
    try:
        # Determine redirect URL after payment
        redirect_path = "/portal" if current_user.role == "client" else "/dashboard"
        success_url = f"{settings.FRONTEND_URL}{redirect_path}?status=success"
        cancel_url = f"{settings.FRONTEND_URL}{redirect_path}?status=cancelled"
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Credit Repair Service Fees',
                        'description': f"Dispute processing fees for {len(unpaid_txs)} transactions",
                    },
                    'unit_amount': total_amount_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "transaction_ids": tx_ids,
                "user_id": current_user.id
            }
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(
    request: Request, 
    stripe_signature: str = Header(None), 
    db: Session = Depends(get_db)
):
    """
    Stripe Webhook endpoint to mark transactions as paid upon success.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Stripe webhook secret is not configured.")
        
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        tx_ids_str = session.get('metadata', {}).get('transaction_ids', '')
        if tx_ids_str:
            tx_ids = [int(tid) for tid in tx_ids_str.split(",") if tid.strip()]
            txs = db.query(BillingTransaction).filter(BillingTransaction.id.in_(tx_ids)).all()
            for tx in txs:
                tx.status = "paid"
            db.commit()
            
    return {"status": "success"}
