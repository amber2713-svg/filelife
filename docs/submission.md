# 保研Agent - 项目提交文档

> 中国科学技术大学"一〇七杯"算力与智能体开发大赛 · 智能体赛道

---

## 一、项目概述

### 1.1 项目名称

保研Agent —— 基于 ReAct + Function Calling 的自主保研规划智能体

### 1.2 项目背景

保研（推荐免试研究生）是本科生升学的重要途径，但信息分散、流程复杂、竞争激烈。每年大量学生因信息不对称、准备不充分而错失理想院校。

### 1.3 解决方案

本项目构建了一个**自主决策的智能体**，采用 ReAct（Reasoning + Acting）模式，通过 OpenAI Function Calling 接口自主调用搜索、知识库、模板等工具，为用户生成数据驱动、个性化、可执行的保研攻略。

**与预设流水线的本质区别**：Agent 不是按固定顺序执行7个Prompt，而是根据用户问题自主决定调用什么工具、搜索什么信息、何时生成最终回答。

---

## 二、技术架构

### 2.1 核心架构：ReAct + Function Calling

```
用户输入
    │
    ▼
┌──────────────────────────────────────┐
│           BaoyanAgent                │
│                                      │
│   ┌────────────────────────────┐     │
│   │    ReAct Loop (最多15轮)    │     │
│   │                            │     │
│   │  1. Thought (思考)          │     │
│   │     ↓                      │     │
│   │  2. Action (工具调用)       │     │
│   │     ↓                      │     │
│   │  3. Observation (观察结果)  │     │
│   │     ↓                      │     │
│   │  4. 信息充足？→ 生成攻略    │     │
│   │     否 → 回到 1            │     │
│   └────────────────────────────┘     │
│                                      │
│   ┌────────────────────────────┐     │
│   │       工具层 (6个)          │     │
│   │  web_search   web_fetch    │     │
│   │  knowledge_base_query      │     │
│   │  knowledge_base_list       │     │
│   │  template_render           │     │
│   │  template_list             │     │
│   └────────────────────────────┘     │
└──────────────────────────────────────┘
    │
    ▼
  Markdown 攻略（流式输出到前端）
```

### 2.2 工作流程示例

以"中科大CS大三，想保研清华"为例：

```
[Thought] 用户想了解保研清华的策略。先查询夏令营流程。
[Action]  knowledge_base_query(topic="夏令营")
[Obs]     返回夏令营时间线、申请条件...
[Thought] 了解了基本流程。搜索清华CS夏令营最新政策。
[Action]  web_search(query="清华大学计算机系 夏令营 2026")
[Obs]     返回报名截止日期、入营要求...
[Thought] 再查询面试技巧。
[Action]  knowledge_base_query(topic="面试技巧")
[Obs]     返回高频问题、准备建议...
[Thought] 信息充足，生成完整攻略。
[Output]  完整Markdown攻略...
```

### 2.3 工具层

| 工具 | 功能 | 降级策略 |
|------|------|----------|
| `web_search` | 搜索互联网获取最新信息 | 本地知识库（20+条目） |
| `web_fetch` | 抓取网页内容 | 返回提示信息 |
| `knowledge_base_query` | 查询结构化知识库 | 内置保研全流程知识 |
| `knowledge_base_list` | 列出知识库主题 | - |
| `template_render` | 渲染邮件/简历模板 | 内置4套核心模板 |
| `template_list` | 列出可用模板 | - |

### 2.4 Web应用架构

```
浏览器 ←── SSE ──── Flask (app.py)
                        │
                        ├── BaoyanAgent (后台线程)
                        │     ├── ReAct Loop
                        │     └── Tool Calls
                        └── 工具层
```

- 前端通过 SSE (Server-Sent Events) 实时接收 Agent 每一步
- Agent 在后台线程运行，不阻塞 Web 服务
- 思维链（Thought/Action/Observation）实时可视化

---

## 三、评分维度对应

### 3.1 创新性

- **自主决策Agent**：不是预设流水线，Agent 通过 ReAct 模式自主决定行动序列
- **Function Calling**：基于 OpenAI 标准接口，Agent 自主选择工具、构造参数
- **思维链可视化**：Web UI 实时展示 Agent 的思考过程，用户可以"看到"Agent如何推理
- **真正的智能体**：与传统 chatbot 不同，Agent 能主动搜索、查询、分析，而非仅靠训练知识回答

### 3.2 实用性

- **覆盖保研全流程**：政策查询、院校分析、导师匹配、时间规划、材料准备、面试指导
- **个性化输出**：基于用户具体背景生成定制化攻略
- **实用模板**：套磁邮件、推荐信请求、英文自我介绍等 4 套可直接使用的模板
- **本地知识库**：内置推免政策、夏令营流程、面试技巧、套磁指南等结构化知识
- **双入口**：Web 应用（可视化思维链）+ CLI（命令行快速使用）

