"""
MCP Gateway Server

FastAPI-based HTTP server that provides a unified endpoint for all MCP servers.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from fastapi import FastAPI, HTTPException, Request, Response
    from fastapi.responses import JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from .registry import ServerRegistry
from .load_balancer import LoadBalancer
from mcp_template.core.server_manager import ServerManager
from mcp_template.template.utils.discovery import TemplateDiscovery

logger = logging.getLogger(__name__)


class MCPGateway:
    """
    MCP Gateway server that routes requests to appropriate MCP servers.
    """
    
    def __init__(self, registry_path: Optional[Union[str, Path]] = None):
        """
        Initialize MCP Gateway.
        
        Args:
            registry_path: Path to server registry configuration
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI is required for the gateway server. Install with: pip install fastapi uvicorn")
        
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp not available - HTTP server proxying will be limited")
        
        self.registry = ServerRegistry(registry_path)
        self.load_balancer = LoadBalancer()
        self.server_manager = ServerManager()
        self.template_discovery = TemplateDiscovery()
        self.app = FastAPI(
            title="MCP Gateway",
            description="Unified endpoint for MCP servers with load balancing",
            version="1.0.0"
        )
        self._setup_routes()
        self._deployed_servers: Dict[str, Any] = {}
    
    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            """Gateway status and information."""
            return {
                "message": "MCP Gateway",
                "version": "1.0.0",
                "servers": self.registry.list_servers(),
                "status": "running"
            }
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}
        
        @self.app.get("/servers")
        async def list_servers():
            """List all available servers."""
            servers = {}
            for server_id in self.registry.list_servers():
                config = self.registry.get_server_config(server_id)
                servers[server_id] = {
                    "type": config.get("type"),
                    "status": "available"
                }
            return {"servers": servers}
        
        @self.app.get("/servers/{server_id}")
        async def get_server_info(server_id: str):
            """Get information about a specific server."""
            config = self.registry.get_server_config(server_id)
            if not config:
                raise HTTPException(status_code=404, detail=f"Server '{server_id}' not found")
            
            info = {
                "server_id": server_id,
                "config": config,
                "status": "available"
            }
            
            # Add load balancer stats if available
            if config.get("type") == "http" and server_id in self.load_balancer.http_balancers:
                info["load_balancer_stats"] = self.load_balancer.http_balancers[server_id].get_stats()
            elif config.get("type") in ["stdio", "template"] and server_id in self.load_balancer.stdio_pools:
                info["pool_stats"] = self.load_balancer.stdio_pools[server_id].get_stats()
            
            return info
        
        @self.app.post("/servers/{server_id}/tools/{tool_name}")
        async def call_tool(server_id: str, tool_name: str, request: Request):
            """Call a tool on a specific server."""
            return await self._route_request(server_id, "tool_call", tool_name, request)
        
        @self.app.get("/servers/{server_id}/tools")
        async def list_tools(server_id: str):
            """List tools available on a specific server."""
            return await self._route_request(server_id, "list_tools")
        
        @self.app.post("/{server_id}/{path:path}")
        @self.app.get("/{server_id}/{path:path}")
        @self.app.put("/{server_id}/{path:path}")
        @self.app.delete("/{server_id}/{path:path}")
        async def proxy_request(server_id: str, path: str, request: Request):
            """Proxy requests to the appropriate server."""
            return await self._route_request(server_id, "proxy", path, request)
        
        @self.app.post("/{server_id}")
        @self.app.get("/{server_id}")
        @self.app.put("/{server_id}")
        @self.app.delete("/{server_id}")
        async def proxy_root_request(server_id: str, request: Request):
            """Proxy root requests to the appropriate server."""
            return await self._route_request(server_id, "proxy", "", request)
    
    async def _route_request(self, server_id: str, action: str, *args, **kwargs) -> Any:
        """
        Route request to the appropriate server.
        
        Args:
            server_id: Target server identifier
            action: Action to perform (tool_call, list_tools, proxy)
            *args: Additional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Response from the target server
        """
        config = self.registry.get_server_config(server_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Server '{server_id}' not found")
        
        server_type = config.get("type")
        
        try:
            if server_type == "http":
                return await self._route_http_request(server_id, config, action, *args, **kwargs)
            elif server_type == "stdio":
                return await self._route_stdio_request(server_id, config, action, *args, **kwargs)
            elif server_type == "template":
                return await self._route_template_request(server_id, config, action, *args, **kwargs)
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Unsupported server type: {server_type}"
                )
        
        except Exception as e:
            logger.error("Error routing request to %s: %s", server_id, e)
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def _route_http_request(self, server_id: str, config: Dict[str, Any], 
                                action: str, *args, **kwargs) -> Any:
        """Route request to HTTP server."""
        instances = config.get("instances", [])
        if not instances:
            raise HTTPException(status_code=503, detail=f"No instances available for server '{server_id}'")
        
        strategy = config.get("load_balancing", "round_robin")
        balancer = self.load_balancer.get_http_balancer(server_id, instances, strategy)
        
        instance = balancer.get_next_instance()
        if not instance:
            raise HTTPException(status_code=503, detail=f"No healthy instances for server '{server_id}'")
        
        endpoint = instance["endpoint"]
        
        if action == "tool_call":
            tool_name = args[0]
            request = args[1]
            body = await request.body()
            
            # Make HTTP request to the server
            try:
                if not AIOHTTP_AVAILABLE:
                    raise HTTPException(status_code=503, detail="aiohttp not available for HTTP proxying")
                
                async with aiohttp.ClientSession() as session:
                    url = f"{endpoint}/tools/{tool_name}"
                    async with session.post(
                        url,
                        data=body,
                        headers=dict(request.headers)
                    ) as response:
                        content = await response.json()
                        return JSONResponse(content=content, status_code=response.status)
            except Exception as e:
                balancer.mark_unhealthy(endpoint)
                raise HTTPException(status_code=503, detail=f"Error calling tool: {str(e)}")
        
        elif action == "list_tools":
            try:
                if not AIOHTTP_AVAILABLE:
                    raise HTTPException(status_code=503, detail="aiohttp not available for HTTP proxying")
                
                async with aiohttp.ClientSession() as session:
                    url = f"{endpoint}/tools"
                    async with session.get(url) as response:
                        content = await response.json()
                        return JSONResponse(content=content, status_code=response.status)
            except Exception as e:
                balancer.mark_unhealthy(endpoint)
                raise HTTPException(status_code=503, detail=f"Error listing tools: {str(e)}")
        
        elif action == "proxy":
            path = args[0] if args else ""
            request = args[1] if len(args) > 1 else kwargs.get("request")
            
            try:
                if not AIOHTTP_AVAILABLE:
                    raise HTTPException(status_code=503, detail="aiohttp not available for HTTP proxying")
                
                async with aiohttp.ClientSession() as session:
                    url = f"{endpoint}/{path}" if path else endpoint
                    body = await request.body()
                    
                    async with session.request(
                        method=request.method,
                        url=url,
                        data=body,
                        headers=dict(request.headers),
                        params=dict(request.query_params)
                    ) as response:
                        content = await response.read()
                        return Response(
                            content=content,
                            status_code=response.status,
                            headers=dict(response.headers)
                        )
            except Exception as e:
                balancer.mark_unhealthy(endpoint)
                raise HTTPException(status_code=503, detail=f"Error proxying request: {str(e)}")
    
    async def _route_stdio_request(self, server_id: str, config: Dict[str, Any], 
                                 action: str, *args, **kwargs) -> Any:
        """Route request to stdio server."""
        pool = self.load_balancer.get_stdio_pool(server_id, config)
        connection = await pool.get_connection()
        
        if not connection:
            raise HTTPException(status_code=503, detail=f"No available connections for server '{server_id}'")
        
        try:
            if action == "tool_call":
                tool_name = args[0]
                request = args[1]
                body = await request.body()
                
                # Parse JSON body for tool arguments
                try:
                    arguments = json.loads(body) if body else {}
                except json.JSONDecodeError:
                    arguments = {}
                
                result = await connection.call_tool(tool_name, arguments)
                if result is None:
                    raise HTTPException(status_code=500, detail="Tool call failed")
                
                return JSONResponse(content=result)
            
            elif action == "list_tools":
                result = await connection.list_tools()
                if result is None:
                    raise HTTPException(status_code=500, detail="Failed to list tools")
                
                return JSONResponse(content={"tools": result})
            
            else:
                raise HTTPException(status_code=400, detail=f"Action '{action}' not supported for stdio servers")
        
        finally:
            await pool.return_connection(connection)
    
    async def _route_template_request(self, server_id: str, config: Dict[str, Any], 
                                    action: str, *args, **kwargs) -> Any:
        """Route request to template-based server."""
        template_name = config.get("template_name")
        if not template_name:
            raise HTTPException(status_code=500, detail=f"No template_name configured for server '{server_id}'")
        
        # Check if server is deployed, deploy if needed
        if server_id not in self._deployed_servers:
            await self._deploy_template_server(server_id, config)
        
        deployed_config = self._deployed_servers.get(server_id)
        if not deployed_config:
            raise HTTPException(status_code=503, detail=f"Failed to deploy server '{server_id}'")
        
        # Route based on the deployed server type
        if deployed_config.get("transport") == "http":
            # Create HTTP config for routing
            http_config = {
                "type": "http",
                "instances": [{"endpoint": deployed_config["endpoint"]}],
                "load_balancing": "round_robin"
            }
            return await self._route_http_request(server_id, http_config, action, *args, **kwargs)
        else:
            # Default to stdio routing
            stdio_config = {
                "type": "stdio",
                "command": deployed_config.get("command", []),
                "working_dir": deployed_config.get("working_dir"),
                "env_vars": deployed_config.get("env_vars", {})
            }
            return await self._route_stdio_request(server_id, stdio_config, action, *args, **kwargs)
    
    async def _deploy_template_server(self, server_id: str, config: Dict[str, Any]) -> None:
        """Deploy a template-based server."""
        template_name = config["template_name"]
        
        try:
            # Get template data
            templates = self.template_discovery.discover_templates()
            template_data = templates.get(template_name)
            
            if not template_data:
                raise ValueError(f"Template '{template_name}' not found")
            
            # Generate run configuration
            instances = config.get("instances", 1)
            template_config = config.get("config", {})
            
            run_config = self.server_manager.generate_run_config(
                template_data=template_data,
                transport="http",  # Prefer HTTP for gateway routing
                configuration=template_config
            )
            
            if not run_config:
                raise ValueError(f"Failed to generate run config for template '{template_name}'")
            
            # Store deployment info
            self._deployed_servers[server_id] = run_config
            logger.info("Deployed template server: %s -> %s", server_id, template_name)
            
        except Exception as e:
            logger.error("Failed to deploy template server %s: %s", server_id, e)
            raise
    
    async def start(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """
        Start the gateway server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI is required for the gateway server")
        
        gateway_config = self.registry.get_gateway_config()
        host = gateway_config.get("host", host)
        port = gateway_config.get("port", port)
        
        logger.info("Starting MCP Gateway on %s:%d", host, port)
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    async def shutdown(self) -> None:
        """Shutdown the gateway and clean up resources."""
        logger.info("Shutting down MCP Gateway")
        await self.load_balancer.cleanup()
        # Clean up deployed servers if needed
        for server_id in list(self._deployed_servers.keys()):
            del self._deployed_servers[server_id]
        logger.info("MCP Gateway shutdown complete")


async def main():
    """Main entry point for the gateway server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Gateway Server")
    parser.add_argument(
        "--registry", "-r",
        type=str,
        help="Path to server registry configuration file"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create and start gateway
    gateway = MCPGateway(registry_path=args.registry)
    
    try:
        await gateway.start(host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await gateway.shutdown()


if __name__ == "__main__":
    asyncio.run(main())