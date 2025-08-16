"""Payment processing service for ContentFlow revenue."""

import os
import logging
import stripe
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import MetricEvent, Link
from app.utils.logger import logger

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

logger = logging.getLogger(__name__)


class PaymentProcessor:
    """Handle automated payments for ContentFlow revenue."""
    
    def __init__(self):
        self.stripe_key = os.getenv("STRIPE_SECRET_KEY")
        self.paypal_client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.paypal_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        
        if not self.stripe_key:
            logger.warning("Stripe API key not configured")
        if not self.paypal_client_id or not self.paypal_secret:
            logger.warning("PayPal credentials not configured")
    
    def calculate_monthly_revenue(self, db: Session, user_id: int = None) -> Dict[str, float]:
        """Calculate total monthly revenue from all sources."""
        try:
            # Query revenue from metric events
            from sqlalchemy import func, text
            from datetime import datetime, timedelta
            
            # Get current month start
            now = datetime.now()
            month_start = datetime(now.year, now.month, 1)
            
            # Calculate revenue from clicks and conversions
            revenue_query = db.execute(text("""
                SELECT 
                    platform,
                    COUNT(CASE WHEN kind = 'click' THEN 1 END) as clicks,
                    SUM(CASE WHEN amount_eur > 0 THEN amount_eur ELSE 0 END) as direct_revenue
                FROM metric_events 
                WHERE timestamp >= :month_start
                GROUP BY platform
            """), {"month_start": month_start}).fetchall()
            
            platform_revenue = {}
            total_revenue = 0.0
            
            for row in revenue_query:
                # Calculate estimated revenue from clicks (€0.25 per click average)
                click_revenue = float(row.clicks) * 0.25
                direct_revenue = float(row.direct_revenue or 0)
                platform_total = click_revenue + direct_revenue
                
                platform_revenue[row.platform] = platform_total
                total_revenue += platform_total
            
            platform_revenue["total"] = total_revenue
            platform_revenue["month"] = now.strftime("%Y-%m")
            
            logger.info(f"Monthly revenue calculated: €{total_revenue:.2f}")
            return platform_revenue
            
        except Exception as e:
            logger.error(f"Error calculating monthly revenue: {e}")
            return {"total": 0.0, "error": str(e)}
    
    def create_stripe_payout(self, amount_eur: float, description: str = "ContentFlow monthly revenue") -> Dict[str, Any]:
        """Create a Stripe payout for revenue."""
        try:
            if not self.stripe_key:
                return {"success": False, "error": "Stripe not configured"}
            
            # Convert EUR to cents
            amount_cents = int(amount_eur * 100)
            
            # Create payout
            payout = stripe.Payout.create(
                amount=amount_cents,
                currency="eur",
                description=description,
                method="instant"
            )
            
            logger.info(f"Stripe payout created: {payout.id} for €{amount_eur:.2f}")
            
            return {
                "success": True,
                "payout_id": payout.id,
                "amount": amount_eur,
                "status": payout.status,
                "estimated_arrival": payout.arrival_date
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe payout failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_paypal_access_token(self) -> Optional[str]:
        """Get PayPal access token for API calls."""
        try:
            if not self.paypal_client_id or not self.paypal_secret:
                return None
            
            url = "https://api.paypal.com/v1/oauth2/token"
            headers = {
                "Accept": "application/json",
                "Accept-Language": "en_US",
            }
            data = "grant_type=client_credentials"
            
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=(self.paypal_client_id, self.paypal_secret)
            )
            
            if response.status_code == 200:
                return response.json()["access_token"]
            else:
                logger.error(f"PayPal auth failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"PayPal auth error: {e}")
            return None
    
    def create_paypal_payout(self, amount_eur: float, recipient_email: str, description: str = "ContentFlow revenue") -> Dict[str, Any]:
        """Create a PayPal payout."""
        try:
            access_token = self.get_paypal_access_token()
            if not access_token:
                return {"success": False, "error": "PayPal authentication failed"}
            
            url = "https://api.paypal.com/v1/payments/payouts"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
            
            payout_data = {
                "sender_batch_header": {
                    "sender_batch_id": f"ContentFlow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "email_subject": "Vous avez reçu un paiement ContentFlow",
                    "email_message": f"Vos revenus ContentFlow: €{amount_eur:.2f}"
                },
                "items": [
                    {
                        "recipient_type": "EMAIL",
                        "amount": {
                            "value": f"{amount_eur:.2f}",
                            "currency": "EUR"
                        },
                        "receiver": recipient_email,
                        "note": description,
                        "sender_item_id": f"CF_{datetime.now().timestamp()}"
                    }
                ]
            }
            
            response = requests.post(url, json=payout_data, headers=headers)
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"PayPal payout created: {result['batch_header']['payout_batch_id']}")
                
                return {
                    "success": True,
                    "batch_id": result["batch_header"]["payout_batch_id"],
                    "amount": amount_eur,
                    "status": result["batch_header"]["batch_status"]
                }
            else:
                logger.error(f"PayPal payout failed: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"PayPal payout error: {e}")
            return {"success": False, "error": str(e)}
    
    def process_monthly_payout(self, db: Session, payment_method: str = "stripe", recipient_email: str = None) -> Dict[str, Any]:
        """Process automated monthly payout."""
        try:
            # Calculate revenue
            revenue_data = self.calculate_monthly_revenue(db)
            total_revenue = revenue_data.get("total", 0.0)
            
            # Check minimum payout threshold
            min_payout = float(os.getenv("MIN_PAYOUT_EUR", "50.0"))
            if total_revenue < min_payout:
                return {
                    "success": False,
                    "message": f"Revenue €{total_revenue:.2f} below minimum €{min_payout:.2f}",
                    "revenue": revenue_data
                }
            
            # Process payout based on method
            if payment_method == "stripe":
                result = self.create_stripe_payout(total_revenue)
            elif payment_method == "paypal" and recipient_email:
                result = self.create_paypal_payout(total_revenue, recipient_email)
            else:
                return {"success": False, "error": "Invalid payment method or missing email"}
            
            if result["success"]:
                # Record payout in metrics
                payout_event = MetricEvent(
                    platform="system",
                    kind="payout",
                    value=total_revenue,
                    amount_eur=total_revenue,
                    metadata_json=f'{{"method": "{payment_method}", "payout_data": {result}}}'
                )
                db.add(payout_event)
                db.commit()
                
                logger.info(f"Monthly payout processed: €{total_revenue:.2f} via {payment_method}")
            
            return {
                "success": result["success"],
                "amount": total_revenue,
                "method": payment_method,
                "revenue_breakdown": revenue_data,
                "payout_details": result
            }
            
        except Exception as e:
            logger.error(f"Monthly payout processing failed: {e}")
            return {"success": False, "error": str(e)}


def get_payment_processor() -> PaymentProcessor:
    """Get configured payment processor instance."""
    return PaymentProcessor()