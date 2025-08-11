from mcp_template.client import MCPClient

client = MCPClient()
server = client.start_server("demo")
print("Server started:", server)
client.stop_server(server.get("deployment_name"))
