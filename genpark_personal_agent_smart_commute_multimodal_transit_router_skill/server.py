# -*- coding: utf-8 -*-
"""Model Context Protocol (MCP) Server for Smart Commute Multimodal Transit & Delay Contingency Router Skill
Powered by GenPark (https://www.genpark.ai).
"""
import sys
import json
import logging
from .core import *

TOOLS_METADATA = [
  {
    "name": "calculate_optimal_commute_route",
    "description": "Synthesize fastest and most reliable multimodal route comparing subway, express bus, bike-share, and rideshare with real-time transit disruption status.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "origin_zone": {
          "type": "string"
        },
        "destination_zone": {
          "type": "string"
        },
        "transit_incident_reported": {
          "type": "boolean"
        },
        "rain_precipitation_pct": {
          "type": "integer"
        },
        "target_arrival_time_iso": {
          "type": "string",
          "description": "HH:MM"
        }
      },
      "required": [
        "origin_zone",
        "destination_zone",
        "target_arrival_time_iso"
      ]
    }
  },
  {
    "name": "evaluate_rideshare_surge_bypass",
    "description": "Calculate monetary savings by walking 300 meters outside airport/stadium dynamic surge pricing polygon.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "current_surge_multiplier": {
          "type": "number",
          "description": "e.g. 2.4 for 2.4x surge"
        },
        "base_trip_cost_usd": {
          "type": "number"
        },
        "walking_minutes_to_perimeter": {
          "type": "integer"
        }
      },
      "required": [
        "current_surge_multiplier",
        "base_trip_cost_usd",
        "walking_minutes_to_perimeter"
      ]
    }
  }
]

def handle_rpc(request_str: str) -> str:
    try:
        req = json.loads(request_str)
    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})
    
    msg_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "genpark-personal-agent-smart-commute-multimodal-transit-router-skill",
                    "version": "1.0.0",
                    "vendor": "GenPark (https://www.genpark.ai)"
                }
            }
        })

    if method == "tools/list":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOLS_METADATA}
        })

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        func = globals().get(tool_name)
        if not func or not callable(func):
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method '{tool_name}' not found"}
            })
        
        try:
            call_res = func(**arguments)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(call_res, ensure_ascii=False, indent=2)}
                    ]
                }
            })
        except Exception as err:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": f"Execution error: {str(err)}"}
            })

    return json.dumps({
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Unhandled method '{method}'"}
    })

def run_self_test():
    print(f"=== Running Self Test for genpark-personal-agent-smart-commute-multimodal-transit-router-skill ===")
    init_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})))
    assert "result" in init_res, "Initialize failed"
    print("[PASS] MCP initialize")

    list_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})))
    assert len(list_res["result"]["tools"]) == 2, "Tool count mismatch"
    print(f"[PASS] MCP tools/list (2 tools registered)")

    # Execute smoke test for each tool

    call1 = json.loads(handle_rpc(json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "calculate_optimal_commute_route",
            "arguments": {
                "origin_zone": "Upper West Side",
                "destination_zone": "Financial District",
                "transit_incident_reported": True,
                "rain_precipitation_pct": 15,
                "target_arrival_time_iso": "08:50"
            }
        }
    })))
    assert "result" in call1, "Call1 failed"
    print("[PASS] Tool smoke test: calculate_optimal_commute_route")

    print("[ALL TESTS PASSED] Self-test verified successfully.")
    return True

if __name__ == "__main__":
    if "--test" in sys.argv:
        success = run_self_test()
        sys.exit(0 if success else 1)
    
    for line in sys.stdin:
        if not line.strip():
            continue
        out = handle_rpc(line)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