### 3.3 技术难度

- **ReAct 循环实现**：多轮 Thought → Action → Observation 迭代，最多15轮
- **Function Calling 集成**：6个工具定义为 JSON Schema，Agent 自主调用
- **SSE 流式推送**：Agent 每产生一步就实时推送到前端
- **线程并发**：Agent 在后台线程运行，SSE 循环同步推送步骤
- **多级降级**：API 不可用 → Mock 模式（模拟完整 ReAct 过程）
- **XSS 防护**：前端使用 DOMParser 白名单过滤 HTML

### 3.4 完成度

- **端到端可运行**：从用户输入到攻略输出完整流程可运行
- **双模式**：API 模式（真实 LLM）+ Mock 模式（无 API Key 演示）
- **完整文档**：README、提交文档、模板文件、示例输出
- **代码质量**：模块化设计，类型注解，清晰的项目结构

---

## 四、运行指南

### 4.1 环境要求

- Python 3.11+
- 网络环境（可选，用于调用 LLM API）

### 4.2 安装与配置

```bash
# 克隆项目
git clone <repo-url>
cd zzzlife

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（可选）
export LLM_API_BASE="https://api.llm.ustc.edu.cn/v1"
export LLM_API_KEY="your-api-key"
export LLM_MODEL="glm-5.2"
```

### 4.3 运行方式

**Web应用（推荐）**

```bash
python app.py
# 浏览器打开 http://localhost:8080
```

**命令行**

```bash
python main.py --demo          # 演示模式
python main.py                 # 交互式对话
python main.py --input "..."   # 单次运行
```

### 4.4 无 API Key 运行

不设置 `LLM_API_KEY` 环境变量，自动启用 Mock 模式。Mock 模式会模拟完整的 ReAct 过程（思考 → 工具调用 → 观察 → 生成攻略），无需任何外部依赖即可体验完整功能。

---

## 五、项目结构

```
zzzlife/
├── app.py                     # Web应用入口（Flask + SSE）
├── main.py                    # CLI入口
├── requirements.txt           # Python依赖
├── .env.example               # 环境变量示例
├── .gitignore
├── prompt_0.md                # 原始提示词 v1.0
├── prompt_1.md                # 改进提示词 v2.0
├── README.md
├── docs/
│   └── submission.md          # 本提交文档
├── static/
│   ├── style.css              # Web界面样式（暗色主题）
│   └── app.js                 # Web界面逻辑（SSE + 思维链渲染）
├── templates/
│   ├── index.html             # Web界面模板
│   ├── email_templates.md     # 邮件模板集
│   └── resume_template.md     # 简历模板
├── output/
│   └── sample_guide.md        # 示例攻略
└── src/
    ├── config.py              # 配置管理
    ├── agent.py               # 核心：自主ReAct Agent
    ├── tools/
    │   ├── search.py          # 搜索工具 + 本地知识库
    │   ├── knowledge_base.py  # 结构化知识库
    │   └── templates.py       # 模板引擎（4套模板）
    └── utils/
        └── __init__.py        # 工具函数
```

---

## 六、演示流程

### 6.1 Web应用演示

1. 启动服务：`python app.py`
2. 打开浏览器访问 `http://localhost:8080`
3. 点击"一键演示"或输入用户信息
4. 观察 Agent 思维链实时展示：
   - 💭 思考步骤（紫色）
   - 🔧 工具调用（橙色）
   - 📋 工具结果（灰色）
5. 最终生成完整 Markdown 攻略

### 6.2 CLI 演示

```bash
python main.py --demo
```

观察控制台输出的 ReAct 过程：
```
💭 思考: 用户想了解保研相关信息...
🔧 调用工具: knowledge_base_query
   参数: {"topic": "夏令营"}
📋 结果: {...}
💭 思考: 了解了夏令营流程，搜索院校信息...
...
==================================================
# 保研攻略 - 个性化定制版
...
```

---

## 七、技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 语言 | Python 3.11+ | 类型注解、dataclass |
| LLM | GLM-5.2 (api.llm.ustc.edu.cn) | OpenAI 兼容接口 |
| Agent SDK | openai >= 1.0.0 | Function Calling |
| Web框架 | Flask >= 3.0.0 | 轻量级 |
| 流式传输 | SSE (Server-Sent Events) | 实时推送 |
| 前端 | 原生 JS | 无框架依赖 |

---

## 八、团队信息

- **参赛赛道**: 智能体赛道
- **项目名称**: 保研Agent - 基于 ReAct + Function Calling 的自主保研规划智能体

---

*本文档为"一〇七杯"算力与智能体开发大赛参赛提交材料*
