import json
import subprocess


class Pipe:
    def __init__(self, command: list[str]):
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )

    def write(self, data: str):
        if self.process.stdin:
            self.process.stdin.write(data)
            self.process.stdin.flush()

    def readline(self) -> str:
        if self.process.stdout:
            return self.process.stdout.readline().strip()
        return ""

    def terminate(self):
        self.process.terminate()


class MCPServer:
    def __init__(self, name: str, command: str, args: list[str]):
        self.name = name
        self.command = [command] + args
        self._id_counter = 0
        self.process: Pipe = Pipe(self.command)

        # 1. Initialize handshake
        self._send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "fittencode-vim-agent", "version": "1.0.0"},
            },
        )
        # 2. Send initialized notification
        notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        self.process.write(json.dumps(notification) + "\n")
        # 3. Cache available tools
        self.tools_cache = self._send_request("tools/list", {}).get("tools", [])

    def _send_request(self, method: str, params: dict) -> dict:
        self._id_counter += 1
        req_id = self._id_counter
        request = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}

        try:
            self.process.write(json.dumps(request) + "\n")

            line = self.process.readline()
            if not line:
                return {"error": "Server disconnected"}

            response = json.loads(line)
            if response.get("id") == req_id:
                if "error" in response:
                    return {"error": response["error"]}
                return response.get("result", {})
        except Exception as e:
            return {"error": str(e)}
        return {}

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        res = self._send_request(
            "tools/call", {"name": tool_name, "arguments": arguments}
        )

        if "error" in res:
            return f"MCP Error: {res['error']}"

        content_list = res.get("content", [])
        texts = [c["text"] for c in content_list if c.get("type") == "text"]
        return "\n".join(texts) if texts else "Success (no output)"

    def stop(self):
        self.process.terminate()


class MCPManager:
    """
    Manages multiple MCP servers and provides a unified tool interface for the Agent.
    """

    def __init__(self):
        self.servers: dict[str, MCPServer] = {}
        self.schema_cache: list[dict] = []

    def add_server(self, name: str, command: str, args: list[str] | None = None):
        """Register and start an MCP server."""
        try:
            self.servers[name] = MCPServer(name, command, args or [])
        except Exception:
            # Silent fail for robustness in CLI
            pass
        finally:
            for tool in self.servers[name].tools_cache:
                self.schema_cache.append(
                    {
                        "tool": tool["name"],
                        "description": tool.get("description", ""),
                        "arguments": tool.get("inputSchema", {}).get("properties", {}),
                    }
                )

    def get_tools_schema(self) -> list:
        return self.schema_cache

    def execute(self, tool_name: str, **kwargs) -> str:
        for server in self.servers.values():
            if any(t["name"] == tool_name for t in server.tools_cache):
                return server.call_tool(tool_name, kwargs)
        return f"Unknown tool: {tool_name}"

    def shutdown(self):
        for server in self.servers.values():
            server.stop()
