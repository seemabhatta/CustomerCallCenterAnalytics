#!/usr/bin/env python3
"""
Test script to verify OpenTelemetry configuration.
Run this after installing dependencies to test tracing.
"""
import os
import sys
import asyncio
from typing import Dict, Any

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_telemetry_imports():
    """Test that all telemetry imports work correctly."""
    try:
        from src.telemetry import (
            initialize_tracing,
            get_tracer,
            trace_async_function,
            trace_function,
            set_span_attributes,
            add_span_event
        )
        print("✅ All telemetry imports successful")
        return True
    except ImportError as e:
        print(f"❌ Telemetry import failed: {e}")
        return False

def test_tracer_initialization():
    """Test that tracer initializes correctly."""
    try:
        from src.telemetry import initialize_tracing
        
        # Test with console exporter only (should work without external deps)
        tracer = initialize_tracing(
            service_name="test-service",
            enable_console=True,
            enable_jaeger=False,
            enable_otlp=False
        )
        
        print("✅ Tracer initialization successful")
        return True
    except Exception as e:
        print(f"❌ Tracer initialization failed: {e}")
        return False

async def test_async_tracing():
    """Test async function tracing."""
    from src.telemetry import set_span_attributes, add_span_event
    
    set_span_attributes(
        test_param="test_value",
        operation_type="test"
    )
    add_span_event("test.operation_started")
    
    # Simulate some work
    await asyncio.sleep(0.1)
    
    add_span_event("test.operation_completed")
    return {"result": "success", "duration": 0.1}

def test_pipeline_integration():
    """Test that pipeline can import telemetry modules."""
    try:
        # Test imports that pipeline uses
        from src.telemetry import get_tracer, set_span_attributes, add_span_event, trace_async_function
        
        tracer = get_tracer()
        
        # Test creating a simple span
        with tracer.start_as_current_span("test.pipeline_operation") as span:
            set_span_attributes(
                test_id="test_123",
                operation="test_pipeline"
            )
            add_span_event("test.pipeline_started")
            span.set_attribute("status", "completed")
            add_span_event("test.pipeline_completed")
        
        print("✅ Pipeline telemetry integration successful")
        return True
    except Exception as e:
        print(f"❌ Pipeline telemetry integration failed: {e}")
        return False

def test_simple_formatter():
    """Test the simple span formatter function."""
    try:
        from src.telemetry import simple_span_formatter
        from src.telemetry import get_tracer, set_span_attributes, add_span_event
        
        print("✅ Simple formatter function imported successfully")
        
        # Test that formatter integration works
        tracer = get_tracer()
        
        print("Testing simple format output:")
        print("=" * 40)
        
        # Create a test span that will use the simple formatter
        with tracer.start_as_current_span("test.risk_assessment") as span:
            set_span_attributes(
                workflow_type="BORROWER",
                risk_level="HIGH",
                action_item_id="test_123"
            )
            add_span_event("test.llm_call_started")
            # Simulate some processing time
            import time
            time.sleep(0.1)
            add_span_event("test.llm_call_completed")
        
        print("=" * 40)
        print("✅ Simple formatter test completed")
        return True
    except Exception as e:
        print(f"❌ Simple formatter test failed: {e}")
        return False

async def run_tests():
    """Run all telemetry tests."""
    print("🔍 Testing OpenTelemetry Implementation\n")
    
    tests = [
        ("Telemetry Imports", test_telemetry_imports),
        ("Tracer Initialization", test_tracer_initialization),
        ("Pipeline Integration", test_pipeline_integration),
        ("Simple Formatter", test_simple_formatter),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
        print()
    
    # Test async tracing
    print("Running: Async Function Tracing")
    try:
        result = await test_async_tracing()
        print("✅ Async function tracing successful")
        results.append(("Async Function Tracing", True))
    except Exception as e:
        print(f"❌ Async function tracing failed: {e}")
        results.append(("Async Function Tracing", False))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        emoji = "✅" if success else "❌"
        print(f"{emoji} {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OpenTelemetry implementation is ready.")
    else:
        print("⚠️  Some tests failed. Check dependencies and configuration.")
    
    return passed == total

if __name__ == "__main__":
    # Set environment variables for testing
    os.environ["OTEL_CONSOLE_ENABLED"] = "true"
    os.environ["OTEL_JAEGER_ENABLED"] = "false"
    os.environ["OTEL_OTLP_ENABLED"] = "false"
    os.environ["OTEL_CONSOLE_FORMAT"] = "simple"
    
    asyncio.run(run_tests())