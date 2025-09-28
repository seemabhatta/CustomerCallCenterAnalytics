#!/usr/bin/env python3
"""
Initialize KuzuDB schema for the knowledge graph.
Creates all required node and relationship tables.
"""

import kuzu
import os
import sys

def initialize_kuzu_schema():
    """Initialize the complete KuzuDB schema for the knowledge graph."""

    db_path = 'data/knowledge_graph_v2.db'
    print(f"Initializing KuzuDB schema at: {db_path}")

    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    try:
        # Connect to database
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)

        print("\n=== Creating Node Tables ===")

        # Core business entity nodes
        node_schemas = [
            # Primary business entities
            ("Customer", """
                customer_id STRING,
                name STRING,
                email STRING,
                phone STRING,
                risk_score DOUBLE,
                compliance_flags STRING,
                total_interactions INT64,
                last_updated TIMESTAMP,
                last_contact_date TIMESTAMP,
                satisfaction_score DOUBLE,
                created_at TIMESTAMP,
                PRIMARY KEY (customer_id)
            """),

            ("Transcript", """
                transcript_id STRING,
                customer_id STRING,
                content STRING,
                duration_seconds INT64,
                channel STRING,
                created_at TIMESTAMP,
                PRIMARY KEY (transcript_id)
            """),

            ("Analysis", """
                analysis_id STRING,
                call_id STRING,
                transcript_id STRING,
                intent STRING,
                urgency_level STRING,
                sentiment STRING,
                confidence_score DOUBLE,
                risk_factors STRING,
                compliance_issues STRING,
                customer_satisfaction STRING,
                analysis_summary STRING,
                llm_reasoning STRING,
                analyzed_at TIMESTAMP,
                analyzer_version STRING,
                processing_time_ms INT64,
                created_at TIMESTAMP,
                PRIMARY KEY (analysis_id)
            """),

            ("Plan", """
                plan_id STRING,
                analysis_id STRING,
                actions STRING[],
                priority STRING,
                estimated_duration INT64,
                source_stage STRING,
                created_at TIMESTAMP,
                PRIMARY KEY (plan_id)
            """),

            ("Workflow", """
                workflow_id STRING,
                plan_id STRING,
                steps STRING[],
                current_step INT64,
                status STRING,
                created_at TIMESTAMP,
                PRIMARY KEY (workflow_id)
            """),

            ("Execution", """
                execution_id STRING,
                workflow_id STRING,
                step_results STRING[],
                status STRING,
                completed_at TIMESTAMP,
                created_at TIMESTAMP,
                PRIMARY KEY (execution_id)
            """),

            # Knowledge graph learning nodes
            ("Hypothesis", """
                hypothesis_id STRING,
                hypothesis_text STRING,
                title STRING,
                description STRING,
                confidence DOUBLE,
                source_entity_type STRING,
                source_entity_id STRING,
                pattern_type STRING,
                created_at TIMESTAMP,
                status STRING,
                PRIMARY KEY (hypothesis_id)
            """),

            ("CandidatePattern", """
                pattern_id STRING,
                pattern_type STRING,
                pattern_data STRING,
                support_count INT64,
                confidence_score DOUBLE,
                source_hypotheses STRING[],
                created_at TIMESTAMP,
                PRIMARY KEY (pattern_id)
            """),

            ("ValidatedPattern", """
                pattern_id STRING,
                original_candidate_id STRING,
                validation_score DOUBLE,
                validation_method STRING,
                validation_data STRING,
                impact_score DOUBLE,
                created_at TIMESTAMP,
                PRIMARY KEY (pattern_id)
            """),

            ("Prediction", """
                prediction_id STRING,
                prediction_type STRING,
                target_entity STRING,
                target_entity_id STRING,
                predicted_event STRING,
                probability DOUBLE,
                confidence DOUBLE,
                scope STRING,
                source_stage STRING,
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                PRIMARY KEY (prediction_id)
            """),

            ("LearningNode", """
                learning_id STRING,
                learning_type STRING,
                content STRING,
                confidence DOUBLE,
                source_entities STRING[],
                created_at TIMESTAMP,
                PRIMARY KEY (learning_id)
            """),

            ("KnowledgeEntity", """
                entity_id STRING,
                entity_type STRING,
                entity_name STRING,
                properties STRING,
                confidence DOUBLE,
                source STRING,
                created_at TIMESTAMP,
                PRIMARY KEY (entity_id)
            """),

            ("MetaLearning", """
                meta_id STRING,
                meta_learning_id STRING,
                learning_type STRING,
                insights STRING,
                insight_source STRING,
                meta_insight STRING,
                improvement_area STRING,
                system_component STRING,
                impact_assessment STRING,
                confidence DOUBLE,
                source_entities STRING[],
                created_at TIMESTAMP,
                PRIMARY KEY (meta_id)
            """)
        ]

        # Create all node tables
        for table_name, schema in node_schemas:
            try:
                query = f"CREATE NODE TABLE {table_name}({schema})"
                print(f"Creating {table_name}...")
                conn.execute(query)
                print(f"✅ {table_name} created successfully")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"⚠️  {table_name} already exists, skipping")
                else:
                    print(f"❌ Error creating {table_name}: {e}")
                    raise

        print("\n=== Creating Relationship Tables ===")

        # Define relationships
        relationships = [
            # Core business flow relationships
            ("TRANSCRIPT_BELONGS_TO", "Transcript", "Customer", "MANY_ONE"),
            ("ANALYSIS_ANALYZES", "Analysis", "Transcript", "MANY_ONE"),
            ("PLAN_PLANS_FOR", "Plan", "Analysis", "MANY_ONE"),
            ("WORKFLOW_IMPLEMENTS", "Workflow", "Plan", "MANY_ONE"),
            ("EXECUTION_EXECUTES", "Execution", "Workflow", "MANY_ONE"),

            # Knowledge learning relationships
            ("HYPOTHESIS_DERIVED_FROM", "Hypothesis", "Analysis", "MANY_ONE"),
            ("HYPOTHESIS_DERIVED_FROM_PLAN", "Hypothesis", "Plan", "MANY_ONE"),
            ("HYPOTHESIS_DERIVED_FROM_EXECUTION", "Hypothesis", "Execution", "MANY_ONE"),

            ("PATTERN_FORMED_FROM", "CandidatePattern", "Hypothesis", "MANY_MANY"),
            ("PATTERN_VALIDATED", "ValidatedPattern", "CandidatePattern", "ONE_ONE"),

            ("PREDICTION_BASED_ON", "Prediction", "ValidatedPattern", "MANY_ONE"),
            ("TARGETS_CUSTOMER", "Prediction", "Customer", "MANY_ONE"),

            ("LEARNING_CONNECTS", "LearningNode", "KnowledgeEntity", "MANY_MANY"),
            ("KNOWLEDGE_EXTRACTED_FROM", "KnowledgeEntity", "Transcript", "MANY_ONE"),

            # Cross-connections for learning
            ("HYPOTHESIS_CONNECTS", "Hypothesis", "KnowledgeEntity", "MANY_MANY"),
            ("PATTERN_INVOLVES", "CandidatePattern", "KnowledgeEntity", "MANY_MANY"),
            ("TRIGGERED_HYPOTHESIS", "Customer", "Hypothesis", "MANY_MANY"),
        ]

        # Create relationship tables
        for rel_name, from_table, to_table, cardinality in relationships:
            try:
                # Add specific properties for certain relationships
                if rel_name == "TARGETS_CUSTOMER":
                    query = f"CREATE REL TABLE {rel_name}(FROM {from_table} TO {to_table}, prediction_scope STRING, target_date STRING, created_at TIMESTAMP DEFAULT current_timestamp())"
                elif rel_name == "TRIGGERED_HYPOTHESIS":
                    query = f"CREATE REL TABLE {rel_name}(FROM {from_table} TO {to_table}, trigger_strength DOUBLE, triggered_at STRING, created_at TIMESTAMP DEFAULT current_timestamp())"
                else:
                    query = f"CREATE REL TABLE {rel_name}(FROM {from_table} TO {to_table}, created_at TIMESTAMP DEFAULT current_timestamp())"
                print(f"Creating {rel_name}...")
                conn.execute(query)
                print(f"✅ {rel_name} created successfully")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"⚠️  {rel_name} already exists, skipping")
                else:
                    print(f"❌ Error creating {rel_name}: {e}")
                    raise

        print("\n=== Schema Initialization Complete ===")
        print("All tables and relationships have been created successfully!")

        # Verify schema by testing a simple query on each table
        print("\n=== Verifying Schema ===")
        for table_name, _ in node_schemas:
            try:
                result = conn.execute(f"MATCH (n:{table_name}) RETURN count(*)")
                count = result.get_next()[0] if result.has_next() else 0
                print(f"✅ {table_name}: {count} nodes")
            except Exception as e:
                print(f"❌ {table_name}: Verification failed - {e}")

        conn.close()
        print(f"\n🎉 KuzuDB schema initialized successfully at {db_path}")

    except Exception as e:
        print(f"❌ Failed to initialize schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    initialize_kuzu_schema()