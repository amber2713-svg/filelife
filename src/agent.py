"""
自主保研Agent - 基于ReAct + Function Calling
Agent自主决定使用什么工具、何时生成攻略
"""

import json
import logging
import time
from typing import Any, Callable

from openai import OpenAI

from src.config import LLMConfig
from src.tools.search import web_search, web_fetch
from src.tools.knowledge_base import knowledge_base_query, knowledge_base_list
from src.tools.templates import template_render, template_list

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是"保研Agent"——一个专业的保研规划智能助手。

你的任务是通过主动搜索信息、查询知识库、使用模板，为用户生成一份全面、个性化、可执行的保研攻略。

## 工作方式

你必须按照 ReAct（Reasoning + Acting）模式工作：
1. **思考（Thought）**: 分析当前情况，决定下一步做什么
2. **行动（Action）**: 调用工具获取信息
3. **观察（Observation）**: 分析工具返回的结果
4. **重复**: 直到收集到足够信息，生成最终攻略

## 工具使用策略

- 先用 `knowledge_base_query` 了解保研基本流程
- 用 `web_search` 搜索用户目标院校的最新政策
- 用 `template_render` 生成邮件模板等实用内容
- 信息充足后，直接输出完整的Markdown攻略

## 攻略必须包含

1. 个人定位分析（SWOT）
2. 保研流程时间线
3. 硬性条件准备（成绩、英语、科研）
4. 院校与导师选择策略
5. 材料准备清单
6. 面试应试指南
7. 避坑指南

## 输出要求

- 使用Markdown格式
- 关键数据用表格呈现
- 重要提醒用引用块标注
- 所有建议具体可操作
- 信息标注来源

现在开始。先了解用户背景，然后主动搜索信息，最后生成攻略。"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索互联网获取最新信息。用于查找院校政策、夏令营通知、经验帖等时效性信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，如：'清华大学计算机系 夏令营 2026'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "抓取指定URL的网页内容。用于深入阅读搜索结果中的具体页面。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "要抓取的网页URL"},
                    "extract_prompt": {"type": "string", "description": "提取内容的指导，如'提取报名截止日期和要求'"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "knowledge_base_query",
            "description": "查询保研知识库。包含推免政策、夏令营流程、面试技巧、套磁指南等结构化知识。",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "查询主题，如：'夏令营'、'推免资格'、'面试技巧'、'套磁'"}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "knowledge_base_list",
            "description": "列出知识库中所有可用主题。",
            "parameters": {
                "type": "object",
                "properties": {},
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "template_render",
            "description": "渲染预设模板。可用模板：mentor_contact_email（导师套磁邮件）、follow_up_email（跟进邮件）、recommendation_request（推荐信请求）、self_introduction_en（英文自我介绍）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "template_name": {
                        "type": "string",
                        "description": "模板名称",
                        "enum": ["mentor_contact_email", "follow_up_email", "recommendation_request", "self_introduction_en"]
                    },
                    "variables": {
                        "type": "object",
                        "description": "模板变量键值对，如 {\"name\": \"张三\", \"university\": \"中科大\"}"
                    }
                },
                "required": ["template_name", "variables"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "template_list",
            "description": "列出所有可用的模板及其说明。",
            "parameters": {
                "type": "object",
                "properties": {},
            }
        }
    },
]

TOOL_FUNCTIONS: dict[str, Callable] = {
    "web_search": lambda args: json.dumps(web_search(args.get("query", "")), ensure_ascii=False),
    "web_fetch": lambda args: web_fetch(args.get("url", ""), args.get("extract_prompt", "")),
    "knowledge_base_query": lambda args: json.dumps(knowledge_base_query(args.get("topic", "")), ensure_ascii=False),
    "knowledge_base_list": lambda args: json.dumps(knowledge_base_list(), ensure_ascii=False),
    "template_render": lambda args: template_render(
        args.get("template_name", ""),
        args.get("variables", {})
    ),
    "template_list": lambda args: json.dumps(template_list(), ensure_ascii=False),
}


