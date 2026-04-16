import asyncio
import os
import sys
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

async def main():
    chroma_abs_path = str((Path.cwd() / "data" / "chroma").absolute())
    scripts_dir = Path(sys.executable).parent
    chroma_exe_path = str(scripts_dir / "chroma-mcp-server.exe") if sys.platform == "win32" else "chroma-mcp-server"

    client = MultiServerMCPClient({
        "chroma": {
            "transport": "stdio",
            "command": chroma_exe_path,
            "args": [],
            "env": {
                **os.environ,
                "CHROMA_CLIENT_TYPE": "persistent",
                "CHROMA_DATA_DIR": chroma_abs_path,
                "LOG_LEVEL": "INFO",
            }
        }
    })
    
    async with client.session("chroma") as chroma_session:
        chroma_tools = await load_mcp_tools(chroma_session)
        print("FOUND", len(chroma_tools), "TOOLS!")
        for t in chroma_tools:
            print("-", t.name)

asyncio.run(main())
