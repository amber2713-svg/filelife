"""
Netlify Function - 保研Agent API
包装 Flask app 为 serverless function
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.config import config
from src.agent import BaoyanAgent, AgentStep

agents = {}


def get_agent(session_id):
    if session_id not in agents:
        agents[session_id] = BaoyanAgent(config.llm)
    return agents[session_id]


def handler(event, context):
    """Netlify Function entry point"""
    
    # CORS headers
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Content-Type": "application/json",
    }
    
    # Handle preflight
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}
    
    # Handle GET /api/config
    if event.get("httpMethod") == "GET":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "llm_api_base": config.llm.api_base,
                "llm_model": config.llm.model,
                "has_api_key": bool(config.llm.api_key),
                "mode": "production" if config.llm.api_key else "mock",
            }),
        }
    
    # Handle POST /api/chat/stream (simplified - no SSE, just return full result)
    if event.get("httpMethod") == "POST":
        try:
            body = json.loads(event.get("body", "{}"))
            user_input = body.get("message", "")
            session_id = body.get("session_id", "default")
            
            if not user_input:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "请输入消息"}),
                }
            
            agent = get_agent(session_id)
            steps_list = []
            
            def on_step(step):
                steps_list.append(step.to_dict())
            
            content = agent.chat(user_input, on_step=on_step)
            
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({
                    "session_id": session_id,
                    "content": content,
                    "steps": steps_list,
                }, ensure_ascii=False),
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": headers,
                "body": json.dumps({"error": str(e)}),
            }
    
    return {
        "statusCode": 404,
        "headers": headers,
        "body": json.dumps({"error": "Not found"}),
    }
