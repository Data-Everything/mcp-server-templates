#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

try:
    print("1. Testing basic imports...")
    from rich.console import Console
    from rich.table import Table
    print("   Rich imports successful")
    
    print("2. Testing MCP imports...")
    from mcp_template.interactive_cli import ResponseBeautifier
    print("   ResponseBeautifier import successful")
    
    print("3. Creating instance...")
    beautifier = ResponseBeautifier()
    print("   Instance created successfully")
    
    print("4. Testing analyze method...")
    test_data = {"name": "test", "version": "1.0", "active": True}
    analysis = beautifier._analyze_data_types(test_data)
    print(f"   Analysis successful: {analysis.get('best_display', 'unknown')}")
    
    print("5. Testing beautify method...")
    beautifier.beautify_json(test_data, "Test Data")
    print("   Beautify method completed")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    import traceback
    print(f"❌ Error occurred: {e}")
    print("\nFull traceback:")
    print(traceback.format_exc())
