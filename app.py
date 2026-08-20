#!/usr/bin/env python3
"""
保研Agent Web应用 - 展示自主Agent的ReAct过程
Flask + SSE流式输出
"""

import json
import logging
import os
import threading
import time
import uuid

from flask import Flask, render_template, request, jsonify, Response

from src.config import config
from src.agent import BaoyanAgent, AgentStep
from src.utils import setup_logging

setup_logging("WARNING")

app = Flask(__name__)

sessions: dict[str, BaoyanAgent] = {}


def get_or_create_session(session_id: str) -> BaoyanAgent:
    if session_id not in sessions:
        sessions[session_id] = BaoyanAgent(config.llm)
    return sessions[session_id]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json()
    user_input = data.get("message", "").strip()
    session_id = data.get("session_id", str(uuid.uuid4()))

    if not user_input:
        return jsonify({"error": "请输入消息"}), 400

    agent = get_or_create_session(session_id)

    def generate():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

        steps_buffer = []

        def on_step(step: AgentStep):
            steps_buffer.append(step)

        result_holder = {"content": ""}
        error_holder = {"error": ""}

        def run_agent():
            try:
                result_holder["content"] = agent.chat(user_input, on_step=on_step)
            except Exception as e:
                error_holder["error"] = str(e)

        thread = threading.Thread(target=run_agent)
        thread.start()

        sent_steps = 0
        while thread.is_alive() or sent_steps < len(steps_buffer):
            while sent_steps < len(steps_buffer):
                step = steps_buffer[sent_steps]
                yield f"data: {json.dumps({'type': 'step', 'step': step.to_dict()}, ensure_ascii=False)}\n\n"
                sent_steps += 1
            if thread.is_alive():
                time.sleep(0.1)

        thread.join()

        if error_holder["error"]:
            yield f"data: {json.dumps({'type': 'error', 'message': error_holder['error']})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.route("/api/demo", methods=["POST"])
def demo():
    session_id = str(uuid.uuid4())
    agent = get_or_create_session(session_id)

    demo_input = (
        "我是中科大计算机科学与技术专业大三上的学生，"
        "绩点3.7/4.0，专业排名前15%，"
        "六级550分，有一篇CCF-B会议的在投论文，"
        "参加过ACM-ICPC区域赛获铜奖。"
        "目标院校是清华、北大、中科院计算所的计算机相关专业。"
        "请帮我制定一份详细的保研攻略。"
    )

    return jsonify({
        "session_id": session_id,
        "input": demo_input,
    })


@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify({
        "llm_api_base": config.llm.api_base,
        "llm_model": config.llm.model,
        "has_api_key": bool(config.llm.api_key),
        "mode": "production" if config.llm.api_key else "mock",
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(f"\n{'='*50}")
    print(f"  保研Agent Web应用 v3.0")
    print(f"  访问: http://localhost:{port}")
    print(f"  模式: {'API模式 (' + config.llm.model + ')' if config.llm.api_key else 'Mock模式（未配置API Key）'}")
    print(f"{'='*50}\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
