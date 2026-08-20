---
title: 保研Agent - ReAct + Function Calling
emoji: 🎓
colorFrom: blue
colorTo: purple
sdk: gradio
python_version: 3.12
app_file: app_gradio.py
pinned: false
---

# 🎓 保研Agent

基于 **ReAct + Function Calling** 的自主保研规划智能体。

## 功能说明

- Agent 自主决定调用什么工具、搜索什么信息
- 实时展示思维链：思考 → 工具调用 → 观察结果
- 最终生成完整的个性化保研攻略

## 使用方式

1. 在输入框描述你的背景（学校、专业、绩点、科研、目标院校）
2. 点击"发送"或按 Enter
3. 右侧实时显示 Agent 推理过程
4. 或直接点击"🎯 一键演示"体验完整流程

## 技术栈

- Python 3.12 + Gradio
- OpenAI SDK (Function Calling)
- 中科大 LLM API (GLM-5.2)
