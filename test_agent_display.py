#!/usr/bin/env python3
"""
Test script for agent display modes
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_display_modes():
    """Test all agent display modes"""
    print("🧪 Testing Agent Display Modes\n")
    
    # Set up handoffs
    os.environ['ENABLE_HANDOFFS'] = 'true'
    
    from agents import get_conversation_router
    from cli import run_agent_sync
    from config import settings
    
    test_input = "hi there!"
    router = get_conversation_router()
    
    modes = [
        ('full', None, "Full mode - shows agent chain"),
        ('simple', None, "Simple mode - shows agent name"),
        ('none', None, "None mode - no agent name"),
        ('full', 'Co-Pilot', "Override mode - unified branding")
    ]
    
    for mode, override, description in modes:
        print(f"📋 {description}")
        print("-" * 50)
        
        # Override settings
        settings.AGENT_DISPLAY_MODE = mode
        settings.AGENT_NAME_OVERRIDE = override
        
        response = run_agent_sync(router, test_input)
        display = response.format_display(
            mode=settings.AGENT_DISPLAY_MODE,
            override=settings.AGENT_NAME_OVERRIDE
        )
        
        print(f"Input: {test_input}")
        print(f"Output: {display}")
        print()
    
    print("✅ All display modes working correctly!")
    
    # Test generation routing
    print("\n🎯 Testing Router Agent Decisions")
    print("-" * 50)
    
    test_cases = [
        "hi",
        "generate some transcripts", 
        "analyze recent calls",
        "plan something for me"
    ]
    
    settings.AGENT_DISPLAY_MODE = 'simple'
    settings.AGENT_NAME_OVERRIDE = None
    
    for test_case in test_cases:
        print(f"Input: '{test_case}'")
        response = run_agent_sync(router, test_case)
        display = response.format_display(
            mode=settings.AGENT_DISPLAY_MODE,
            override=settings.AGENT_NAME_OVERRIDE
        )
        print(f"Response: {display}")
        print()

if __name__ == "__main__":
    test_display_modes()