import { randomUUID } from "crypto";
import { and, inArray, lt, eq } from "drizzle-orm";
import { db } from "../db";
import { tickets, ticketMessages, type InsertTicket, type InsertTicketMessage } from "@shared/support";

// FAQ patterns and responses
const FAQ = [
  {
    pattern: /payout|paiement|versement/i,
    response: "Paiements: seuil {min}€, hebdo. Disponible: {available}€. Réserve: {reserved}€ (libérée sous {days}j)."
  },
  {
    pattern: /magic|login|lien/i,
    response: "Login: /partner-auth avec ton email."
  },
  {
    pattern: /dmca|copyright/i,
    response: "DMCA: on met en quarantaine et on traite sous 72h."
  },
  {
    pattern: /help|aide|support/i,
    response: "Support disponible 24/7. Décris ton problème et nous te répondrons rapidement."
  }
];

// Get partner balances (mock implementation)
function getPartnerBalances(partnerId: string | null): { available: number; reserved: number } {
  // In real implementation, this would query the partner earnings/balances
  return {
    available: partnerId ? 23.80 : 0,
    reserved: partnerId ? 45.20 : 0
  };
}

// Generate automatic bot reply based on message content
function generateAutoReply(partnerId: string | null, body: string): string {
  const balances = getPartnerBalances(partnerId);
  
  for (const faq of FAQ) {
    if (faq.pattern.test(body || "")) {
      return faq.response
        .replace("{min}", "10")
        .replace("{available}", balances.available.toString())
        .replace("{reserved}", balances.reserved.toString())
        .replace("{days}", "30");
    }
  }
  
  return "Reçu. Le bot a routé ta demande. Réponse humaine si nécessaire <24h. Stats: /partner-profile.";
}

// Create a new support ticket
export async function createTicket(
  partnerId: string | null,
  subject: string,
  body: string,
  kind: string = "faq"
): Promise<string> {
  const ticketId = randomUUID();
  
  // Create ticket
  const ticketData: InsertTicket = {
    partnerId,
    kind,
    subject: subject || (body || "").substring(0, 60),
    status: "open",
    priority: "P3"
  };
  
  await db.insert(tickets).values({ ...ticketData, id: ticketId });
  
  // Add user message
  const userMessage: InsertTicketMessage = {
    ticketId,
    author: "user",
    body: body || ""
  };
  
  await db.insert(ticketMessages).values({ ...userMessage, id: randomUUID() });
  
  // Generate and add bot reply
  const botReply = generateAutoReply(partnerId, body || "");
  const botMessage: InsertTicketMessage = {
    ticketId,
    author: "bot",
    body: botReply
  };
  
  await db.insert(ticketMessages).values({ ...botMessage, id: randomUUID() });
  
  // Update ticket with bot reply and status
  await db.update(tickets)
    .set({
      lastBotReply: botReply,
      status: "bot_answered",
      updatedAt: new Date()
    })
    .where(eq(tickets.id, ticketId));
  
  return ticketId;
}

// Auto-close stale tickets
export async function autoCloseStaleTickets(): Promise<number> {
  const DAYS_TO_AUTO_CLOSE = 5;
  const cutoff = new Date(Date.now() - DAYS_TO_AUTO_CLOSE * 24 * 60 * 60 * 1000);
  
  const result = await db.update(tickets)
    .set({ status: "closed", updatedAt: new Date() })
    .where(
      and(
        inArray(tickets.status, ["bot_answered", "awaiting_user"]),
        lt(tickets.updatedAt, cutoff)
      )
    );
  
  return (result as any).rowCount || 0;
}

// Support configuration
export const SUPPORT_CONFIG = {
  FEATURE_SUPPORTBOT: true,
  TICKET_AUTO_CLOSE_DAYS: 5,
  PAYOUT_MIN_EUR: 10,
  PAYOUT_RELEASE_DAYS: 30
};