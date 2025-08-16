import { Router } from "express";
import { eq, and } from "drizzle-orm";
import { db } from "../db";
import { partnerFlags, payouts } from "@shared/schema";
import { removePartnerFlag, getHeldPartners } from "../services/riskBot";

const router = Router();

// Admin secret check
function checkAdminAuth(req: any): boolean {
  const adminSecret = req.headers['x-admin-secret'];
  const expectedSecret = process.env.ADMIN_SECRET || "change_me";
  return adminSecret === expectedSecret;
}

// View held partners
router.get("/holds", async (req, res) => {
  if (!checkAdminAuth(req)) {
    return res.status(401).send("Unauthorized - Missing or invalid x-admin-secret header");
  }
  
  try {
    const heldPartners = await getHeldPartners();
    
    const htmlRows = heldPartners.map(flag => {
      const valueData = JSON.parse(flag.valueJson || "{}");
      return `
        <tr>
          <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">${flag.partnerId}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">${valueData.reason || 'Unknown'}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">${flag.createdAt?.toISOString().split('T')[0] || 'N/A'}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">
            <a href="/ops/unhold?pid=${flag.partnerId}" 
               style="color: #dc2626; text-decoration: none; font-weight: 500;">
              🔓 Unhold
            </a>
          </td>
        </tr>
      `;
    }).join('');
    
    res.setHeader("Content-Type", "text/html");
    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Admin - Held Partners</title>
        <style>
          body { font-family: system-ui; max-width: 1200px; margin: 20px auto; padding: 20px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th { background: #f3f4f6; padding: 12px 8px; text-align: left; font-weight: 600; }
          .header { background: #1f2937; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        </style>
      </head>
      <body>
        <div class="header">
          <h2>🚫 Held Partners - Admin Panel</h2>
          <p>Partners currently on hold for risk violations</p>
        </div>
        
        <table>
          <thead>
            <tr>
              <th>Partner ID</th>
              <th>Reason</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${htmlRows || '<tr><td colspan="4" style="padding: 20px; text-align: center; color: #6b7280;">No held partners</td></tr>'}
          </tbody>
        </table>
        
        <div style="margin-top: 30px; padding: 15px; background: #fef3c7; border-radius: 8px;">
          <strong>📋 Admin Actions:</strong><br>
          • <a href="/ops/payouts/pending">View Pending Payouts</a><br>
          • Header required: <code>x-admin-secret: ${process.env.ADMIN_SECRET || 'change_me'}</code>
        </div>
      </body>
      </html>
    `);
  } catch (error) {
    console.error("Error fetching held partners:", error);
    res.status(500).send("Error fetching held partners");
  }
});

// Unhold a partner
router.get("/unhold", async (req, res) => {
  if (!checkAdminAuth(req)) {
    return res.status(401).send("Unauthorized");
  }
  
  const { pid } = req.query;
  if (!pid) {
    return res.status(400).send("Partner ID required");
  }
  
  try {
    const removed = await removePartnerFlag(pid as string, "hold");
    if (removed) {
      res.redirect("/ops/holds");
    } else {
      res.status(404).send("Hold flag not found");
    }
  } catch (error) {
    console.error("Error removing hold:", error);
    res.status(500).send("Error removing hold");
  }
});

// View pending payouts
router.get("/payouts/pending", async (req, res) => {
  if (!checkAdminAuth(req)) {
    return res.status(401).send("Unauthorized");
  }
  
  try {
    const THRESHOLD = parseFloat(process.env.PAYOUT_APPROVAL_THRESHOLD_EUR || "200");
    
    const pendingPayouts = await db
      .select()
      .from(payouts)
      .where(
        and(
          eq(payouts.status, "approved"),
          // Note: amountDueEur is stored as varchar, need to cast for comparison
        )
      );
    
    // Filter by amount (since we can't do numeric comparison on varchar in query)
    const filteredPayouts = pendingPayouts.filter(p => 
      parseFloat(p.amountDueEur) >= THRESHOLD
    );
    
    const htmlRows = filteredPayouts.map(payout => `
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">${payout.partnerId}</td>
        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">€${payout.amountDueEur}</td>
        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">${payout.method || 'N/A'}</td>
        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">${payout.createdAt?.toISOString().split('T')[0] || 'N/A'}</td>
        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">
          <a href="/ops/payouts/${payout.id}/mark-paid" 
             style="color: #059669; text-decoration: none; font-weight: 500;">
            ✅ Mark Paid
          </a>
        </td>
      </tr>
    `).join('');
    
    res.setHeader("Content-Type", "text/html");
    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Admin - Pending Payouts</title>
        <style>
          body { font-family: system-ui; max-width: 1200px; margin: 20px auto; padding: 20px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th { background: #f3f4f6; padding: 12px 8px; text-align: left; font-weight: 600; }
          .header { background: #1f2937; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        </style>
      </head>
      <body>
        <div class="header">
          <h2>💰 Pending Payouts - Admin Panel</h2>
          <p>Payouts requiring manual approval (≥ €${THRESHOLD})</p>
        </div>
        
        <table>
          <thead>
            <tr>
              <th>Partner ID</th>
              <th>Amount</th>
              <th>Method</th>
              <th>Requested</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${htmlRows || '<tr><td colspan="5" style="padding: 20px; text-align: center; color: #6b7280;">No pending payouts</td></tr>'}
          </tbody>
        </table>
      </body>
      </html>
    `);
  } catch (error) {
    console.error("Error fetching pending payouts:", error);
    res.status(500).send("Error fetching pending payouts");
  }
});

// Mark payout as paid
router.get("/payouts/:id/mark-paid", async (req, res) => {
  if (!checkAdminAuth(req)) {
    return res.status(401).send("Unauthorized");
  }
  
  const { id } = req.params;
  
  try {
    const result = await db
      .update(payouts)
      .set({ 
        status: "paid", 
        processedAt: new Date() 
      })
      .where(eq(payouts.id, id));
    
    if ((result as any).rowCount && (result as any).rowCount > 0) {
      res.redirect("/ops/payouts/pending");
    } else {
      res.status(404).send("Payout not found");
    }
  } catch (error) {
    console.error("Error marking payout as paid:", error);
    res.status(500).send("Error updating payout");
  }
});

export default router;