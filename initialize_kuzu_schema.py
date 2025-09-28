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
                total_interactions INT32,
                last_updated STRING,
                last_contact_date TIMESTAMP,
                satisfaction_score DOUBLE,
                created_at STRING,
                PRIMARY KEY (customer_id)
            """),

            ("Transcript", """
                transcript_id STRING,
                customer_id STRING,
                content STRING,
                duration_seconds INT32,
                channel STRING,
                created_at STRING,
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
                analyzed_at STRING,
                analyzer_version STRING,
                processing_time_ms INT32,
                created_at STRING,
                PRIMARY KEY (analysis_id)
            """),

            ("Plan", """
                plan_id STRING,
                analysis_id STRING,
                transcript_id STRING,
                customer_id STRING,
                actions STRING[],
                priority STRING,
                priority_level STRING,
                action_count INT32,
                urgency_level STRING,
                estimated_duration INT32,
                source_stage STRING,
                status STRING,
                created_at STRING,
                PRIMARY KEY (plan_id)
            """),

            ("Workflow", """
                workflow_id STRING,
                plan_id STRING,
                customer_id STRING,
                advisor_id STRING,
                steps STRING[],
                step_count INT32,
                current_step INT32,
                status STRING,
                estimated_duration INT32,
                priority STRING,
                created_at STRING,
                PRIMARY KEY (workflow_id)
            """),

            ("Execution", """
                execution_id STRING,
                workflow_id STRING,
                step_results STRING[],
                status STRING,
                completed_at STRING,
                created_at STRING,
                PRIMARY KEY (execution_id)
            """),

            ("Advisor", """
                advisor_id STRING,
                name STRING,
                department STRING,
                skill_level STRING,
                performance_score DOUBLE,
                total_calls_handled INT32,
                average_resolution_time INT32,
                customer_satisfaction_rating DOUBLE,
                coaching_sessions_completed INT32,
                last_performance_review STRING,
                hire_date STRING,
                status STRING,
                created_at STRING,
                PRIMARY KEY (advisor_id)
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
                evidence_count INT32,
                success_rate DOUBLE,
                last_observed STRING,
                source_pipeline STRING,
                occurrences INT32,
                created_at STRING,
                status STRING,
                PRIMARY KEY (hypothesis_id)
            """),

            ("CandidatePattern", """
                pattern_id STRING,
                pattern_type STRING,
                pattern_data STRING,
                support_count INT32,
                confidence_score DOUBLE,
                source_hypotheses STRING[],
                created_at STRING,
                PRIMARY KEY (pattern_id)
            """),

            ("ValidatedPattern", """
                pattern_id STRING,
                original_candidate_id STRING,
                validation_score DOUBLE,
                validation_method STRING,
                validation_data STRING,
                impact_score DOUBLE,
                created_at STRING,
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
                priority STRING,
                created_at STRING,
                expires_at STRING,
                PRIMARY KEY (prediction_id)
            """),

            ("LearningNode", """
                learning_id STRING,
                learning_type STRING,
                content STRING,
                confidence DOUBLE,
                source_entities STRING[],
                created_at STRING,
                PRIMARY KEY (learning_id)
            """),

            ("KnowledgeEntity", """
                entity_id STRING,
                entity_type STRING,
                entity_name STRING,
                properties STRING,
                confidence DOUBLE,
                source STRING,
                created_at STRING,
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
                validation_status STRING,
                validation_count INT32,
                confidence DOUBLE,
                source_entities STRING[],
                created_at STRING,
                PRIMARY KEY (meta_learning_id)
            """),

            ("Wisdom", """
                wisdom_id STRING,
                wisdom_type STRING,
                title STRING,
                content STRING,
                source_context STRING,
                learning_domain STRING,
                applicability STRING,
                validated BOOLEAN,
                validation_count INT32,
                effectiveness_score DOUBLE,
                created_at STRING,
                last_applied STRING,
                application_count INT32,
                PRIMARY KEY (wisdom_id)
            """),

            # Call table for business entity creation
            ("Call", """
                call_id STRING,
                transcript_id STRING,
                customer_id STRING,
                advisor_id STRING,
                duration_seconds INT32,
                start_time STRING,
                end_time STRING,
                status STRING,
                topic STRING,
                urgency_level STRING,
                sentiment STRING,
                resolved BOOLEAN,
                call_date STRING,
                created_at STRING,
                PRIMARY KEY (call_id)
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

            # Call node relationships - Connect Call to main graph
            ("CALL_BELONGS_TO_CUSTOMER", "Call", "Customer", "MANY_ONE"),
            ("CALL_HANDLED_BY", "Call", "Advisor", "MANY_ONE"),
            ("CALL_HAS_TRANSCRIPT", "Call", "Transcript", "ONE_ONE"),

            # Advisor node relationships - Connect Advisor to main graph
            ("ADVISOR_HANDLES_WORKFLOW", "Advisor", "Workflow", "ONE_MANY"),
            ("ADVISOR_LEARNS_FROM", "Advisor", "Wisdom", "MANY_MANY"),
            ("PATTERN_TEACHES_ADVISOR", "ValidatedPattern", "Advisor", "MANY_MANY"),

            # Wisdom node relationships - Connect Wisdom to main graph
            ("WISDOM_DERIVED_FROM_PLAN", "Wisdom", "Plan", "MANY_ONE"),
            ("WISDOM_GUIDES_EXECUTION", "Wisdom", "Execution", "MANY_MANY"),
            ("WISDOM_VALIDATES_PATTERN", "Wisdom", "ValidatedPattern", "MANY_MANY"),

            # MetaLearning node relationships - Connect MetaLearning to main graph
            ("METALEARNING_ANALYZES_HYPOTHESIS", "MetaLearning", "Hypothesis", "MANY_MANY"),
            ("METALEARNING_IMPROVES_PATTERN", "MetaLearning", "ValidatedPattern", "MANY_MANY"),
            ("METALEARNING_GENERATES_WISDOM", "MetaLearning", "Wisdom", "ONE_MANY"),
        ]

        # Create relationship tables
        for rel_name, from_table, to_table, cardinality in relationships:
            try:
                # Add specific properties for certain relationships
                if rel_name == "TARGETS_CUSTOMER":
                    query = f"CREATE REL TABLE {rel_name}(FROM {from_table} TO {to_table}, prediction_scope STRING, target_date STRING, created_at STRING DEFAULT current_timestamp())"
                elif rel_name == "TRIGGERED_HYPOTHESIS":
                    query = f"CREATE REL TABLE {rel_name}(FROM {from_table} TO {to_table}, trigger_strength DOUBLE, triggered_at STRING, created_at STRING DEFAULT current_timestamp())"
                else:
                    query = f"CREATE REL TABLE {rel_name}(FROM {from_table} TO {to_table}, created_at STRING DEFAULT current_timestamp())"
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