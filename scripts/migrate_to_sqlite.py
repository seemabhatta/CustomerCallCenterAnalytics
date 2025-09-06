#!/usr/bin/env python3
"""
Migration script to convert JSON files to SQLite database.
Preserves all existing data including IDs, timestamps, and metadata.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storage_sqlite import SQLiteStorage
from config import settings


def migrate_json_to_sqlite(json_dir: Path, db_path: str = None, dry_run: bool = False):
    """
    Migrate all JSON files from data directory to SQLite database.
    
    Args:
        json_dir: Path to directory containing JSON files
        db_path: Path for SQLite database (optional)
        dry_run: If True, show what would be migrated without actually doing it
    """
    
    print(f"🔄 Starting migration from {json_dir} to SQLite")
    print("=" * 60)
    
    # Initialize SQLite storage
    if not dry_run:
        storage = SQLiteStorage(db_path)
        print(f"✅ Initialized SQLite database at: {storage.db_path}")
    
    # Find all JSON files
    json_files = list(json_dir.glob("*.json"))
    print(f"📁 Found {len(json_files)} JSON files to migrate")
    
    if not json_files:
        print("❌ No JSON files found. Nothing to migrate.")
        return
    
    # Statistics
    stats = {
        "transcripts": 0,
        "analyses": 0,
        "errors": 0,
        "skipped": 0
    }
    
    # Process each file
    for json_file in sorted(json_files):
        print(f"\n📄 Processing: {json_file.name}")
        
        try:
            # Load JSON data
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate required fields
            if not all(key in data for key in ['id', 'content', 'created_at']):
                print(f"  ⚠️  Skipping {json_file.name}: Missing required fields")
                stats["skipped"] += 1
                continue
            
            # Determine if this is an analysis or transcript
            is_analysis = (
                data.get('metadata', {}).get('type') == 'analysis' or
                'ANALYSIS_START' in data.get('content', '') or
                data['id'].startswith('ANALYSIS_')
            )
            
            if dry_run:
                file_type = "analysis" if is_analysis else "transcript"
                print(f"  📋 Would migrate: {data['id']} ({file_type})")
                if is_analysis:
                    print(f"      → Links to transcript: {data.get('metadata', {}).get('transcript_id', 'unknown')}")
                stats["analyses" if is_analysis else "transcripts"] += 1
                continue
            
            # Migrate the data
            if is_analysis:
                # This is an analysis - need to link it properly
                transcript_id = data.get('metadata', {}).get('transcript_id')
                if not transcript_id:
                    # Try to extract from ID pattern ANALYSIS_CALLID_TIME
                    parts = data['id'].split('_')
                    if len(parts) >= 3:
                        transcript_id = f"CALL_{parts[1]}_{parts[2]}"
                
                if transcript_id:
                    # Use the existing save_analysis method
                    # But we need to preserve the original ID and timestamp
                    stored_id = storage._save_analysis_with_id(
                        data['id'],
                        transcript_id, 
                        data['content'],
                        data.get('metadata', {}),
                        data['created_at']
                    )
                    print(f"  ✅ Migrated analysis: {stored_id}")
                    stats["analyses"] += 1
                else:
                    print(f"  ⚠️  Skipping analysis {data['id']}: No transcript_id found")
                    stats["skipped"] += 1
            else:
                # This is a transcript
                stored_id = storage._save_transcript_with_id(
                    data['id'],
                    data['content'],
                    data.get('metadata', {}),
                    data['created_at']
                )
                print(f"  ✅ Migrated transcript: {stored_id}")
                stats["transcripts"] += 1
                
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON decode error in {json_file.name}: {e}")
            stats["errors"] += 1
        except Exception as e:
            print(f"  ❌ Error processing {json_file.name}: {e}")
            stats["errors"] += 1
    
    # Print summary
    print(f"\n📊 Migration Summary")
    print("=" * 30)
    print(f"Transcripts: {stats['transcripts']}")
    print(f"Analyses: {stats['analyses']}")
    print(f"Errors: {stats['errors']}")  
    print(f"Skipped: {stats['skipped']}")
    print(f"Total processed: {sum(stats.values())}")
    
    if not dry_run and stats["transcripts"] + stats["analyses"] > 0:
        print(f"\n✅ Migration completed successfully!")
        
        # Show final database stats
        db_stats = storage.get_stats()
        print(f"📊 Database now contains:")
        print(f"  • {db_stats.get('transcripts', 0)} transcripts")
        print(f"  • {db_stats.get('analyses', 0)} analyses")
        print(f"  • Database size: {db_stats.get('total_size_mb', 0)} MB")
        print(f"  • Location: {db_stats.get('storage_path')}")


def add_migration_methods_to_storage():
    """Add temporary migration methods to SQLiteStorage for preserving IDs."""
    
    def _save_transcript_with_id(self, transcript_id: str, content: str, 
                                metadata: dict, created_at: str) -> str:
        """Save transcript with specific ID and timestamp (migration only)."""
        metadata_json = json.dumps(metadata or {})
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO transcripts (id, content, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (transcript_id, content, metadata_json, created_at, created_at))
            
            # Update FTS if available
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO transcripts_fts (id, content, source) 
                    VALUES (?, ?, ?)
                """, (transcript_id, content, metadata.get('type', 'transcript')))
            except:
                pass
        
        return transcript_id
    
    def _save_analysis_with_id(self, analysis_id: str, transcript_id: str, 
                              analysis_content: str, metadata: dict, created_at: str) -> str:
        """Save analysis with specific ID and timestamp (migration only)."""
        
        # Parse analysis for structured data
        confidence_score, risk_level, resolution_status = self._parse_analysis(analysis_content)
        
        metadata_json = json.dumps(metadata or {})
        
        with self._get_connection() as conn:
            # Insert analysis as transcript (backward compatibility)
            conn.execute("""
                INSERT OR REPLACE INTO transcripts (id, content, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (analysis_id, analysis_content, metadata_json, created_at, created_at))
            
            # Insert into analyses table
            conn.execute("""
                INSERT OR REPLACE INTO analyses (id, transcript_id, content, confidence_score, 
                                               risk_level, resolution_status, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (analysis_id, transcript_id, analysis_content, confidence_score, 
                  risk_level, resolution_status, metadata_json, created_at))
            
            # Update FTS if available
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO transcripts_fts (id, content, source) 
                    VALUES (?, ?, ?)
                """, (analysis_id, analysis_content, 'analysis'))
            except:
                pass
        
        return analysis_id
    
    # Add methods to SQLiteStorage class
    SQLiteStorage._save_transcript_with_id = _save_transcript_with_id
    SQLiteStorage._save_analysis_with_id = _save_analysis_with_id


def main():
    """Main migration script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate JSON files to SQLite database')
    parser.add_argument('--json-dir', type=str, default='./data', 
                       help='Directory containing JSON files (default: ./data)')
    parser.add_argument('--db-path', type=str, 
                       help='SQLite database path (default: from settings)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be migrated without actually doing it')
    parser.add_argument('--backup', action='store_true', default=True,
                       help='Create backup of JSON directory before migration')
    
    args = parser.parse_args()
    
    json_dir = Path(args.json_dir)
    
    if not json_dir.exists():
        print(f"❌ JSON directory not found: {json_dir}")
        return 1
    
    if args.backup and not args.dry_run:
        # Create backup
        backup_dir = json_dir.parent / f"data_backup_{datetime.now():%Y%m%d_%H%M%S}"
        print(f"📦 Creating backup at: {backup_dir}")
        import shutil
        shutil.copytree(json_dir, backup_dir)
        print(f"✅ Backup created")
    
    # Add migration methods
    add_migration_methods_to_storage()
    
    # Run migration
    try:
        migrate_json_to_sqlite(json_dir, args.db_path, args.dry_run)
        return 0
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())