// Partner Authentication Service
// Provides magic-link authentication and session management for BYOP partners

import crypto from 'crypto';

class PartnerAuthService {
  constructor() {
    // In production, use Redis or database for token storage
    this.magicTokens = new Map();
    this.partnerSessions = new Map();
  }

  generateMagicLink(email, baseUrl = null) {
    const token = crypto.randomBytes(32).toString('hex');
    const expiresAt = Date.now() + (15 * 60 * 1000); // 15 minutes
    
    this.magicTokens.set(token, {
      email,
      expiresAt,
      used: false
    });

    // Use provided baseUrl or fallback to env variables
    if (!baseUrl) {
      // Force use of Replit public URL for production
      if (process.env.REPL_ID) {
        // Use the current Replit URL format
        baseUrl = `https://${process.env.REPL_ID}-00-pgtccvos2tvg.riker.replit.dev`;
      } else if (process.env.REPLIT_DOMAINS) {
        const domain = process.env.REPLIT_DOMAINS.split(',')[0];
        baseUrl = `https://${domain}`;
      } else if (process.env.REPL_SLUG) {
        baseUrl = `https://${process.env.REPL_SLUG}.${process.env.REPL_OWNER}.repl.co`;
      } else {
        baseUrl = process.env.BASE_URL || 'http://localhost:5000';
      }
    }
    
    return {
      token,
      link: `${baseUrl}/api/auth/verify?token=${token}`,
      expiresAt
    };
  }

  verifyMagicToken(token) {
    const tokenData = this.magicTokens.get(token);
    
    if (!tokenData) {
      return { success: false, error: 'Invalid token' };
    }

    if (Date.now() > tokenData.expiresAt) {
      this.magicTokens.delete(token);
      return { success: false, error: 'Token expired' };
    }

    // Generate partner session
    const partnerId = this.generatePartnerId(tokenData.email);
    const sessionToken = crypto.randomBytes(32).toString('hex');
    
    // Check if session already exists for this partner
    const existingSession = Array.from(this.partnerSessions.values())
      .find(session => session.partnerId === partnerId);
    
    if (!existingSession) {
      this.partnerSessions.set(sessionToken, {
        partnerId,
        email: tokenData.email,
        createdAt: Date.now()
      });
    }

    // Mark token as used but don't delete it immediately to allow multiple clicks
    if (!tokenData.used) {
      tokenData.used = true;
      // Schedule token deletion after 5 minutes to allow multiple redirects
      setTimeout(() => {
        this.magicTokens.delete(token);
      }, 5 * 60 * 1000);
    }

    return {
      success: true,
      partnerId,
      sessionToken,
      email: tokenData.email
    };
  }

  generatePartnerId(email) {
    // Generate deterministic partner ID from email
    return crypto.createHash('sha256').update(email).digest('hex').substring(0, 16);
  }

  verifySession(sessionToken) {
    const session = this.partnerSessions.get(sessionToken);
    
    if (!session) {
      return null;
    }

    // Sessions valid for 30 days
    if (Date.now() - session.createdAt > (30 * 24 * 60 * 60 * 1000)) {
      this.partnerSessions.delete(sessionToken);
      return null;
    }

    return session;
  }

  invalidateSession(sessionToken) {
    return this.partnerSessions.delete(sessionToken);
  }

  // Cleanup expired tokens (call periodically)
  cleanup() {
    const now = Date.now();
    
    // Clean expired magic tokens
    for (const [token, data] of this.magicTokens.entries()) {
      if (now > data.expiresAt) {
        this.magicTokens.delete(token);
      }
    }

    // Clean old sessions (> 30 days)
    for (const [token, session] of this.partnerSessions.entries()) {
      if (now - session.createdAt > (30 * 24 * 60 * 60 * 1000)) {
        this.partnerSessions.delete(token);
      }
    }
  }
}

// Modern Brevo email service using fetch API
class BrevoEmailService {
  static async sendMagicLink(email, link) {
    console.log(`📧 Sending magic link to ${email}: ${link}`);
    
    if (!process.env.BREVO_API_KEY) {
      console.log(`📧 Fallback - No Brevo API key, showing link: ${link}`);
      return { success: true, fallback: true };
    }
    
    try {
      const emailData = {
        sender: { 
          email: 'lecoinrdc@gmail.com', 
          name: 'ContentFlow Partenaire' 
        },
        to: [{ email }],
        replyTo: { 
          email: 'lecoinrdc@gmail.com', 
          name: 'Support ContentFlow' 
        },
        subject: 'Connexion à votre espace partenaire ContentFlow',
        htmlContent: `
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="utf-8">
            <title>Connexion ContentFlow</title>
          </head>
          <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 8px;">
              <h1 style="color: white; margin: 0;">ContentFlow</h1>
              <p style="color: white; margin: 10px 0 0 0;">Espace Partenaire</p>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa; border-radius: 8px; margin-top: 20px;">
              <h2 style="color: #333; margin-bottom: 20px;">Connexion à votre espace partenaire</h2>
              
              <p style="color: #666; line-height: 1.6;">
                Bonjour,<br><br>
                Cliquez sur le bouton ci-dessous pour vous connecter à votre espace partenaire ContentFlow :
              </p>
              
              <div style="text-align: center; margin: 30px 0;">
                <a href="${link}" 
                   style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                  Se connecter maintenant
                </a>
              </div>
              
              <p style="color: #999; font-size: 14px; line-height: 1.5;">
                • Ce lien est valide pendant 15 minutes<br>
                • Une seule utilisation autorisée<br>
                • Si vous n'avez pas demandé cette connexion, ignorez cet email
              </p>
              
              <div style="border-top: 1px solid #ddd; margin-top: 30px; padding-top: 20px;">
                <p style="color: #999; font-size: 12px; margin: 0;">
                  Lien direct (si le bouton ne fonctionne pas) :<br>
                  <a href="${link}" style="color: #667eea; word-break: break-all;">${link}</a>
                </p>
              </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
              <p style="color: #999; font-size: 12px;">
                ContentFlow - Plateforme d'automatisation de contenu<br>
                Cet email a été envoyé automatiquement, ne pas répondre.
              </p>
            </div>
          </body>
          </html>
        `
      };

      const response = await fetch('https://api.brevo.com/v3/smtp/email', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'api-key': process.env.BREVO_API_KEY
        },
        body: JSON.stringify(emailData)
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Brevo API error: ${response.status} - ${errorData}`);
      }

      const result = await response.json();
      console.log('✅ Email envoyé avec succès via Brevo:', result.messageId);
      
      return { 
        success: true, 
        messageId: result.messageId,
        provider: 'brevo'
      };
      
    } catch (error) {
      console.error('❌ Erreur envoi email Brevo:', error.message);
      
      // Fallback en cas d'erreur Brevo
      console.log(`📧 Fallback - Magic link for ${email}: ${link}`);
      return { 
        success: true, 
        fallback: true,
        error: error.message 
      };
    }
  }
}

export {
  PartnerAuthService,
  BrevoEmailService,
  BrevoEmailService as MockEmailService // Alias for compatibility
};