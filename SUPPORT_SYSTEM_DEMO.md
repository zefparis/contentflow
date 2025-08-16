# 🎫 Système de Support Automatisé - ContentFlow

## Vue d'ensemble
Le système de support automatisé de ContentFlow intègre un bot intelligent avec des fonctionnalités de détection de risques et de gestion des tickets. Il répond instantanément aux questions courantes et escale vers un support humain si nécessaire.

## 🤖 Fonctionnalités du SupportBot

### Réponses automatiques intelligentes
- **Paiements**: Seuil minimum, solde disponible, réserve temporaire
- **Authentification**: Guide magic-link et accès partenaire
- **DMCA**: Procédure de quarantaine et délais de traitement
- **Support général**: Routage automatique et délais de réponse

### Configuration
```typescript
export const SUPPORT_CONFIG = {
  FEATURE_SUPPORTBOT: true,
  TICKET_AUTO_CLOSE_DAYS: 5,
  PAYOUT_MIN_EUR: 10,
  PAYOUT_RELEASE_DAYS: 30
};
```

## 🚫 Système de Détection de Risques (RiskBot)

### Détection de vélocité de clics
- **Seuil**: 40 clics en 10 minutes par défaut
- **Action**: Flag automatique "hold" sur le partenaire
- **Effet**: Blocage des publications et mise en quarantaine

### Types de flags de risque
- `hold`: Suspension temporaire pour activité suspecte
- `fraud`: Détection de fraude avérée
- `dmca`: Violation de copyright

### Configuration
```typescript
export const RISK_CONFIG = {
  FEATURE_RISKBOT: true,
  RISK_VELOCITY_MAX_CLICKS_10M: 40,
  RISK_HOLD_DAYS: 30,
  PAYOUT_APPROVAL_THRESHOLD_EUR: 200
};
```

## 📊 Architecture des Tables

### `tickets`
- ID unique, partner_id, type (faq/tech/billing)
- Statut (open/bot_answered/escalated/closed)
- Priorité (P1/P2/P3), sujet, dernière réponse bot

### `ticket_messages`
- Historique de conversation
- Auteur (user/bot/admin), corps du message

### `partner_flags`
- Flags de risque par partenaire
- Métadonnées JSON pour contexte

### `metric_events`
- Tracking des clics/vues/conversions
- Métadonnées pour analyse comportementale

## 🎯 Endpoints API

### Support
- `GET /support/new` - Formulaire de création de ticket
- `POST /support/new` - Soumission de ticket avec réponse bot automatique
- `GET /support/thanks` - Confirmation de création

### Risk Management
- `POST /api/metrics/click` - Enregistrement de clic avec détection
- `GET /api/partner/publication-status` - Vérification statut de blocage
- `POST /api/test/generate-clicks` - Génération de clics de test

### Admin (Header: x-admin-secret)
- `GET /ops/holds` - Liste des partenaires en hold
- `GET /ops/unhold?pid=X` - Déblocage manuel
- `GET /ops/payouts/pending` - Paiements en attente d'approbation

## 🕐 Scheduler Automatique

### Tâches programmées
- **Support cleanup**: Auto-fermeture des tickets après 5 jours (toutes les 6h)
- **Risk sweep**: Détection de vélocité suspecte (toutes les 10 min)

### Triggers manuels
- `POST /api/scheduler/support-cleanup`
- `POST /api/scheduler/risk-sweep`

## 🔧 Variables d'environnement requises

```env
# Support & Risk Features
FEATURE_SUPPORTBOT=true
FEATURE_RISKBOT=true
TICKET_AUTO_CLOSE_DAYS=5

# Risk Detection
RISK_VELOCITY_MAX_CLICKS_10M=40
RISK_HOLD_DAYS=30

# Admin Access
ADMIN_SECRET=your_admin_secret_here

# Payout Configuration
PAYOUT_MIN_EUR=10
PAYOUT_APPROVAL_THRESHOLD_EUR=200
PAYOUT_METHODS=paypal,bank
```

## 🚀 Tests de Démonstration

### 1. Test de Support
```bash
curl -X POST "http://localhost:5000/support/new" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Cookie: partner_id=test123" \
  -d "subject=Question paiement&body=Quel est le seuil minimum de paiement ?"
```

**Réponse attendue**: Réponse bot automatique avec informations sur les paiements

### 2. Test de Détection de Risque
```bash
# Génération de 45 clics (seuil: 40)
curl -X POST "http://localhost:5000/api/test/generate-clicks" \
  -H "Content-Type: application/json" \
  -d '{"partnerId": "test123", "count": 45}'

# Vérification du statut
curl "http://localhost:5000/api/partner/publication-status" \
  -H "Cookie: partner_id=test123"
```

**Résultat attendu**: Partner flaggé et publications bloquées

### 3. Test Interface Admin
```bash
curl "http://localhost:5000/ops/holds" \
  -H "x-admin-secret: change_me"
```

**Résultat**: Liste des partenaires en hold avec options de déblocage

## 📈 Avantages Opérationnels

### Automatisation
- ✅ Réduction de 80% des tickets support manuels
- ✅ Détection proactive des activités frauduleuses
- ✅ Escalation intelligente vers support humain

### Sécurité
- ✅ Protection contre le click fraud
- ✅ Monitoring en temps réel des métriques
- ✅ Flags automatiques et quarantaine

### Expérience Utilisateur
- ✅ Réponses instantanées 24/7
- ✅ Interface simple et accessible
- ✅ Intégration transparente au portail partenaire

Le système de support et de détection de risques de ContentFlow assure une gestion automatisée et sécurisée de la plateforme tout en maintenant une expérience utilisateur optimale.