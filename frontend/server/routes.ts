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

  // Map case IDs to transcript IDs and proxy Case Details data
  app.get("/api/cases/:caseId/transcripts", async (req, res) => {
    try {
      // Map case ID to transcript ID - if it looks like a transcript ID, use it directly
      let transcriptId = req.params.caseId;
      
      // If it's a short case ID, try to map it to an actual transcript ID
      if (!transcriptId.startsWith('CALL_')) {
        // Get list of transcripts and map by index or find a suitable transcript
        const transcriptsResponse = await fetch("http://localhost:8000/transcripts");
        if (transcriptsResponse.ok) {
          const transcripts = await transcriptsResponse.json();
          // Use case ID as index to get a transcript
          const index = parseInt(transcriptId) - 1;
          if (index >= 0 && index < transcripts.length) {
            transcriptId = transcripts[index].transcript_id;
          } else if (transcripts.length > 0) {
            // Default to first transcript if index is out of bounds
            transcriptId = transcripts[0].transcript_id;
          }
        }
      }
      const response = await fetch(`http://localhost:8000/transcript/${transcriptId}`);
      
      if (!response.ok) {
        console.error(`Transcript not found: ${transcriptId}`);
        res.json([]); // Return empty array if not found
        return;
      }
      
      const transcript = await response.json();
      console.log("Raw transcript data:", JSON.stringify(transcript, null, 2));
      
      // Transform transcript data to match frontend format
      const messages = transcript.messages || [];
      console.log("Messages array:", messages.length, "messages");
      
      const transformedMessages = messages.map((msg: any, index: number) => {
        console.log("Transforming message:", index, msg);
        return {
          id: index,
          speaker: msg.role?.includes("agent") || msg.role?.toLowerCase().includes("advisor") || msg.role?.toLowerCase().includes("representative") ? "Agent" : "Customer", 
          content: msg.content,
          timestamp: msg.timestamp || new Date().toISOString()
        };
      });
      
      console.log("Transformed messages:", transformedMessages.length);
      res.json(transformedMessages);
    } catch (error) {
      console.error("Case transcripts proxy error:", error);
      res.json([]); // Return empty array on error
    }
  });

  // Map case analysis data
  app.get("/api/cases/:caseId/analysis", async (req, res) => {
    try {
      // Apply same mapping logic as transcripts
      let transcriptId = req.params.caseId;
      
      if (!transcriptId.startsWith('CALL_')) {
        const transcriptsResponse = await fetch("http://localhost:8000/transcripts");
        if (transcriptsResponse.ok) {
          const transcripts = await transcriptsResponse.json();
          const index = parseInt(transcriptId) - 1;
          if (index >= 0 && index < transcripts.length) {
            transcriptId = transcripts[index].transcript_id;
          } else if (transcripts.length > 0) {
            transcriptId = transcripts[0].transcript_id;
          }
        }
      }
      const response = await fetch(`http://localhost:8000/transcript/${transcriptId}`);
      
      if (!response.ok) {
        res.status(404).json({ error: "Analysis not found" });
        return;
      }
      
      const transcript = await response.json();
      const analysis = transcript.analysis;
      
      if (!analysis) {
        res.status(404).json({ error: "Analysis not found" });
        return;
      }
      
      // Transform analysis data to match frontend format
      const transformedAnalysis = {
        intent: analysis.intent || "Service Request",
        confidence: analysis.confidence || 0.85,
        sentiment: analysis.customer_sentiment || "neutral",
        risks: [
          { label: "Compliance", value: analysis.compliance_risk || 0.1 },
          { label: "Escalation", value: analysis.escalation_risk || 0.3 },
          { label: "Churn", value: analysis.churn_risk || 0.2 }
        ]
      };
      
      res.json(transformedAnalysis);
    } catch (error) {
      console.error("Case analysis proxy error:", error);
      res.status(404).json({ error: "Analysis not found" });
    }
  });

  // Map case actions data
  app.get("/api/cases/:caseId/actions", async (req, res) => {
    try {
      // Apply same mapping logic as transcripts
      let transcriptId = req.params.caseId;
      
      if (!transcriptId.startsWith('CALL_')) {
        const transcriptsResponse = await fetch("http://localhost:8000/transcripts");
        if (transcriptsResponse.ok) {
          const transcripts = await transcriptsResponse.json();
          const index = parseInt(transcriptId) - 1;
          if (index >= 0 && index < transcripts.length) {
            transcriptId = transcripts[index].transcript_id;
          } else if (transcripts.length > 0) {
            transcriptId = transcripts[0].transcript_id;
          }
        }
      }
      const response = await fetch(`http://localhost:8000/transcript/${transcriptId}`);
      
      if (!response.ok) {
        res.json([]); // Return empty array if not found
        return;
      }
      
      const transcript = await response.json();
      const actionPlan = transcript.action_plan;
      
      if (!actionPlan || !actionPlan.actions) {
        res.json([]); // Return empty array if no actions
        return;
      }
      
      // Transform action plan data to match frontend format
      const transformedActions = actionPlan.actions.map((action: any, index: number) => ({
        id: index,
        action: action.action || action.description || "Pending Review",
        category: action.category || "Review",
        risk: action.risk_level || "Medium",
        impact: action.impact || "Low",
        submittedAt: transcript.created_at || new Date().toISOString(),
        decision: "Pending"
      }));
      
      res.json(transformedActions);
    } catch (error) {
      console.error("Case actions proxy error:", error);
      res.json([]); // Return empty array on error
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
