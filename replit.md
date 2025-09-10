# Customer Call Center Analytics - Replit Setup

## Overview
This project is an AI-powered Customer Call Center Analytics system that generates and analyzes call center transcripts using OpenAI's API. It features intelligent risk assessment, compliance monitoring, and governance workflows for mortgage servicing scenarios.

## Current State
- ✅ Successfully imported and set up in Replit environment
- ✅ Python 3.11 and Node.js 20 installed 
- ✅ All Python and frontend dependencies installed
- ✅ OpenAI API key configured via Replit Secrets
- ✅ Database set up with existing data (28 transcripts)
- ✅ Backend API running on port 8000
- ✅ Frontend dashboard running on port 5000
- ✅ Deployment configured for autoscale with frontend build

## Project Architecture
- **Backend**: FastAPI server with OpenAI integration (port 8000)
- **Frontend**: React + TypeScript dashboard with Vite dev server (port 5000)
- **Database**: SQLite for development (data/call_center.db)
- **AI Engine**: OpenAI GPT models for transcript generation and analysis
- **Server**: Universal server architecture with CLI and API interfaces

## Key Features
- Generate realistic customer call transcripts
- AI-powered call analysis and risk assessment
- Governance and compliance workflows
- Action plan generation with approval routing
- Multi-layer insights (Borrower, Advisor, Supervisor, Leadership)

## API Endpoints
- `GET /` - Service status and info
- `GET /health` - Health check
- `GET /stats` - Database statistics
- `POST /generate` - Generate new transcripts
- `GET /docs` - Interactive API documentation

## Running the Application
The application is configured to run automatically via Replit workflows:
- **Backend API**: `python simple_server.py` (port 8000)
- **Frontend**: `cd frontend && npm run dev` (port 5000)
- **Original CLI**: `python cli_fast.py` available for advanced usage
- **API Documentation**: Available at `/docs` endpoint
- **Dashboard**: Available at main preview URL

## Environment Configuration
- Database: SQLite at `data/call_center.db`
- API Key: Configured via Replit Secrets (OPENAI_API_KEY)
- Host: 0.0.0.0 (Replit compatible)
- Port: 8000 (backend API)

## Recent Changes
- 2025-09-10: Successfully imported from GitHub and set up complete environment
- 2025-09-10: Installed Python 3.11 and Node.js 20 with all dependencies
- 2025-09-10: Configured OpenAI API key via Replit Secrets
- 2025-09-10: Set up dual workflows for backend API and frontend dashboard
- 2025-09-10: Configured deployment for autoscale with frontend build process

## User Preferences
- Prefers working backend API servers over complex CLI interfaces
- Values simple, functional endpoints for testing
- Needs reliable deployment configuration

## Deployment
- Target: Autoscale (stateless web API)
- Command: `python simple_server.py`
- Environment: Production-ready with secrets management