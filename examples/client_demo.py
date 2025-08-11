#!/usr/bin/env python3
"""
Example usage of the MCP Client for programmatic access.

This script demonstrates how to use the MCPClient for programmatic
access to MCP server template functionality.
"""

from mcp_template import MCPClient


def main():
    """Demonstrate MCP Client functionality."""
    print("🚀 MCP Client Example - Programmatic Access Demo")
    print("=" * 50)
    
    # Initialize the client
    print("\n1. Initializing MCP Client with mock backend...")
    client = MCPClient(backend_type="mock")  # Use mock to avoid Docker dependencies
    print("✅ Client initialized successfully")
    
    # List available templates
    print("\n2. Listing available templates...")
    templates = client.list_templates()
    print(f"✅ Found {len(templates)} templates:")
    for name, template in templates.items():
        print(f"   • {name}: {template.get('description', 'No description')}")
    
    # Get template configuration for a specific template
    print("\n3. Getting configuration for 'demo' template...")
    try:
        config = client.get_template_config("demo")
        print("✅ Demo template configuration schema:")
        if "properties" in config:
            for prop, details in config["properties"].items():
                print(f"   • {prop}: {details.get('description', 'No description')}")
        else:
            print("   • No configuration properties defined")
    except Exception as e:
        print(f"⚠️  Could not get config: {e}")
    
    # List templates in list format with status
    print("\n4. Getting template list with status information...")
    template_list = client.list_templates(as_dict=False)
    print("✅ Template status overview:")
    for template in template_list:
        status_emoji = "🟢" if template["status"] == "running" else "⚪"
        print(f"   {status_emoji} {template['name']}: {template['status']}")
    
    # List deployments
    print("\n5. Listing current deployments...")
    try:
        deployments = client.list_deployments()
        print(f"✅ Found {len(deployments)} active deployments")
        if deployments:
            for deployment in deployments:
                print(f"   • {deployment.get('name', 'Unknown')}: {deployment.get('status', 'Unknown status')}")
        else:
            print("   • No active deployments")
    except Exception as e:
        print(f"⚠️  Could not list deployments: {e}")
    
    # Test error handling
    print("\n6. Testing error handling...")
    try:
        client.get_template_config("nonexistent_template")
        print("❌ Should have raised an error")
    except ValueError as e:
        print(f"✅ Proper error handling: {e}")
    
    # Example deployment (commented out to avoid actual deployment)
    print("\n7. Example deployment code (not executed):")
    print("""
    # Deploy a template programmatically:
    deployment = client.deploy("demo", config={
        "greeting": "Hello from programmatic client!",
        "port": 8080
    })
    
    # Stop a deployment:
    client.stop("demo")
    
    # Discover tools from a running deployment:
    tools = client.discover_tools("demo")
    
    # Call a specific tool:
    result = client.call_tool("demo", "greet", {"name": "World"})
    """)
    
    print("\n🎉 MCP Client demonstration completed!")
    print("\nKey Benefits:")
    print("✅ Programmatic access to all MCP template functionality")
    print("✅ Clean, object-oriented API")
    print("✅ Error handling and validation")
    print("✅ No CLI dependency - pure Python interface")
    print("✅ Compatible with existing CLI tools")


if __name__ == "__main__":
    main()