import { sql } from "drizzle-orm";
import { pgTable, text, varchar, integer, decimal, timestamp, boolean, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const cases = pgTable("cases", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  customerId: text("customer_id").notNull(),
  callId: text("call_id").notNull(),
  scenario: text("scenario").notNull(),
  priority: integer("priority").notNull(),
  status: text("status").notNull(),
  risk: text("risk").notNull(),
  financialImpact: text("financial_impact"),
  exchanges: integer("exchanges").default(0),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const transcripts = pgTable("transcripts", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  caseId: varchar("case_id").references(() => cases.id),
  speaker: text("speaker").notNull(),
  content: text("content").notNull(),
  timestamp: timestamp("timestamp").defaultNow(),
});

export const analyses = pgTable("analyses", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  caseId: varchar("case_id").references(() => cases.id),
  intent: text("intent").notNull(),
  confidence: decimal("confidence", { precision: 3, scale: 2 }),
  sentiment: text("sentiment").notNull(),
  risks: jsonb("risks").$type<Array<{ label: string; value: number }>>(),
});

export const actions = pgTable("actions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  caseId: varchar("case_id").references(() => cases.id),
  action: text("action").notNull(),
  category: text("category").notNull(),
  risk: text("risk").notNull(),
  impact: text("impact").notNull(),
  submittedAt: timestamp("submitted_at").defaultNow(),
  decision: text("decision").notNull(),
  autoCount: integer("auto_count").default(0),
  doneCount: integer("done_count").default(0),
  pendingCount: integer("pending_count").default(0),
});

export const metrics = pgTable("metrics", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  totalTranscripts: integer("total_transcripts").default(0),
  transcriptsPrev: integer("transcripts_prev").default(0),
  completeRate: decimal("complete_rate", { precision: 4, scale: 3 }),
  completeRatePrev: decimal("complete_rate_prev", { precision: 4, scale: 3 }),
  avgProcessingTime: decimal("avg_processing_time", { precision: 5, scale: 2 }),
  avgProcessingTimePrev: decimal("avg_processing_time_prev", { precision: 5, scale: 2 }),
  stageData: jsonb("stage_data").$type<{
    transcript: { ready: number; processing: number };
    analysis: { queue: number; processing: number };
    plan: { queue: number; generating: number };
    approval: { pending: number; approved: number };
    execution: { running: number; complete: number };
  }>(),
  lastUpdated: timestamp("last_updated").defaultNow(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export const insertCaseSchema = createInsertSchema(cases).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertTranscriptSchema = createInsertSchema(transcripts).omit({
  id: true,
  timestamp: true,
});

export const insertAnalysisSchema = createInsertSchema(analyses).omit({
  id: true,
});

export const insertActionSchema = createInsertSchema(actions).omit({
  id: true,
  submittedAt: true,
});

export type User = typeof users.$inferSelect;
export type InsertUser = z.infer<typeof insertUserSchema>;
export type Case = typeof cases.$inferSelect;
export type InsertCase = z.infer<typeof insertCaseSchema>;
export type Transcript = typeof transcripts.$inferSelect;
export type InsertTranscript = z.infer<typeof insertTranscriptSchema>;
export type Analysis = typeof analyses.$inferSelect;
export type InsertAnalysis = z.infer<typeof insertAnalysisSchema>;
export type Action = typeof actions.$inferSelect;
export type InsertAction = z.infer<typeof insertActionSchema>;
export type Metrics = typeof metrics.$inferSelect;
