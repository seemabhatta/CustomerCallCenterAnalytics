# 🏗️ Clean Separation Architecture

## Overview

This document outlines a **clean separation architecture** that separates business logic, interface layers, and tests. This pattern promotes maintainability, testability, and reusability by ensuring that core business logic remains independent of user interfaces.

## Core Philosophy

### **Agentic Approach**
- **Trust the AI/Logic** - Minimal hardcoded validation and constraints
- **Dynamic and Flexible** - Use `**kwargs` and flexible data structures
- **LLM/AI Responsibility** - Let AI models handle business decisions

### **Clean Separation**
- **Business Logic** - Pure Python classes with zero UI dependencies
- **Interface Layer** - CLI, API, Web UI consume business logic
- **Storage Layer** - Database operations separate from business rules
- **Test Layer** - Each layer tested independently

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│         BUSINESS LOGIC LAYER            │
│         (Pure Python - No UI)           │
├─────────────────────────────────────────┤
│ • Core business classes                 │
│ • Domain models                         │
│ • Business rules and processes          │
│ • No CLI, API, Web, or UI dependencies │
└──────────────┬──────────────────────────┘
               │
     ┌─────────┼─────────┬──────────┬─────────┐
     ▼         ▼         ▼          ▼         ▼
┌─────────┐ ┌──────┐ ┌──────┐ ┌─────────┐ ┌──────┐
│   CLI   │ │ REST │ │GraphQL│ │   Web   │ │Script│
│ (Typer) │ │(Fast │ │ API   │ │   UI    │ │Import│
│         │ │ API) │ │       │ │(React)  │ │      │
└─────────┘ └──────┘ └──────┘ └─────────┘ └──────┘
```

## Directory Structure

### **Recommended Layout**
```
project/
├── src/                           # Business Logic Layer
│   ├── core/                          # Core business classes
│   │   ├── service_class.py               # Main service
│   │   ├── processor.py                   # Business logic processor
│   │   └── __init__.py
│   ├── models/                        # Data models
│   │   ├── entities.py                    # Core entities
│   │   └── __init__.py
│   ├── storage/                       # Storage abstraction
│   │   ├── repository.py                  # Data access layer
│   │   └── __init__.py
│   └── utils/                         # Shared utilities
│       ├── helpers.py
│       └── __init__.py
├── interfaces/                    # Interface Layer
│   ├── cli.py                         # Command-line interface
│   ├── api.py                         # REST API interface
│   └── web.py                         # Web interface (optional)
├── tests/                         # Test Layer
│   ├── test_core.py                   # Business logic tests
│   ├── test_models.py                 # Model tests
│   ├── test_storage.py                # Storage tests
│   ├── test_cli.py                    # CLI interface tests
│   └── test_api.py                    # API interface tests
├── requirements.txt               # Dependencies
└── README.md                      # Documentation
```

## Design Principles

### **1. Business Logic Independence**
```python
# ✅ GOOD - Pure business logic
class DocumentProcessor:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def process(self, **parameters):
        # Pure business logic, no UI concerns
        return self._execute_processing(**parameters)

# ❌ BAD - UI concerns mixed with business logic  
class DocumentProcessor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.console = Console()  # CLI dependency!
    
    def process(self, **parameters):
        self.console.print("Processing...")  # UI in business logic!
        return self._execute_processing(**parameters)
```

### **2. Dynamic and Flexible Models**
```python
# ✅ GOOD - Flexible with dynamic attributes
class Document:
    def __init__(self, id: str = None, **kwargs):
        self.id = id or str(uuid.uuid4())
        # Store any additional attributes dynamically
        for key, value in kwargs.items():
            setattr(self, key, value)

# ❌ BAD - Rigid, hardcoded attributes
class Document:
    VALID_TYPES = ['pdf', 'word', 'text']
    
    def __init__(self, id: str, doc_type: str):
        if doc_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid type: {doc_type}")
        self.id = id
        self.doc_type = doc_type
```

### **3. Interface Layer as Thin Wrapper**
```python
# CLI Interface (cli.py)
@app.command()
def process(
    params: List[str] = typer.Argument(None),
    output_format: str = typer.Option("json")
):
    # Parse interface-specific input
    kwargs = parse_dynamic_params(params)
    
    # Use pure business logic
    processor = DocumentProcessor()
    result = processor.process(**kwargs)
    
    # Handle interface-specific output
    display_result(result, output_format)

# API Interface (api.py) - Same business logic!
@app.post("/process")
async def process_document(request: ProcessRequest):
    processor = DocumentProcessor()
    result = processor.process(**request.dict())
    return {"result": result}
```

### **4. Separated Testing Strategy**
```python
# Test business logic independently
class TestDocumentProcessor:
    def test_process_basic(self):
        processor = DocumentProcessor()
        result = processor.process(content="test")
        assert result.success == True

# Test CLI interface separately  
class TestCLI:
    @patch('cli.DocumentProcessor')
    def test_process_command(self, mock_processor):
        runner = CliRunner()
        result = runner.invoke(app, ["process", "content=test"])
        assert result.exit_code == 0
        mock_processor.return_value.process.assert_called_once()
