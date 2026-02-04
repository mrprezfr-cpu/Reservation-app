import requests
import json

# 🔑 TA CLÉ BREVO (Celle qui commence par xkeysib-...)
BREVO_API_KEY = "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" 

def send_confirmation_email(client_email, client_name, date, time, pax):
    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    payload = {
        "sender": {"name": "Le Petit Bistrot", "email": "mrprezfr@gmail.com"}, # <--- METS TON EMAIL ICI
        "to": [{"email": client_email, "name": client_name}],
        "subject": "Confirmation de réservation - Le Petit Bistrot",
        "htmlContent": f"""
        <html>
            <body>
                <h1>Merci {client_name} !</h1>
                <p>Votre table est bien pré-réservée.</p>
                <ul>
                    <li>📅 Date : {date}</li>
                    <li>🕗 Heure : {time}</li>
                    <li>👥 Personnes : {pax}</li>
                </ul>
                <p>Une empreinte bancaire a été sécurisée. Elle ne sera débitée qu'en cas de non-présentation.</p>
                <br>
                <p>À très vite,<br>L'équipe du Petit Bistrot</p>
            </body>
        </html>
        """
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 201:
            print(f"📧 Email envoyé avec succès à {client_email} !")
            return True
        else:
            print(f"❌ Erreur Brevo : {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur connection : {str(e)}")
        return False

# --- PETIT TEST RAPIDE ---
# Ce bloc ne s'exécute que si on lance ce fichier directement
if __name__ == "__main__":
    print("Test d'envoi d'email...")
    # Mets ton propre email ici pour tester que tu le reçois bien
    send_confirmation_email("mrprezfr@gmail.com", "Testeur", "2024-01-01", "20:00", 2)