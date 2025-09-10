import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertCaseSchema, insertTranscriptSchema, insertAnalysisSchema, insertActionSchema } from "@shared/schema";

export async function registerRoutes(app: Express): Promise<Server> {
  // Metrics endpoint
  app.get("/api/metrics", async (_req, res) => {
    try {
      const metrics = await storage.getMetrics();
      res.json(metrics);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch metrics" });
    }
  });

  // Cases endpoints
  app.get("/api/cases", async (req, res) => {
    try {
      const { priority, status, search } = req.query;
      const cases = await storage.getCases({
        priority: priority as string,
        status: status as string,
        search: search as string,
      });
      res.json(cases);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch cases" });
    }
  });

  app.get("/api/cases/:id", async (req, res) => {
    try {
      const case_ = await storage.getCase(req.params.id);
      if (!case_) {
        return res.status(404).json({ error: "Case not found" });
      }
      res.json(case_);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch case" });
    }
  });

  app.post("/api/cases", async (req, res) => {
    try {
      const validatedData = insertCaseSchema.parse(req.body);
      const case_ = await storage.createCase(validatedData);
      res.status(201).json(case_);
    } catch (error) {
      res.status(400).json({ error: "Invalid case data" });
    }
  });

  app.patch("/api/cases/:id", async (req, res) => {
    try {
      const case_ = await storage.updateCase(req.params.id, req.body);
      if (!case_) {
        return res.status(404).json({ error: "Case not found" });
      }
      res.json(case_);
    } catch (error) {
      res.status(500).json({ error: "Failed to update case" });
    }
  });

  // Transcripts endpoints
  app.get("/api/cases/:caseId/transcripts", async (req, res) => {
    try {
      const transcripts = await storage.getTranscriptsByCase(req.params.caseId);
      res.json(transcripts);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch transcripts" });
    }
  });

  app.post("/api/cases/:caseId/transcripts", async (req, res) => {
    try {
      const validatedData = insertTranscriptSchema.parse({
        ...req.body,
        caseId: req.params.caseId,
      });
      const transcript = await storage.createTranscript(validatedData);
      res.status(201).json(transcript);
    } catch (error) {
      res.status(400).json({ error: "Invalid transcript data" });
    }
  });

  // Analysis endpoints
  app.get("/api/cases/:caseId/analysis", async (req, res) => {
    try {
      const analysis = await storage.getAnalysisByCase(req.params.caseId);
      if (!analysis) {
        return res.status(404).json({ error: "Analysis not found" });
      }
      res.json(analysis);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch analysis" });
    }
  });

  app.post("/api/cases/:caseId/analysis", async (req, res) => {
    try {
      const validatedData = insertAnalysisSchema.parse({
        ...req.body,
        caseId: req.params.caseId,
      });
      const analysis = await storage.createAnalysis(validatedData);
      res.status(201).json(analysis);
    } catch (error) {
      res.status(400).json({ error: "Invalid analysis data" });
    }
  });

  // Actions endpoints
  app.get("/api/cases/:caseId/actions", async (req, res) => {
    try {
      const actions = await storage.getActionsByCase(req.params.caseId);
      res.json(actions);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch actions" });
    }
  });

  app.post("/api/cases/:caseId/actions", async (req, res) => {
    try {
      const validatedData = insertActionSchema.parse({
        ...req.body,
        caseId: req.params.caseId,
      });
      const action = await storage.createAction(validatedData);
      res.status(201).json(action);
    } catch (error) {
      res.status(400).json({ error: "Invalid action data" });
    }
  });

  app.patch("/api/actions/:id", async (req, res) => {
    try {
      const action = await storage.updateAction(req.params.id, req.body);
      if (!action) {
        return res.status(404).json({ error: "Action not found" });
      }
      res.json(action);
    } catch (error) {
      res.status(500).json({ error: "Failed to update action" });
    }
  });

  // Proxy generate requests to the FastAPI backend
  app.post("/generate", async (req, res) => {
    try {
      const backendUrl = "http://localhost:8000/generate";
      
      // Map frontend parameters to backend expected format
      const backendPayload = {
        scenario: req.body.scenario,
        customer_id: req.body.customer_id,
        urgency: req.body.urgency,
        customer_sentiment: req.body.sentiment, // Map sentiment to customer_sentiment
        financial_impact: req.body.financial_impact || false,
        store: true // Always store transcripts
      };

      console.log("Proxying generate request:", backendPayload);

      const response = await fetch(backendUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(backendPayload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Backend error: ${response.status} - ${errorText}`);
        throw new Error(`Backend API error: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      console.log("Generate result:", result);
      res.json(result);
    } catch (error) {
      console.error("Generate proxy error:", error);
      res.status(500).json({ 
        error: "Failed to generate transcript", 
        details: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  // Proxy transcripts requests to FastAPI backend for Case Details
  app.get("/api/transcripts", async (req, res) => {
    try {
      const response = await fetch("http://localhost:8000/transcripts");
      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }
      const transcripts = await response.json();
      res.json(transcripts);
    } catch (error) {
      console.error("Transcripts proxy error:", error);
      res.status(500).json({ error: "Failed to fetch transcripts" });
    }
  });

  // Proxy individual transcript requests to FastAPI backend
  app.get("/api/transcript/:id", async (req, res) => {
    try {
      const response = await fetch(`http://localhost:8000/transcript/${req.params.id}`);
      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }
      const transcript = await response.json();
      res.json(transcript);
    } catch (error) {
      console.error("Transcript detail proxy error:", error);
      res.status(500).json({ error: "Failed to fetch transcript" });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
