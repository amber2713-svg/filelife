# 保研Agent

> 中国科大"一〇七杯"算力与智能体开发大赛 · 智能体赛道参赛作品

## 项目简介

基于 **ReAct + Function Calling** 的自主保研规划智能体。Agent 自主决定调用哪些工具、搜索什么信息、何时生成攻略——不是预设流水线，而是真正的自主决策。

## 架构设计

```
用户输入
    │
    ▼
┌──────────────────────────────────┐
│         BaoyanAgent              │
│                                  │
│  ┌─────────────────────────┐     │
│  │   ReAct Loop            │     │
│  │   Thought → Action →    │     │
│  │   Observation → repeat  │     │
│  └─────────┬───────────────┘     │
│            │                     │
│   ┌────────┼────────┐           │
│   ▼        ▼        ▼           │
│ web_search  KB    templates     │
│ web_fetch   list    render      │
└──────────────────────────────────┘
    │
    ▼
  Markdown 攻略
```

Agent 通过 OpenAI Function Calling 接口自主调用 6 个工具：

| 工具 | 功能 |
|------|------|
| `web_search` | 搜索互联网获取最新院校政策、夏令营通知 |
| `web_fetch` | 抓取指定URL的网页内容 |
| `knowledge_base_query` | 查询保研知识库（推免政策、面试技巧等） |
| `knowledge_base_list` | 列出知识库所有可用主题 |
| `template_render` | 渲染套磁邮件、自我介绍等模板 |
| `template_list` | 列出所有可用模板 |

## 快速开始

### Web应用（推荐）

```bash
# 创建虚拟环境 & 安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 启动Web服务
python app.py

# 浏览器打开 http://localhost:8080
```

### 命令行模式

```bash
python main.py --demo          # 演示模式
python main.py                 # 交互式对话
python main.py --input "..."   # 单次运行
```

### 配置LLM API（可选）

```bash
export LLM_API_BASE="https://api.llm.ustc.edu.cn/v1"
export LLM_API_KEY="your-api-key"
export LLM_MODEL="glm-5.2"
```

未配置 API Key 时自动启用 Mock 模式，模拟完整的 ReAct 过程。

## 项目结构

```
├── app.py                      # Web应用入口（Flask + SSE流式）
├── main.py                     # CLI入口
├── requirements.txt
├── .env.example
├── prompt_0.md                 # 原始提示词 v1.0
├── prompt_1.md                 # 改进提示词 v2.0
├── docs/
│   └── submission.md           # 比赛提交文档
├── static/
│   ├── style.css               # Web界面样式
│   └── app.js                  # Web界面逻辑（SSE + 思维链展示）
├── templates/
│   ├── index.html              # Web界面模板
│   ├── email_templates.md      # 套磁/推荐信邮件模板
│   └── resume_template.md      # 简历模板
├── output/                     # 生成的攻略输出
│   └── sample_guide.md
└── src/
    ├── config.py               # 配置管理
    ├── agent.py                # 核心：自主ReAct Agent
    ├── tools/
    │   ├── search.py           # 搜索工具 + 本地知识库
    │   ├── knowledge_base.py   # 结构化知识库
    │   └── templates.py        # 模板引擎
    └── utils/
        └── __init__.py
```

## 核心特性

- **自主决策**: Agent 通过 ReAct 模式自主决定搜索什么、查询什么、何时生成
- **Function Calling**: 基于 OpenAI 标准接口，Agent 自主选择和调用工具
- **思维链可视化**: Web UI 实时展示 Agent 的思考、工具调用、观察结果
- **流式输出**: SSE 实时推送 Agent 每一步到前端
- **降级容错**: API 不可用时自动切换 Mock 模式
- **本地知识库**: 内置保研全流程知识（推免政策、夏令营、面试技巧等）
- **实用模板**: 套磁邮件、推荐信请求、英文自我介绍等 4 套模板

## 评分维度

| 维度 | 实现 |
|------|------|
| 创新性 | 自主 ReAct Agent，非预设流水线；思维链实时可视化 |
| 实用性 | 覆盖保研全流程，内置知识库和模板，Web + CLI 双入口 |
| 技术难度 | OpenAI Function Calling、ReAct 循环、SSE 流式推送、多级降级 |
| 完成度 | 端到端可运行，Mock/API 双模式，完整文档 |

## 技术栈

- Python 3.11+
- LLM: GLM-5.2 (api.llm.ustc.edu.cn) / OpenAI 兼容接口
- Agent: OpenAI SDK Function Calling + ReAct 模式
- Web: Flask + SSE (Server-Sent Events)
- 前端: 原生 JS，实时渲染 Agent 思维链
