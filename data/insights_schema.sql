-- Leadership Insights Agent Database Schema
-- Tables for conversation sessions, caching, and learning patterns

-- Leadership conversation sessions
CREATE TABLE IF NOT EXISTS leadership_sessions (
    session_id TEXT PRIMARY KEY,
    executive_id TEXT NOT NULL,
    executive_role TEXT CHECK (executive_role IN ('VP', 'CCO', 'COO', 'Director', 'Manager')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    focus_area TEXT CHECK (focus_area IN ('compliance', 'performance', 'risk', 'strategic', 'operational')),
    context_data TEXT, -- JSON: conversation context
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'closed')),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation message history
CREATE TABLE IF NOT EXISTS session_messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,

    -- Agent decision tracking
    query_classification TEXT, -- JSON: intent, urgency, scope, etc.
    data_sources_used TEXT,   -- JSON: which stores were queried
    confidence_score REAL CHECK (confidence_score >= 0 AND confidence_score <= 100),
    token_count INTEGER DEFAULT 0,

    -- Performance metrics
    response_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES leadership_sessions(session_id)
);

-- Learned patterns for improving agent performance
CREATE TABLE IF NOT EXISTS insight_patterns (
    pattern_id TEXT PRIMARY KEY,
    pattern_type TEXT NOT NULL CHECK (pattern_type IN ('query_classification', 'data_strategy', 'aggregation_method', 'response_format')),
    query_pattern TEXT NOT NULL, -- Pattern or template
    successful_approach TEXT NOT NULL, -- JSON: what worked
    effectiveness_score REAL CHECK (effectiveness_score >= 0 AND effectiveness_score <= 100),
    usage_count INTEGER DEFAULT 0,

    -- Context
    executive_roles TEXT, -- JSON array: which roles this works for
    focus_areas TEXT,     -- JSON array: which areas this applies to

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance cache for expensive aggregations
CREATE TABLE IF NOT EXISTS aggregation_cache (
    cache_key TEXT PRIMARY KEY, -- Hash of query + filters + timeframe
    query_hash TEXT NOT NULL,   -- Hash of the original query
    aggregated_data TEXT NOT NULL, -- JSON: pre-computed insights

    -- Cache metadata
    data_sources TEXT,      -- JSON: which stores were used
    record_count INTEGER,   -- How many records were aggregated
    computation_time_ms INTEGER,

    -- TTL management
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    hit_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent reflection and quality tracking
CREATE TABLE IF NOT EXISTS agent_reflections (
    reflection_id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,

    -- Quality scores
    accuracy_score REAL CHECK (accuracy_score >= 0 AND accuracy_score <= 100),
    completeness_score REAL CHECK (completeness_score >= 0 AND completeness_score <= 100),
    clarity_score REAL CHECK (clarity_score >= 0 AND clarity_score <= 100),
    actionability_score REAL CHECK (actionability_score >= 0 AND actionability_score <= 100),
    overall_confidence REAL CHECK (overall_confidence >= 0 AND overall_confidence <= 100),

    -- Improvement suggestions
    strengths TEXT,           -- JSON array: what worked well
    weaknesses TEXT,          -- JSON array: what could improve
    missing_information TEXT, -- JSON array: what was missing
    suggested_improvements TEXT, -- JSON array: specific suggestions

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (message_id) REFERENCES session_messages(message_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_executive ON leadership_sessions(executive_id);
CREATE INDEX IF NOT EXISTS idx_sessions_focus ON leadership_sessions(focus_area);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON leadership_sessions(last_active);

CREATE INDEX IF NOT EXISTS idx_messages_session ON session_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON session_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_role ON session_messages(role);

CREATE INDEX IF NOT EXISTS idx_patterns_type ON insight_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_effectiveness ON insight_patterns(effectiveness_score);
CREATE INDEX IF NOT EXISTS idx_patterns_usage ON insight_patterns(usage_count);

CREATE INDEX IF NOT EXISTS idx_cache_expires ON aggregation_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_query ON aggregation_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_cache_created ON aggregation_cache(created_at);

CREATE INDEX IF NOT EXISTS idx_reflections_message ON agent_reflections(message_id);
CREATE INDEX IF NOT EXISTS idx_reflections_confidence ON agent_reflections(overall_confidence);

-- Triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_session_timestamp
    AFTER UPDATE ON leadership_sessions
BEGIN
    UPDATE leadership_sessions
    SET updated_at = CURRENT_TIMESTAMP
    WHERE session_id = NEW.session_id;
END;

CREATE TRIGGER IF NOT EXISTS update_pattern_timestamp
    AFTER UPDATE ON insight_patterns
BEGIN
    UPDATE insight_patterns
    SET updated_at = CURRENT_TIMESTAMP
    WHERE pattern_id = NEW.pattern_id;
END;

-- Trigger to update last_active on new messages
CREATE TRIGGER IF NOT EXISTS update_session_activity
    AFTER INSERT ON session_messages
BEGIN
    UPDATE leadership_sessions
    SET last_active = CURRENT_TIMESTAMP
    WHERE session_id = NEW.session_id;
END;

-- Trigger to increment cache hit count
CREATE TRIGGER IF NOT EXISTS update_cache_hit
    AFTER UPDATE ON aggregation_cache
    WHEN NEW.last_accessed > OLD.last_accessed
BEGIN
    UPDATE aggregation_cache
    SET hit_count = hit_count + 1
    WHERE cache_key = NEW.cache_key;
END;