import { randomUUID } from "crypto";
import { and, gte, sql, eq, isNotNull, inArray } from "drizzle-orm";
import { db } from "../db";
import { partnerFlags, metricEvents, type InsertPartnerFlag, type InsertMetricEvent } from "@shared/support";

// Risk detection configuration
export const RISK_CONFIG = {
  FEATURE_RISKBOT: true,
  RISK_VELOCITY_MAX_CLICKS_10M: 40,
  RISK_HOLD_DAYS: 30,
  PAYOUT_APPROVAL_THRESHOLD_EUR: 200
};

// Record a metric event (click, view, conversion)
export async function recordMetricEvent(
  partnerId: string | null,
  kind: "click" | "view" | "conversion",
  metadata: any = {}
): Promise<void> {
  const eventData: InsertMetricEvent = {
    partnerId,
    kind,
    metadata: JSON.stringify(metadata)
  };
  
  await db.insert(metricEvents).values({ ...eventData, id: randomUUID() });
}

// Sweep for click velocity violations
export async function sweepClickVelocity(maxClicks: number = RISK_CONFIG.RISK_VELOCITY_MAX_CLICKS_10M): Promise<number> {
  const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);
  
  // Find partners with excessive clicks in last 10 minutes
  const suspiciousPartners = await db
    .select({
      partnerId: metricEvents.partnerId,
      clickCount: sql<number>`count(*)`
    })
    .from(metricEvents)
    .where(
      and(
        eq(metricEvents.kind, "click"),
        gte(metricEvents.ts, tenMinutesAgo),
        isNotNull(metricEvents.partnerId)
      )
    )
    .groupBy(metricEvents.partnerId)
    .having(sql`count(*) >= ${maxClicks}`);
  
  let flaggedCount = 0;
  
  for (const { partnerId } of suspiciousPartners) {
    if (!partnerId) continue;
    
    // Check if already flagged
    const existingFlag = await db
      .select()
      .from(partnerFlags)
      .where(
        and(
          eq(partnerFlags.partnerId, partnerId),
          eq(partnerFlags.flag, "hold")
        )
      )
      .limit(1);
    
    if (existingFlag.length === 0) {
      // Add hold flag
      const flagData: InsertPartnerFlag = {
        partnerId,
        flag: "hold",
        valueJson: JSON.stringify({ reason: "velocity", detected_at: new Date().toISOString() })
      };
      
      await db.insert(partnerFlags).values({ ...flagData, id: randomUUID() });
      flaggedCount++;
    }
  }
  
  return flaggedCount;
}

// Check if partner is on hold
export async function isPartnerOnHold(partnerId: string): Promise<boolean> {
  const holdFlags = await db
    .select()
    .from(partnerFlags)
    .where(
      and(
        eq(partnerFlags.partnerId, partnerId),
        eq(partnerFlags.flag, "hold")
      )
    )
    .limit(1);
  
  return holdFlags.length > 0;
}

// Add a flag to a partner
export async function addPartnerFlag(
  partnerId: string,
  flag: "hold" | "fraud" | "dmca",
  metadata: any = {}
): Promise<string> {
  const flagData: InsertPartnerFlag = {
    partnerId,
    flag,
    valueJson: JSON.stringify(metadata)
  };
  
  const id = randomUUID();
  await db.insert(partnerFlags).values({ ...flagData, id });
  return id;
}

// Remove a flag from a partner
export async function removePartnerFlag(partnerId: string, flag: string): Promise<boolean> {
  const result = await db
    .delete(partnerFlags)
    .where(
      and(
        eq(partnerFlags.partnerId, partnerId),
        eq(partnerFlags.flagType, flag)
      )
    );
  
  return ((result as any).rowCount || 0) > 0;
}

// Get all flags for a partner
export async function getPartnerFlags(partnerId: string) {
  return await db
    .select()
    .from(partnerFlags)
    .where(eq(partnerFlags.partnerId, partnerId))
    .orderBy(partnerFlags.createdAt);
}

// Get all held partners (admin view)
export async function getHeldPartners() {
  return await db
    .select()
    .from(partnerFlags)
    .where(eq(partnerFlags.flag, "hold"))
    .orderBy(partnerFlags.createdAt);
}