import requests
import json

# TA CLÉ (Je l'ai remise pour toi)
BREVO_API_KEY = "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" 

# TON EMAIL
ADMIN_EMAIL = "mrprezfr@gmail.com"

def send_email_via_brevo(to_email, subject, html_content):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "Le Petit Bistrot", "email": ADMIN_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # 👇 C'EST ICI QUE J'AI CHANGÉ LE CODE 👇
        if response.status_code == 201:
            print(f"✅ Email envoyé avec succès à {to_email}")
            return True
        else:
            # On affiche l'erreur exacte donnée par Brevo
            print(f"❌ ERREUR BREVO ({response.status_code}) :")
            print(response.text) 
            return False
            
    except Exception as e:
        print(f"❌ Erreur connexion Python: {e}")
        return False

# ... Le reste ne change pas ...
def send_confirmation_email(client_email, client_name, date, time, pax):
    html = f"<h1>Merci {client_name}</h1><p>Confirmé !</p>"
    send_email_via_brevo(client_email, "Confirmation", html)

def send_admin_alert(client_name, date, time, pax):
    html = f"<h1>Nouvelle résa : {client_name}</h1>"
    send_email_via_brevo(ADMIN_EMAIL, "Alerte Admin", html)

if __name__ == "__main__":
    print("Tentative d'envoi...")
    send_admin_alert("Testeur Admin", "2024-01-01", "20:00", 4)