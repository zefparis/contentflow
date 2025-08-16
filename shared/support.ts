import { pgTable, varchar, text, timestamp, index } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Tickets table for support system
export const tickets = pgTable("tickets", {
  id: varchar("id").primaryKey(),
  partnerId: varchar("partner_id"),
  kind: varchar("kind").notNull(),
  status: varchar("status").notNull().default("open"),
  priority: varchar("priority").notNull().default("P3"),
  subject: varchar("subject"),
  lastBotReply: text("last_bot_reply"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
}, (table) => [
  index("idx_tickets_partner").on(table.partnerId),
  index("idx_tickets_status").on(table.status),
]);

// Ticket messages for conversation history
export const ticketMessages = pgTable("ticket_messages", {
  id: varchar("id").primaryKey(),
  ticketId: varchar("ticket_id").notNull(),
  author: varchar("author").notNull(), // user|bot|admin
  body: text("body").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
}, (table) => [
  index("idx_messages_ticket").on(table.ticketId),
]);

// Partner flags for risk management
export const partnerFlags = pgTable("partner_flags", {
  id: varchar("id").primaryKey(),
  partnerId: varchar("partner_id").notNull(),
  flag: varchar("flag").notNull(), // hold|fraud|dmca
  valueJson: text("value_json").notNull().default("{}"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
}, (table) => [
  index("idx_flags_partner").on(table.partnerId),
  index("idx_flags_type").on(table.flag),
]);

// Metric events for tracking clicks and actions
export const metricEvents = pgTable("metric_events", {
  id: varchar("id").primaryKey(),
  partnerId: varchar("partner_id"),
  kind: varchar("kind").notNull(), // click|view|conversion
  ts: timestamp("ts", { withTimezone: true }).defaultNow(),
  metadata: text("metadata").default("{}"),
}, (table) => [
  index("idx_metrics_partner_time").on(table.partnerId, table.ts),
  index("idx_metrics_kind_time").on(table.kind, table.ts),
]);

// Schemas for validation
export const insertTicketSchema = createInsertSchema(tickets).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertTicketMessageSchema = createInsertSchema(ticketMessages).omit({
  id: true,
  createdAt: true,
});

export const insertPartnerFlagSchema = createInsertSchema(partnerFlags).omit({
  id: true,
  createdAt: true,
});

export const insertMetricEventSchema = createInsertSchema(metricEvents).omit({
  id: true,
  ts: true,
});

// Types
export type Ticket = typeof tickets.$inferSelect;
export type InsertTicket = z.infer<typeof insertTicketSchema>;
export type TicketMessage = typeof ticketMessages.$inferSelect;
export type InsertTicketMessage = z.infer<typeof insertTicketMessageSchema>;
export type PartnerFlag = typeof partnerFlags.$inferSelect;
export type InsertPartnerFlag = z.infer<typeof insertPartnerFlagSchema>;
export type MetricEvent = typeof metricEvents.$inferSelect;
export type InsertMetricEvent = z.infer<typeof insertMetricEventSchema>;