import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from .config import settings

class Storage:
    """Simple JSON-based storage for transcripts and analysis results."""
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or settings.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
        
    def save_transcript(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save transcript with auto-generated ID"""
        timestamp = datetime.now()
        transcript_id = f"CALL_{timestamp:%Y%m%d_%H%M%S}"
        
        data = {
            "id": transcript_id,
            "content": content,
            "metadata": metadata or {},
            "created_at": timestamp.isoformat()
        }
        
        path = self.data_dir / f"{transcript_id}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return transcript_id
    
    def load_transcript(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Load transcript by ID or partial ID"""
        
        # Handle exact match first
        exact_path = self.data_dir / f"{transcript_id}.json"
        if exact_path.exists():
            with open(exact_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Handle partial matches
        matches = list(self.data_dir.glob(f"*{transcript_id}*.json"))
        
        if not matches:
            return None
        if len(matches) > 1:
            return {
                "error": "Multiple matches found",
                "matches": [m.stem for m in matches],
                "suggestion": "Use a more specific ID or choose from the matches above"
            }
        
        with open(matches[0], 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent transcripts"""
        try:
            # Get all transcript files
            files = list(self.data_dir.glob("CALL_*.json"))
            
            # Sort by modification time (most recent first)
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            results = []
            for f in files[:limit]:
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                    
                    # Extract first line of content as summary
                    content = data.get('content', '')
                    if content:
                        # Find the first meaningful line (skip empty lines)
                        lines = [line.strip() for line in content.split('\n') if line.strip()]
                        first_line = lines[0] if lines else "Empty transcript"
                    else:
                        first_line = "Empty transcript"
                    
                    results.append({
                        "id": data.get('id', f.stem),
                        "summary": first_line[:80] + "..." if len(first_line) > 80 else first_line,
                        "created": data.get('created_at', 'Unknown'),
                        "has_metadata": bool(data.get('metadata')),
                        "type": data.get('metadata', {}).get('type', 'transcript')
                    })
                    
                except (json.JSONDecodeError, KeyError) as e:
                    # Skip corrupted files but don't fail completely
                    continue
            
            return results
            
        except Exception as e:
            return []
    
    def save_analysis(self, transcript_id: str, analysis_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save analysis results linked to a transcript"""
        timestamp = datetime.now()
        analysis_id = f"ANALYSIS_{transcript_id}_{timestamp:%H%M%S}"
        
        analysis_metadata = metadata or {}
        analysis_metadata.update({
            "type": "analysis",
            "transcript_id": transcript_id,
            "analysis_timestamp": timestamp.isoformat()
        })
        
        return self.save_transcript(analysis_content, analysis_metadata)
    
    def get_transcript_with_analysis(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get transcript along with any associated analysis"""
        transcript = self.load_transcript(transcript_id)
        if not transcript or 'error' in transcript:
            return transcript
        
        # Look for related analysis files
        analysis_files = list(self.data_dir.glob(f"ANALYSIS_{transcript_id}_*.json"))
        analyses = []
        
        for analysis_file in analysis_files:
            try:
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)
                    analyses.append(analysis_data)
            except (json.JSONDecodeError, IOError):
                continue
        
        # Sort analyses by creation time
        analyses.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        result = transcript.copy()
        result['analyses'] = analyses
        return result
    
    def search_transcripts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search transcripts by content"""
        query_lower = query.lower()
        results = []
        
        try:
            # Get all transcript files
            files = list(self.data_dir.glob("CALL_*.json"))
            
            for f in files:
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                    
                    content = data.get('content', '').lower()
                    if query_lower in content:
                        # Find context around the match
                        match_pos = content.find(query_lower)
                        start = max(0, match_pos - 50)
                        end = min(len(content), match_pos + len(query) + 50)
                        
                        context = content[start:end]
                        if start > 0:
                            context = "..." + context
                        if end < len(content):
                            context = context + "..."
                        
                        results.append({
                            "id": data.get('id', f.stem),
                            "match_context": context,
                            "created": data.get('created_at', 'Unknown')
                        })
                        
                        if len(results) >= limit:
                            break
                            
                except (json.JSONDecodeError, KeyError):
                    continue
                    
        except Exception:
            pass
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            all_files = list(self.data_dir.glob("*.json"))
            transcript_files = [f for f in all_files if f.stem.startswith('CALL_')]
            analysis_files = [f for f in all_files if f.stem.startswith('ANALYSIS_')]
            
            total_size = sum(f.stat().st_size for f in all_files)
            
            return {
                "total_files": len(all_files),
                "transcripts": len(transcript_files),
                "analyses": len(analysis_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_path": str(self.data_dir.absolute())
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "storage_path": str(self.data_dir.absolute())
            }

# Global storage instance
_storage = None

def get_storage():
    """Get the global storage instance (JSON or SQLite based on config)"""
    global _storage
    if _storage is None:
        if settings.USE_SQLITE:
            from .storage_sqlite import SQLiteStorage
            _storage = SQLiteStorage()
        else:
            _storage = Storage()
    return _storage