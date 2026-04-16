import asyncio
import sys
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

async def main():
    # Construct complete absolute path for DB
    db_abs_path = str((Path.cwd() / "data" / "db" / "wealth_advisor.db").absolute())

    # Build absolute paths for the executables to bypass Windows WinError 2 
    scripts_dir = Path(sys.executable).parent
    sqlite_exe_path = str(scripts_dir / "mcp-sqlite.exe") if sys.platform == "win32" else "mcp-sqlite"

    client = MultiServerMCPClient({
        "sqlite": {
            "transport": "stdio",
            "command": sqlite_exe_path,
            "args": [db_abs_path],
        }
    })
    
    async with client.session("sqlite") as sqlite_session:
        sqlite_tools = await load_mcp_tools(sqlite_session)
        print("FOUND", len(sqlite_tools), "SQLITE TOOLS!")
        for t in sqlite_tools:
            print("-", t.name)

if __name__ == "__main__":
    asyncio.run(main())
