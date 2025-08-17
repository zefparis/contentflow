from pydantic import BaseModel, EmailStr

class TestEmail(BaseModel):
    email: EmailStr

# Test avec un email valide
try:
    test = TestEmail(email="test@example.com")
    print("✅ Email valide accepté avec succès")
except Exception as e:
    print(f"❌ Erreur avec email valide: {e}")

# Test avec un email invalide
try:
    test = TestEmail(email="invalide")
    print("❌ Email invalide accepté par erreur")
except Exception as e:
    print(f"✅ Email invalide correctement rejeté: {e}")
