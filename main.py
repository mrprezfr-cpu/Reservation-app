import stripe
import uvicorn
import secrets
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager

# 👇 NOUVEL IMPORT : On appelle notre facteur
from email_service import send_confirmation_email

from Database import SessionLocal, engine, Restaurant, Booking, ResourceType, BookingStatus, init_db

# --- SÉCURITÉ ---
security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "supersecret")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Accès interdit",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Démarrage...")
    init_db()
    db = SessionLocal()
    try:
        if db.query(Restaurant).count() == 0:
            resto = Restaurant(name="Le Petit Bistrot", resource_type=ResourceType.TABLE, deposit_amount_cents=1000, max_capacity=50)
            db.add(resto)
            db.commit()
    finally:
        db.close()
    yield
    print("🛑 Arrêt...")

app = FastAPI(lifespan=lifespan)

# ⚠️⚠️ REMETS TES CLÉS STRIPE ICI ⚠️⚠️
stripe.api_key = "sk_test_51SwoLAAU8Nnw6fb8ixFtXi9Kg9EqJnEcfjTbOvjW2RKqvY0Eul8hIjZIX7e09eRYlOyh3WsE4OTNp0T2JoYP1Xms00vRMTTGKx" 
ENDPOINT_SECRET = "whsec_..." 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# 👇 MISE À JOUR : On ajoute l'email dans la requête
class BookingRequest(BaseModel):
    restaurant_id: int
    name: str
    email: str  # <--- Nouveau champ
    date: str
    time: str
    pax: int

@app.get("/")
def read_root():
    return FileResponse('index.html')

@app.get("/admin.html")
def read_admin():
    return FileResponse('admin.html')

@app.post("/create-deposit")
def create_deposit(req: BookingRequest, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == req.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant introuvable")

    amount = restaurant.deposit_amount_cents * req.pax if restaurant.resource_type == ResourceType.TABLE else restaurant.deposit_amount_cents
    
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='eur',
            capture_method='manual', 
            payment_method_types=['card'],
            metadata={'restaurant_id': restaurant.id, 'client_name': req.name, 'client_email': req.email}
        )
        
        # Enregistrement en base (avec l'email !)
        new_booking = Booking(
            restaurant_id=restaurant.id,
            client_name=req.name,
            client_email=req.email, # <--- On sauvegarde l'email
            pax=req.pax,
            stripe_payment_intent_id=intent.id,
            status=BookingStatus.PENDING
        )
        db.add(new_booking)
        db.commit()

        # 👇 ENVOI DE L'EMAIL DE CONFIRMATION 👇
        print(f"Tentative d'envoi d'email à {req.email}...")
        send_confirmation_email(req.email, req.name, req.date, req.time, req.pax)

        return {"clientSecret": intent.client_secret}

    except Exception as e:
        print(f"Erreur: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, ENDPOINT_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Webhook Error")

    if event['type'] == 'payment_intent.amount_capturable_updated':
        intent = event['data']['object']
        booking = db.query(Booking).filter(Booking.stripe_payment_intent_id == intent['id']).first()
        if booking:
            booking.status = BookingStatus.CONFIRMED
            db.commit()
    return {"status": "success"}

# --- ROUTES ADMIN ---
@app.get("/api/bookings")
def get_all_bookings(db: Session = Depends(get_db), username: str = Depends(get_current_username)):
    return db.query(Booking).order_by(Booking.id.desc()).all()

@app.post("/api/bookings/{booking_id}/capture")
def capture_booking(booking_id: int, db: Session = Depends(get_db), username: str = Depends(get_current_username)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking: raise HTTPException(status_code=404, detail="Introuvable")
    try:
        stripe.PaymentIntent.capture(booking.stripe_payment_intent_id)
        booking.status = BookingStatus.NOSHOW
        db.commit()
        return {"status": "captured"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/bookings/{booking_id}/release")
def release_booking(booking_id: int, db: Session = Depends(get_db), username: str = Depends(get_current_username)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking: raise HTTPException(status_code=404, detail="Introuvable")
    try:
        stripe.PaymentIntent.cancel(booking.stripe_payment_intent_id)
        booking.status = BookingStatus.COMPLETED
        db.commit()
        return {"status": "released"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)