class AgentStep:
    """Agent执行的一步，用于前端展示"""

    def __init__(self, step_type: str, content: str):
        self.type = step_type  # "thought", "tool_call", "tool_result", "content"
        self.content = content
        self.tool_name = ""
        self.tool_args = ""

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "content": self.content,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
        }


class BaoyanAgent:
    """自主保研Agent - ReAct + Function Calling"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = config.api_key
        self.use_mock = not bool(self.api_key)
        self.messages: list[dict] = []
        self.steps: list[AgentStep] = []
        self.max_iterations = 15

        if not self.use_mock:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=config.api_base.rstrip("/"),
            )

    def chat(self, user_input: str, on_step: Callable[[AgentStep], None] | None = None) -> str:
        """
        处理用户输入，返回最终回复。
        on_step: 每产生一步就回调，用于实时展示
        """
        self.steps = []

        if not self.messages:
            self.messages.append({"role": "system", "content": SYSTEM_PROMPT})

        self.messages.append({"role": "user", "content": user_input})

        if self.use_mock:
            return self._mock_chat(user_input, on_step)

        return self._real_chat(on_step)

    def _real_chat(self, on_step: Callable | None = None) -> str:
        """真正的ReAct循环，使用OpenAI function calling"""
        for iteration in range(self.max_iterations):
            logger.info(f"Agent iteration {iteration + 1}/{self.max_iterations}")

            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=self.messages,
                tools=TOOLS,
                temperature=0.7,
                max_tokens=self.config.max_tokens,
            )

            choice = response.choices[0]
            message = choice.message

            if message.tool_calls:
                self.messages.append(message.model_dump())

                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)

                    step = AgentStep("tool_call", f"调用 {func_name}")
                    step.tool_name = func_name
                    step.tool_args = json.dumps(func_args, ensure_ascii=False)
                    self.steps.append(step)
                    if on_step:
                        on_step(step)

                    logger.info(f"Tool call: {func_name}({func_args})")

                    if func_name in TOOL_FUNCTIONS:
                        result = TOOL_FUNCTIONS[func_name](func_args)
                    else:
                        result = json.dumps({"error": f"未知工具: {func_name}"})

                    result_step = AgentStep("tool_result", result[:500])
                    result_step.tool_name = func_name
                    self.steps.append(result_step)
                    if on_step:
                        on_step(result_step)

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })

            elif message.content:
                self.messages.append({"role": "assistant", "content": message.content})

                step = AgentStep("content", message.content)
                self.steps.append(step)
                if on_step:
                    on_step(step)

                return message.content

            else:
                break

        return "Agent达到最大迭代次数，请尝试简化问题。"

    def _mock_chat(self, user_input: str, on_step: Callable | None = None) -> str:
        """Mock模式 - 模拟ReAct过程"""
        mock_sequence = [
            ("thought", "用户想了解保研相关信息。我需要先了解保研基本流程，然后搜索具体院校政策。"),
            ("tool_call", "knowledge_base_query", {"topic": "夏令营"}),
            ("tool_result", "knowledge_base_query", json.dumps(knowledge_base_query("夏令营"), ensure_ascii=False)[:500]),
            ("thought", "了解了夏令营流程。接下来搜索用户可能关注的院校信息。"),
            ("tool_call", "web_search", {"query": "计算机保研夏令营 清华北大 2026"}),
            ("tool_result", "web_search", json.dumps(web_search("计算机保研夏令营 清华北大 2026"), ensure_ascii=False)[:500]),
            ("thought", "获取了院校信息。再查询面试技巧相关知识。"),
            ("tool_call", "knowledge_base_query", {"topic": "面试技巧"}),
            ("tool_result", "knowledge_base_query", json.dumps(knowledge_base_query("面试技巧"), ensure_ascii=False)[:500]),
            ("thought", "再查询套磁指南，这对保研很重要。"),
            ("tool_call", "knowledge_base_query", {"topic": "套磁"}),
            ("tool_result", "knowledge_base_query", json.dumps(knowledge_base_query("套磁"), ensure_ascii=False)[:500]),
            ("thought", "信息已经足够充分了。现在生成一份完整的保研攻略。"),
        ]

        for item in mock_sequence:
            step_type = item[0]
            if step_type == "thought":
                step = AgentStep("thought", item[1])
            elif step_type == "tool_call":
                step = AgentStep("tool_call", f"调用 {item[1]}")
                step.tool_name = item[1]
                step.tool_args = json.dumps(item[2], ensure_ascii=False)
            elif step_type == "tool_result":
                step = AgentStep("tool_result", item[2])
                step.tool_name = item[1]
            else:
                continue

            self.steps.append(step)
            if on_step:
                on_step(step)
            time.sleep(0.3)

        guide = self._mock_guide()
        step = AgentStep("content", guide)
        self.steps.append(step)
        if on_step:
            on_step(step)

        self.messages.append({"role": "assistant", "content": guide})
        return guide

    def _mock_guide(self) -> str:
        return """# 保研攻略 - 个性化定制版

