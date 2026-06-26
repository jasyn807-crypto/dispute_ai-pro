import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.billing import BillingTransaction
from app.models.client import Client
from app.models.dispute import DisputeLetter

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


@router.post("/create-mail-session/{letter_id}")
def create_mail_session(
    letter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a Stripe Checkout Session URL for a specific dispute letter mailing fee.
    Ensures pre-payment of certified mail fee before physical printing & dispatch occurs.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe secret key is not configured on this server.")
        
    letter = db.query(DisputeLetter).filter(DisputeLetter.id == letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Dispute letter not found")
        
    client = db.query(Client).filter(Client.id == letter.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client profile not found")
        
    # Check if they already have a paid transaction for this letter
    existing_paid = db.query(BillingTransaction).filter(
        BillingTransaction.client_id == client.id,
        BillingTransaction.description.like(f"%Letter #{letter_id}%"),
        BillingTransaction.status == "paid"
    ).first()
    if existing_paid:
        raise HTTPException(status_code=400, detail="This letter has already been paid for and queued/dispatched.")
        
    # Find or create a pending transaction for this specific letter
    tx = db.query(BillingTransaction).filter(
        BillingTransaction.client_id == client.id,
        BillingTransaction.description.like(f"%Letter #{letter_id}%"),
        BillingTransaction.status == "pending"
    ).first()
    
    if not tx:
        tx = BillingTransaction(
            agency_id=client.agency_id,
            client_id=client.id,
            amount=15.00, # Certified mail printing and USPS certified postage cost
            description=f"USPS Certified Mail Dispatch Fee (Letter #{letter_id})",
            status="pending"
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        
    total_amount_cents = int(tx.amount * 100)
    
    try:
        redirect_path = "/portal/disputes" if current_user.role == "client" else "/disputes"
        success_url = f"{settings.FRONTEND_URL}{redirect_path}?status=success"
        cancel_url = f"{settings.FRONTEND_URL}{redirect_path}?status=cancelled"
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'USPS Certified Mail Dispatch Service',
                        'description': f"Certified Mail printing & physical dispatch for Letter #{letter_id}",
                    },
                    'unit_amount': total_amount_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "transaction_ids": str(tx.id),
                "dispute_letter_id": str(letter_id),
                "action": "mail_letter",
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
    Automatically triggers physical mailing if the action is mail_letter.
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
        action = session.get('metadata', {}).get('action', '')
        letter_id_str = session.get('metadata', {}).get('dispute_letter_id', '')
        user_id_str = session.get('metadata', {}).get('user_id', '')
        
        if tx_ids_str:
            tx_ids = [int(tid) for tid in tx_ids_str.split(",") if tid.strip()]
            txs = db.query(BillingTransaction).filter(BillingTransaction.id.in_(tx_ids)).all()
            for tx in txs:
                tx.status = "paid"
            db.commit()
            
        # Trigger Lob certified mail dispatch on successful payment receipt
        if action == "mail_letter" and letter_id_str:
            letter_id = int(letter_id_str)
            letter = db.query(DisputeLetter).filter(DisputeLetter.id == letter_id).first()
            if letter and letter.status != "mailed":
                from app.api.mailing import perform_mail_dispatch
                user_id = int(user_id_str) if user_id_str else None
                perform_mail_dispatch(
                    letter=letter,
                    db=db,
                    triggered_by_user_id=user_id
                )
            
    return {"status": "success"}

