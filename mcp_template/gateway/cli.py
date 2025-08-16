"""
CLI command for running the MCP Gateway
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

try:
    import typer
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False

if TYPER_AVAILABLE:
    gateway_app = typer.Typer(
        name="gateway",
        help="MCP Gateway server commands"
    )
else:
    # Create a dummy gateway_app for when typer is not available
    class DummyApp:
        def command(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    
    gateway_app = DummyApp()


def check_dependencies():
    """Check if required dependencies are available."""
    missing = []
    
    if not TYPER_AVAILABLE:
        missing.append("typer")
    
    try:
        import fastapi
        import uvicorn
    except ImportError:
        missing.append("fastapi")
        missing.append("uvicorn")
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    return True


if TYPER_AVAILABLE:


    @gateway_app.command("start")
    def start_gateway(
        registry: Optional[str] = typer.Option(
            None,
            "--registry", "-r",
            help="Path to server registry configuration file"
        ),
        host: str = typer.Option(
            "0.0.0.0",
            "--host",
            help="Host to bind to"
        ),
        port: int = typer.Option(
            8000,
            "--port", "-p",
            help="Port to bind to"
        ),
        log_level: str = typer.Option(
            "INFO",
            "--log-level",
            help="Log level (DEBUG, INFO, WARNING, ERROR)"
        )
    ):
        """Start the MCP Gateway server."""
        
        if not check_dependencies():
            raise typer.Exit(1)
        
        from mcp_template.gateway.server import MCPGateway
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        async def run():
            gateway = MCPGateway(registry_path=registry)
            
            try:
                await gateway.start(host=host, port=port)
            except KeyboardInterrupt:
                typer.echo("Received interrupt signal")
            finally:
                await gateway.shutdown()
        
        typer.echo(f"Starting MCP Gateway on {host}:{port}")
        if registry:
            typer.echo(f"Using registry: {registry}")
        
        asyncio.run(run())


    @gateway_app.command("validate")
    def validate_registry(
        registry: str = typer.Argument(..., help="Path to registry file to validate")
    ):
        """Validate a server registry configuration file."""
        
        from mcp_template.gateway.registry import ServerRegistry
        
        registry_path = Path(registry)
        if not registry_path.exists():
            typer.echo(f"Error: Registry file not found: {registry}", err=True)
            raise typer.Exit(1)
        
        try:
            server_registry = ServerRegistry(registry_path)
            servers = server_registry.list_servers()
            
            typer.echo(f"✓ Registry loaded successfully from: {registry}")
            typer.echo(f"✓ Found {len(servers)} servers: {', '.join(servers)}")
            
            # Validate each server configuration
            errors = []
            for server_id in servers:
                config = server_registry.get_server_config(server_id)
                server_errors = server_registry.validate_server_config(config)
                if server_errors:
                    errors.extend([f"Server '{server_id}': {err}" for err in server_errors])
            
            if errors:
                typer.echo("\n✗ Validation errors found:")
                for error in errors:
                    typer.echo(f"  - {error}")
                raise typer.Exit(1)
            else:
                typer.echo("✓ All server configurations are valid")
        
        except Exception as e:
            typer.echo(f"Error validating registry: {e}", err=True)
            raise typer.Exit(1)


    @gateway_app.command("example")
    def create_example_registry(
        output: str = typer.Option(
            "gateway-registry.json",
            "--output", "-o", 
            help="Output file path"
        )
    ):
        """Create an example registry configuration file."""
        
        from mcp_template.gateway.registry import ServerRegistry
        
        # Create a registry with example configuration
        registry = ServerRegistry()
        
        # Add some example servers
        registry.add_server("demo", {
            "type": "template",
            "template_name": "demo", 
            "instances": 1,
            "config": {"hello_from": "Gateway"}
        })
        
        registry.add_server("example-http", {
            "type": "http",
            "instances": [
                {"endpoint": "http://localhost:8080"},
                {"endpoint": "http://localhost:8081"}
            ],
            "load_balancing": "round_robin"
        })
        
        registry.add_server("example-stdio", {
            "type": "stdio",
            "command": ["python", "-m", "my_mcp_server"],
            "pool_size": 3,
            "working_dir": "/app",
            "env_vars": {"LOG_LEVEL": "info"}
        })
        
        # Update gateway config
        registry.update_gateway_config({
            "host": "0.0.0.0",
            "port": 8000,
            "reload_registry": True,
            "health_check_interval": 30
        })
        
        # Save to file
        registry.save(output)
        typer.echo(f"✓ Created example registry configuration: {output}")
        typer.echo("Edit this file to configure your MCP servers, then start the gateway with:")
        typer.echo(f"  mcpt gateway start --registry {output}")


if __name__ == "__main__":
    if TYPER_AVAILABLE:
        gateway_app()
    else:
        print("typer is required to run the gateway CLI")
        print("Install with: pip install typer")