```

## Implementation Guidelines

### **Step 1: Start with Pure Business Logic**
1. Create core business classes in `src/core/`
2. Ensure zero dependencies on UI frameworks
3. Use dependency injection for external services
4. Implement flexible data models with `**kwargs`

### **Step 2: Create Interface Layers**
1. CLI using Typer or Click
2. API using FastAPI or Flask
3. Each interface imports and uses business logic
4. Handle interface-specific concerns (parsing, formatting, validation)

### **Step 3: Implement Storage Abstraction**
1. Create repository/store classes in `src/storage/`
2. Use dependency injection for database connections
3. Keep storage logic separate from business logic

### **Step 4: Write Layered Tests**
1. Unit tests for business logic (no mocking of external UI)
2. Integration tests for storage layer
3. Interface tests for CLI/API (mock business logic)

## Interface Implementation Examples

### **CLI with Typer**
```python
#!/usr/bin/env python3
import typer
from rich.console import Console
from src.core.service import BusinessService

app = typer.Typer(help="Application CLI")
console = Console()

def init_system():
    """Initialize business logic components."""
    return BusinessService()

@app.command()
def process(
    params: List[str] = typer.Argument(None),
    store: bool = typer.Option(False, "--store"),
    show: bool = typer.Option(False, "--show")
):
    """Process with dynamic parameters."""
    service = init_system()
    kwargs = parse_dynamic_params(params or [])
    
    # Use pure business logic
    result = service.process(**kwargs)
    
    # Handle CLI-specific presentation
    if show:
        display_result(result)
    if store:
        service.store(result)

if __name__ == "__main__":
    app()
```

### **API with FastAPI**
```python
#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.core.service import BusinessService

app = FastAPI(title="Application API")

class ProcessRequest(BaseModel):
    """Request model with flexible parameters."""
    class Config:
        extra = "allow"  # Allow additional fields

def init_service():
    """Initialize business logic."""
    return BusinessService()

@app.post("/process")
async def process_data(request: ProcessRequest):
    """Process data via API."""
    try:
        service = init_service()
        # Same business logic as CLI!
        result = service.process(**request.dict())
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Testing Strategy

### **Layer-Specific Testing**
```python
# Business Logic Tests (no mocking of interfaces)
class TestBusinessService:
    def test_process_basic(self):
        service = BusinessService()
        result = service.process(input_data="test")
        assert result is not None

# Interface Tests (mock business logic)
class TestCLI:
    @patch('cli.BusinessService')
    def test_cli_process(self, mock_service):
        runner = CliRunner()
        mock_service.return_value.process.return_value = "success"
        
        result = runner.invoke(app, ["process", "input=test"])
        
        assert result.exit_code == 0
        mock_service.return_value.process.assert_called_once()

# Integration Tests (test full flow)
class TestIntegration:
    def test_full_workflow(self):
        # Test complete workflow without mocking
        service = BusinessService()
        result = service.process(input_data="integration_test")
        stored = service.store(result)
        retrieved = service.retrieve(stored.id)
        assert retrieved.id == stored.id
```

## Benefits

### **1. Flexibility and Reusability**
- Same business logic powers CLI, API, web UI
- Easy to add new interfaces without changing core logic
- Business logic can be used in scripts, notebooks, other projects

### **2. Maintainability**
- Changes to CLI don't affect API
- Changes to business logic automatically apply to all interfaces
- Clear separation makes debugging easier

### **3. Testability**
- Test business logic without UI dependencies
- Test interfaces without complex business logic
- Each layer can be tested independently

### **4. Scalability**
- Deploy business logic as microservices
- Scale interfaces independently
- Add new features without touching existing interfaces

### **5. Team Collaboration**
- Frontend team works on interfaces
- Backend team works on business logic
- QA team tests each layer independently
- Clear boundaries reduce conflicts

## Anti-Patterns to Avoid

### **❌ Business Logic in Interface Layer**
```python
# BAD - Business logic in CLI
@app.command()
def process():
    # Complex business logic here
    if condition1 and condition2:
        result = complex_calculation()
        store_in_database(result)
```

### **❌ Interface Dependencies in Business Logic**
```python
# BAD - CLI dependencies in business class
class BusinessService:
    def __init__(self):
        self.console = Console()  # UI dependency!
    
    def process(self):
        self.console.print("Processing...")  # UI in business logic!
```

### **❌ Hardcoded Validation**
```python
# BAD - Rigid validation prevents flexibility
class DocumentProcessor:
    VALID_FORMATS = ['pdf', 'docx']
    
    def process(self, format: str):
        if format not in self.VALID_FORMATS:
            raise ValueError("Invalid format")
```

### **❌ Mixed Layer Testing**
```python
# BAD - Testing CLI behavior in business logic tests
class TestBusinessService:
    def test_process(self):
        runner = CliRunner()  # Testing CLI in business logic test!
        result = runner.invoke(app, ["process"])
```

## Migration Strategy

### **From Monolithic to Clean Separation:**

1. **Extract Business Logic**
   - Move core logic to `src/core/`
   - Remove UI dependencies
   - Make models flexible with `**kwargs`

2. **Create Interface Layer**
   - Move CLI code to separate file
   - Import and use business logic
   - Handle interface-specific concerns

3. **Separate Tests**
   - Move business logic tests to separate files
   - Create interface-specific tests
   - Mock appropriately for each layer

4. **Refactor Gradually**
   - Start with one interface (CLI or API)
   - Gradually extract more business logic
   - Add interfaces incrementally

## Conclusion

Clean separation architecture promotes:
- **Maintainable code** through clear boundaries
- **Flexible systems** that can grow and adapt
- **Testable components** that can be verified independently
- **Reusable business logic** across multiple interfaces
- **Agentic approach** that trusts AI/logic over hardcoded rules

This architecture pattern scales from small scripts to enterprise applications while maintaining simplicity and clarity.