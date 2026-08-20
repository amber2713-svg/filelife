#!/usr/bin/env python3
"""
保研Agent - CLI入口
ReAct + Function Calling 自主智能体

Usage:
    python main.py                # 交互式对话
    python main.py --demo         # 演示模式
    python main.py --input "..."  # 单次运行
"""

import argparse
import sys

from src.config import config
from src.agent import BaoyanAgent, AgentStep
from src.utils import setup_logging


def print_step(step: AgentStep):
    icons = {"thought": "💭", "tool_call": "🔧", "tool_result": "📋"}
    icon = icons.get(step.type, "")
    if step.type == "thought":
        print(f"\n{icon} 思考: {step.content}")
    elif step.type == "tool_call":
        print(f"\n{icon} 调用工具: {step.tool_name}")
        if step.tool_args:
            print(f"   参数: {step.tool_args}")
    elif step.type == "tool_result":
        preview = step.content[:150] + "..." if len(step.content) > 150 else step.content
        print(f"\n{icon} 结果: {preview}")


WELCOME = """
╔══════════════════════════════════════════╗
║         保研Agent v3.0                   ║
║   ReAct + Function Calling              ║
║   一〇七杯 · 智能体赛道                  ║
╚══════════════════════════════════════════╝

你好！我是保研Agent，一个能自主搜索信息、分析数据的智能助手。

我会通过 ReAct 模式工作：思考 → 调用工具 → 观察结果 → 继续思考
直到信息充足后生成完整的保研攻略。

可用工具: web_search, web_fetch, knowledge_base_query, template_render 等

请告诉我你的情况，输入 'quit' 退出。
"""


def interactive_mode():
    print(WELCOME)
    agent = BaoyanAgent(config.llm)

    while True:
        try:
            user_input = input("\n你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！祝保研顺利！")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("再见！祝保研顺利！")
            break

        print()
        result = agent.chat(user_input, on_step=print_step)
        print(f"\n{'='*50}")
        print(result)
        print(f"{'='*50}")


def demo_mode():
    print("[演示模式] 使用预设用户信息...\n")
    agent = BaoyanAgent(config.llm)

    demo_input = (
        "我是中科大计算机科学与技术专业大三上的学生，"
        "绩点3.7/4.0，专业排名前15%，"
        "六级550分，有一篇CCF-B会议的在投论文，"
        "参加过ACM-ICPC区域赛获铜奖。"
        "目标院校是清华、北大、中科院计算所的计算机相关专业。"
        "请帮我制定一份详细的保研攻略。"
    )

    print(f"用户输入: {demo_input}\n")
    result = agent.chat(demo_input, on_step=print_step)
    print(f"\n{'='*50}")
    print(result)


def single_run(user_input: str):
    agent = BaoyanAgent(config.llm)
    result = agent.chat(user_input, on_step=print_step)
    print(result)


def main():
    parser = argparse.ArgumentParser(description="保研Agent - ReAct自主智能体")
    parser.add_argument("--demo", action="store_true", help="演示模式")
    parser.add_argument("--input", type=str, help="单次运行输入")
    parser.add_argument("--log-level", default="WARNING", help="日志级别")
    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.demo:
        demo_mode()
    elif args.input:
        single_run(args.input)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
