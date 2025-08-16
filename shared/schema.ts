import { sql } from "drizzle-orm";
import { pgTable, text, varchar, timestamp, index } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

// Partners table for BYOP system
export const partners = pgTable("partners", {
  id: varchar("id").primaryKey(),
  email: varchar("email").notNull().unique(),
  name: varchar("name"),
  status: varchar("status").default("active"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
  lastLogin: timestamp("last_login", { withTimezone: true }),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
}, (table) => [
  index("idx_partners_email").on(table.email),
]);

// Payouts table
export const payouts = pgTable("payouts", {
  id: varchar("id").primaryKey(),
  partnerId: varchar("partner_id").notNull(),
  status: varchar("status").notNull().default("pending"),
  amountDueEur: varchar("amount_due_eur").notNull(),
  method: varchar("method"), // paypal|bank
  methodData: text("method_data"), // JSON data
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
  processedAt: timestamp("processed_at", { withTimezone: true }),
}, (table) => [
  index("idx_payouts_partner").on(table.partnerId),
  index("idx_payouts_status").on(table.status),
]);

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export const insertPartnerSchema = createInsertSchema(partners).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertPayoutSchema = createInsertSchema(payouts).omit({
  id: true,
  createdAt: true,
  processedAt: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;
export type Partner = typeof partners.$inferSelect;
export type InsertPartner = z.infer<typeof insertPartnerSchema>;
export type Payout = typeof payouts.$inferSelect;
export type InsertPayout = z.infer<typeof insertPayoutSchema>;

// These types will be defined after the table definitions

// Support system tables
export const tickets = pgTable("tickets", {
  id: varchar("id").primaryKey(),
  partnerId: varchar("partner_id"),
  subject: varchar("subject").notNull(),
  status: varchar("status").notNull().default("open"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
});

export const ticketMessages = pgTable("ticket_messages", {
  id: varchar("id").primaryKey(),
  ticketId: varchar("ticket_id").notNull(),
  fromSupport: varchar("from_support").notNull().default("false"),
  message: text("message").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
});

export const partnerFlags = pgTable("partner_flags", {
  id: varchar("id").primaryKey(),
  partnerId: varchar("partner_id").notNull(),
  flagType: varchar("flag_type").notNull(),
  reason: text("reason"),
  isActive: varchar("is_active").notNull().default("true"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
});

export const metricEvents = pgTable("metric_events", {
  id: varchar("id").primaryKey(),
  partnerId: varchar("partner_id"),
  eventType: varchar("event_type").notNull(),
  eventData: text("event_data"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
});

// Content submissions and generated content
export const contentSubmissions = pgTable("content_submissions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  partner_id: varchar("partner_id").notNull(),
  user_message: varchar("user_message", { length: 1000 }),
  generated_title: varchar("generated_title", { length: 200 }),
  generated_description: varchar("generated_description", { length: 1000 }),
  generated_hashtags: varchar("generated_hashtags", { length: 500 }),
  cta: varchar("cta", { length: 200 }),
  compliance_score: varchar("compliance_score").default("0"),
  quality_score: varchar("quality_score").default("0"),
  approved: varchar("approved").default("false"),
  status: varchar("status", { length: 50 }).default("draft"), // draft, published, archived
  published_platforms: text("published_platforms").default("[]"), // JSON array of platforms
  media_files: text("media_files").default("[]"), // JSON array of file info
  created_at: timestamp("created_at", { withTimezone: true }).defaultNow(),
  updated_at: timestamp("updated_at", { withTimezone: true }).defaultNow(),
}, (table) => [
  index("idx_content_partner").on(table.partner_id),
  index("idx_content_status").on(table.status),
]);

// Social media connections for partners
export const socialConnections = pgTable("social_connections", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  partner_id: varchar("partner_id").notNull(),
  platform: varchar("platform", { length: 50 }).notNull(), // instagram, facebook, twitter, tiktok, etc.
  platform_user_id: varchar("platform_user_id").notNull(),
  access_token: varchar("access_token", { length: 500 }),
  refresh_token: varchar("refresh_token", { length: 500 }),
  token_expires_at: timestamp("token_expires_at", { withTimezone: true }),
  account_name: varchar("account_name", { length: 100 }),
  account_url: varchar("account_url", { length: 200 }),
  is_active: varchar("is_active").default("true"),
  permissions: text("permissions").default("[]"), // JSON scopes granted
  created_at: timestamp("created_at", { withTimezone: true }).defaultNow(),
  updated_at: timestamp("updated_at", { withTimezone: true }).defaultNow(),
}, (table) => [
  index("idx_social_partner").on(table.partner_id),
  index("idx_social_platform").on(table.platform),
]);

export type Ticket = typeof tickets.$inferSelect;
export type TicketMessage = typeof ticketMessages.$inferSelect;
export type PartnerFlag = typeof partnerFlags.$inferSelect;
export type MetricEvent = typeof metricEvents.$inferSelect;
export type ContentSubmission = typeof contentSubmissions.$inferSelect;
export type InsertContentSubmission = typeof contentSubmissions.$inferInsert;
export type SocialConnection = typeof socialConnections.$inferSelect;
export type InsertSocialConnection = typeof socialConnections.$inferInsert;
