"""SINTA MCP Server (sinta-mcp-server).

Exposes SINTA Kemdikbud journal accreditation data over standard MCP (Model Context Protocol) stdio.
Free, open, and requires no API key.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from core.integrations.mcp_client import MCPClientWrapper

mcp_client = MCPClientWrapper()


def handle_request(req: dict[str, Any]) -> dict[str, Any]:
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "sinta-mcp-server", "version": "1.0.0"},
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "search_sinta",
                        "description": "Cari informasi akreditasi jurnal ilmiah Indonesia di SINTA (S1 sampai S6) dan indeks Garuda.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "journal_name": {
                                    "type": "string",
                                    "description": "Nama jurnal ilmiah (contoh: Jurnal Komunikasi Indonesia)",
                                }
                            },
                            "required": ["journal_name"],
                        },
                    },
                    {
                        "name": "verify_reference_reputation",
                        "description": "Verifikasi reputasi naskah/jurnal berdasarkan standar Scopus dan SINTA.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "Judul artikel"},
                                "journal": {"type": "string", "description": "Nama jurnal"},
                                "doi": {"type": "string", "description": "DOI artikel (opsional)"},
                            },
                            "required": ["title"],
                        },
                    },
                ]
            },
        }

    if method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "search_sinta":
            res = mcp_client.search_sinta(args.get("journal_name", ""))
            data = res.__dict__ if res else {"status": "not_found", "message": "Jurnal tidak terdaftar di indeks SINTA"}
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]},
            }

        if tool_name == "verify_reference_reputation":
            rep = mcp_client.audit_reference_reputation(
                title=args.get("title", ""),
                journal=args.get("journal"),
                doi=args.get("doi"),
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(rep, indent=2)}]},
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            res = handle_request(req)
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_res = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {e}"},
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
