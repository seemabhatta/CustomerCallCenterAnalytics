# Overview

This is a full-stack enterprise AI pipeline dashboard application built with React frontend, Express.js backend, and PostgreSQL database. The application provides a customer service case management system with AI-powered transcription, analysis, and risk assessment capabilities. It features a dashboard with metrics, an approval queue for managing cases, and detailed case views with transcripts and analysis data.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: React with TypeScript using Vite as the build tool
- **UI Components**: shadcn/ui component library built on Radix UI primitives
- **Styling**: Tailwind CSS with custom design tokens and CSS variables
- **State Management**: TanStack Query (React Query) for server state management
- **Routing**: Wouter for lightweight client-side routing
- **Form Handling**: React Hook Form with Zod validation resolvers

## Backend Architecture
- **Framework**: Express.js with TypeScript
- **API Design**: RESTful API with JSON responses
- **Database ORM**: Drizzle ORM for type-safe database operations
- **Validation**: Zod schemas for request/response validation
- **Development**: Hot module replacement via Vite integration
- **Error Handling**: Centralized error middleware with proper HTTP status codes

## Data Storage Solutions
- **Primary Database**: PostgreSQL with Neon serverless hosting
- **Schema Management**: Drizzle migrations with declarative schema definitions
- **Development Storage**: In-memory storage implementation for development/testing
- **Connection Pooling**: Built-in PostgreSQL connection management

## Database Schema Design
- **Cases**: Core entity storing customer service cases with priority, status, and risk assessment
- **Transcripts**: Conversation records linked to cases with speaker identification and timestamps
- **Analyses**: AI-generated insights including intent detection, confidence scores, and sentiment analysis
- **Actions**: Recommended or taken actions with categorization and risk assessment
- **Users**: Authentication and user management (prepared for future implementation)

## Authentication and Authorization
- **Current State**: Infrastructure prepared but not actively implemented
- **Session Management**: Connect-pg-simple for PostgreSQL-backed sessions (configured but unused)
- **Security**: CORS handling and request validation middleware in place

## External Dependencies
- **Database**: Neon PostgreSQL serverless database
- **UI Framework**: Radix UI for accessible component primitives
- **Styling**: Tailwind CSS for utility-first styling
- **Charts**: Recharts for data visualization components
- **Validation**: Zod for runtime type checking and validation
- **Development**: Replit-specific plugins for enhanced development experience

The application follows a modular monorepo structure with clear separation between client, server, and shared code. The architecture supports both development and production deployments with environment-specific configurations.