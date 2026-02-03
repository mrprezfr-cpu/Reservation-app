import stripe
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, engine, Restaurant, Booking, ResourceType, BookingStatus, init_db

# --- CONFIGURATION ---
app = FastAPI()

# ⚠️ TES CLÉS STRIPE (Laisse les guillemets)
stripe.api_key = "sk_test_..." 
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

class BookingRequest(BaseModel):
    restaurant_id: int
    name: str # J'ai simplifié pour matcher le frontend (form.name)
    date: str
    time: str
    pax: int

@app.on_event("startup")
def startup_event():
    init_db()
    db = SessionLocal()
    if db.query(Restaurant).count() == 0:
        resto = Restaurant(name="Le Petit Bistrot", resource_type=ResourceType.TABLE, deposit_amount_cents=1000, max_capacity=50)
        db.add(resto)
        db.commit()
    db.close()

@app.get("/")
def read_root():
    return FileResponse('index.html')

@app.post("/create-deposit")
def create_deposit(req: BookingRequest, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == req.restaurant_id).first()
    if not restaurant: raise HTTPException(status_code=404, detail="Restaurant introuvable")

    amount = restaurant.deposit_amount_cents * req.pax if restaurant.resource_type == ResourceType.TABLE else restaurant.deposit_amount_cents
    
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount, currency='eur', capture_method='manual', payment_method_types=['card'],
            metadata={'restaurant_id': restaurant.id, 'client_name': req.name}
        )
        new_booking = Booking(restaurant_id=restaurant.id, client_name=req.name, pax=req.pax, stripe_payment_intent_id=intent.id)
        db.add(new_booking)
        db.commit()
        return {"clientSecret": intent.client_secret}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

# --- LA LIGNE SPÉCIALE REPLIT ---
if __name__ == "__main__":
    # host="0.0.0.0" permet d'écouter toutes les connexions (indispensable pour Replit)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
