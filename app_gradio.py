"""
保研Agent - HuggingFace Spaces 版本
Gradio 前端，展示 ReAct 思维链
"""

import threading
import time
import gradio as gr

from src.config import config
from src.agent import BaoyanAgent, AgentStep

agents: dict[str, BaoyanAgent] = {}

CSS = """
.thinking-box { font-size: 13px; max-height: 400px; overflow-y: auto; }
"""


def get_agent(session_id: str) -> BaoyanAgent:
    if session_id not in agents:
        agents[session_id] = BaoyanAgent(config.llm)
    return agents[session_id]


def format_steps(steps: list[dict]) -> str:
    lines = []
    for s in steps:
        if s["type"] == "thought":
            lines.append(f"💭 **思考**: {s['content']}")
            lines.append("")
        elif s["type"] == "tool_call":
            lines.append(f"🔧 **调用工具**: `{s['tool_name']}`")
            if s["tool_args"]:
                lines.append(f"   参数: `{s['tool_args']}`")
            lines.append("")
        elif s["type"] == "tool_result":
            preview = s["content"][:200] + "..." if len(s["content"]) > 200 else s["content"]
            lines.append(f"📋 **结果**: {preview}")
            lines.append("")
    return "\n".join(lines)


def chat_fn(user_message: str, history: list, thinking: str, request: gr.Request):
    if not user_message.strip():
        yield history, thinking, "空闲"
        return

    session_id = request.session_hash
    agent = get_agent(session_id)

    steps_list = []

    def on_step(step: AgentStep):
        steps_list.append(step.to_dict())

    result_holder = {"content": ""}
    error_holder = {"error": ""}

    def run():
        try:
            result_holder["content"] = agent.chat(user_message, on_step=on_step)
        except Exception as e:
            error_holder["error"] = str(e)

    thread = threading.Thread(target=run)
    thread.start()

    history = (history or []) + [{"role": "user", "content": user_message}]

    sent = 0
    while thread.is_alive() or sent < len(steps_list):
        while sent < len(steps_list):
            steps_text = format_steps(steps_list)
            yield history + [{"role": "assistant", "content": "⏳ 生成中..."}], steps_text, "🔄 思考中..."
            sent += 1
        time.sleep(0.2)

    thread.join()

    if error_holder["error"]:
        yield history + [{"role": "assistant", "content": f"❌ 错误: {error_holder['error']}"}], steps_text, "空闲"
    else:
        content = result_holder["content"]
        yield history + [{"role": "assistant", "content": content}], steps_text, "空闲"


def demo_fn(history: list, thinking: str, request: gr.Request):
    demo_input = (
        "我是中科大计算机科学与技术专业大三上的学生，"
        "绩点3.7/4.0，专业排名前15%，"
        "六级550分，有一篇CCF-B会议的在投论文，"
        "参加过ACM-ICPC区域赛获铜奖。"
        "目标院校是清华、北大、中科院计算所的计算机相关专业。"
        "请帮我制定一份详细的保研攻略。"
    )
    yield from chat_fn(demo_input, history, thinking, request)


def build_ui():
    with gr.Blocks(title="保研Agent - ReAct + Function Calling") as app:
        gr.Markdown("""
# 🎓 保研Agent
### 基于 ReAct + Function Calling 的自主保研规划智能体

Agent 会自主搜索信息、查询知识库、分析数据，实时展示推理过程，最终生成个性化保研攻略。
""")

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="对话", height=500)
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="例如：我是中科大CS大三，GPA 3.8，想保研清华...",
                        scale=4,
                        show_label=False,
                    )
                    submit_btn = gr.Button("发送", variant="primary", scale=1)

                with gr.Row():
                    demo_btn = gr.Button("🎯 一键演示", variant="secondary")
                    clear_btn = gr.Button("🗑️ 清空对话")

            with gr.Column(scale=1):
                status = gr.Textbox(label="Agent 状态", value="空闲", interactive=False)
                thinking = gr.Markdown(value="*等待用户输入...*", elem_classes=["thinking-box"])

                gr.Markdown("### 🔧 可用工具")
                gr.Markdown("""
- `web_search` - 搜索互联网
- `web_fetch` - 抓取网页
- `knowledge_base_query` - 查询知识库
- `knowledge_base_list` - 列出知识库主题
- `template_render` - 渲染模板
- `template_list` - 列出模板
""")

                mode = "API 模式" if config.llm.api_key else "Mock 模式"
                gr.Markdown(f"### 运行模式\n**{mode}** ({config.llm.model})")

        msg.submit(chat_fn, [msg, chatbot, thinking], [chatbot, thinking, status]).then(
            lambda: "", None, msg
        )
        submit_btn.click(chat_fn, [msg, chatbot, thinking], [chatbot, thinking, status]).then(
            lambda: "", None, msg
        )
        demo_btn.click(demo_fn, [chatbot, thinking], [chatbot, thinking, status])

        def clear():
            return [], "*等待用户输入...*", "空闲"
        clear_btn.click(clear, None, [chatbot, thinking, status])

    return app


if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=7860, css=CSS, theme=gr.themes.Soft())
