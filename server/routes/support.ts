import { Router } from "express";
import { createTicket } from "../services/supportBot";
import { randomUUID } from "crypto";

const router = Router();

// Get partner ID from request
function getPartnerId(req: any): string | null {
  return req.cookies?.partner_id || req.headers['x-partner-id'] || null;
}

// Support form page
router.get("/new", (req, res) => {
  res.setHeader("Content-Type", "text/html");
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Support — ContentFlow</title>
      <style>
        body { 
          font-family: system-ui, -apple-system, sans-serif; 
          max-width: 720px; 
          margin: 40px auto; 
          padding: 20px;
          background: #f8fafc;
        }
        .container {
          background: white;
          padding: 30px;
          border-radius: 12px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        h2 { 
          color: #1f2937; 
          margin-bottom: 20px;
          font-size: 24px;
        }
        input, textarea { 
          width: 100%; 
          padding: 12px; 
          border: 1px solid #d1d5db; 
          border-radius: 8px;
          font-size: 14px;
          margin-bottom: 16px;
          box-sizing: border-box;
        }
        input:focus, textarea:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        button { 
          background: #3b82f6;
          color: white;
          padding: 12px 24px; 
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }
        button:hover {
          background: #2563eb;
        }
        .help-text {
          color: #6b7280;
          font-size: 13px;
          margin-bottom: 20px;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h2>💬 Support ContentFlow</h2>
        <p class="help-text">
          Besoin d'aide ? Décris ton problème ci-dessous. Notre bot répond immédiatement pour les questions courantes.
        </p>
        <form method="post" action="/support/new">
          <input name="subject" placeholder="Sujet de votre demande" required>
          <textarea name="body" placeholder="Décris ton problème en détail..." rows="6" required></textarea>
          <button type="submit">📨 Envoyer la demande</button>
        </form>
      </div>
    </body>
    </html>
  `);
});

// Create support ticket
router.post("/new", async (req, res) => {
  try {
    const { subject, body } = req.body;
    const partnerId = getPartnerId(req);
    
    if (!subject || !body) {
      return res.status(400).send(`
        <div style="max-width: 720px; margin: 40px auto; padding: 20px; font-family: system-ui;">
          <h3>❌ Erreur</h3>
          <p>Le sujet et le message sont requis.</p>
          <a href="/support/new">← Retour</a>
        </div>
      `);
    }
    
    const ticketId = await createTicket(partnerId, subject, body);
    res.redirect(`/support/thanks?id=${ticketId}`);
  } catch (error) {
    console.error("Error creating ticket:", error);
    res.status(500).send(`
      <div style="max-width: 720px; margin: 40px auto; padding: 20px; font-family: system-ui;">
        <h3>❌ Erreur</h3>
        <p>Impossible de créer le ticket. Veuillez réessayer.</p>
        <a href="/support/new">← Retour</a>
      </div>
    `);
  }
});

// Thank you page
router.get("/thanks", (req, res) => {
  const { id } = req.query;
  res.setHeader("Content-Type", "text/html");
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Demande envoyée — ContentFlow</title>
      <style>
        body { 
          font-family: system-ui, -apple-system, sans-serif; 
          max-width: 720px; 
          margin: 40px auto; 
          padding: 20px;
          background: #f8fafc;
        }
        .container {
          background: white;
          padding: 30px;
          border-radius: 12px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          text-align: center;
        }
        h3 { 
          color: #059669; 
          font-size: 24px;
          margin-bottom: 16px;
        }
        p { 
          color: #4b5563; 
          line-height: 1.6;
          margin-bottom: 20px;
        }
        .ticket-id {
          background: #f3f4f6;
          padding: 8px 12px;
          border-radius: 6px;
          font-family: monospace;
          color: #374151;
          display: inline-block;
          margin: 10px 0;
        }
        a {
          color: #3b82f6;
          text-decoration: none;
          font-weight: 500;
        }
        a:hover {
          text-decoration: underline;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h3>✅ Demande reçue</h3>
        <p>Votre ticket de support a été créé avec succès.</p>
        <div class="ticket-id">Ticket #${id}</div>
        <p>Une réponse automatique a été envoyée. Si une intervention humaine est nécessaire, vous recevrez une réponse dans les 24h.</p>
        <a href="/partner-profile">← Retour au portail partenaire</a>
      </div>
    </body>
    </html>
  `);
});

export default router;