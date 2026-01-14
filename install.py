#!/usr/bin/env python3
"""
Helper script to configure Claude Desktop with the YouTube Music MCP server
"""
import json
import os
from pathlib import Path
import platform


def get_config_path() -> Path:
    """Get Claude Desktop config path for current OS"""
    system = platform.system()
    if system == "Darwin":  # macOS
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    elif system == "Windows":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "Claude/claude_desktop_config.json"
        raise RuntimeError("APPDATA environment variable not found")
    else:  # Linux
        return Path.home() / ".config/Claude/claude_desktop_config.json"


def install_mcp_server():
    """Add this MCP server to Claude Desktop config"""
    config_path = get_config_path()
    project_path = Path(__file__).parent.absolute()

    print(f"Project path: {project_path}")
    print(f"Config path: {config_path}")

    # Read existing config or create new one
    if config_path.exists():
        with open(config_path, "r") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}
    else:
        config = {}

    # Ensure mcpServers key exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Add our server
    config["mcpServers"]["youtube-music"] = {
        "command": "python",
        "args": ["-m", "src.server"],
        "cwd": str(project_path),
    }

    # Write back
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\nAdded YouTube Music MCP server to {config_path}")
    print("\nRestart Claude Desktop to use the new server.")
    print("\nMake sure you have run OAuth setup first:")
    print("  python -m src.auth")


def uninstall_mcp_server():
    """Remove this MCP server from Claude Desktop config"""
    config_path = get_config_path()

    if not config_path.exists():
        print("Claude Desktop config not found. Nothing to remove.")
        return

    with open(config_path, "r") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            print("Could not parse config file.")
            return

    if "mcpServers" in config and "youtube-music" in config["mcpServers"]:
        del config["mcpServers"]["youtube-music"]

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        print(f"Removed YouTube Music MCP server from {config_path}")
        print("Restart Claude Desktop for changes to take effect.")
    else:
        print("YouTube Music MCP server not found in config.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        uninstall_mcp_server()
    else:
        install_mcp_server()