> 由保研Agent自主搜索、分析、生成 | 2026-08-20

---

## 一、个人定位分析

### SWOT分析

| 维度 | 分析 |
|------|------|
| **优势 (S)** | 专业基础扎实，有科研/竞赛经历 |
| **劣势 (W)** | 需根据具体情况分析 |
| **机会 (O)** | 各院校扩招，AI方向需求旺盛 |
| **威胁 (T)** | 竞争激烈，信息不对称 |

---

## 二、保研流程时间线

| 阶段 | 时间 | 关键任务 |
|------|------|----------|
| 准备期 | 大三上(9-1月) | 绩点冲刺、科研产出 |
| 材料期 | 大三下(2-4月) | 简历、套磁、推荐信 |
| 夏令营 | 5-8月 | 申请、参营、争取优秀营员 |
| 预推免 | 8-9月 | 补充申请 |
| 九推 | 9月下旬 | 系统确认 |

---

## 三、硬性条件准备

### 3.1 成绩与绩点
- 目标：专业前15%（冲刺top10）
- 重点课程：算法、机器学习、专业核心课

### 3.2 英语水平
- 基本要求：六级425+
- 加分项：托福90+ / 雅思6.5+

### 3.3 科研成果
- 论文：在投/已发均可，重点讲自己的贡献
- 竞赛：ACM/数模/挑战杯等

---

## 四、院校选择策略

| 档位 | 建议 | 数量 |
|------|------|------|
| 冲刺 | 比自身高1-2档的院校 | 1-2所 |
| 匹配 | 与自身实力相当 | 2-3所 |
| 保底 | 确定能进的院校 | 1-2所 |

---

## 五、材料准备清单

- [ ] 个人简历（一页纸，中英文）
- [ ] 个人陈述（1500字以内）
- [ ] 推荐信（2封）
- [ ] 成绩单（加盖公章）
- [ ] 排名证明
- [ ] 英语成绩证明
- [ ] 科研成果证明

---

## 六、面试应试指南

### 高频问题
1. 自我介绍（中英文各3分钟）
2. 科研经历详解
3. 专业基础知识
4. 对研究方向的理解
5. 未来研究计划

### 准备建议
- 模拟面试至少3次
- 熟悉简历上每一句话
- 准备PPT展示科研项目

---

## 七、避坑指南

> ⚠️ 不要只盯一所学校，至少5所保底
> ⚠️ 套磁信不要群发，每封要个性化
> ⚠️ 论文状态如实说明
> ⚠️ 注意夏令营与期末考试时间冲突
> ⚠️ 推荐信提前1个月联系老师

---

## 八、实用模板

### 套磁邮件要点
1. 简明自我介绍
2. 提到导师具体论文
3. 说明自己的相关经历
4. 附上简历和成绩单
5. 表达读研意愿

---

*本攻略由保研Agent基于知识库和实时搜索自动生成。具体政策请以各院校最新通知为准。*
"""

    def reset(self):
        """重置对话历史"""
        self.messages = []
        self.steps = []
