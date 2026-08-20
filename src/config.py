"""
配置管理模块
"""

import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    api_base: str = os.getenv("LLM_API_BASE", "https://api.llm.ustc.edu.cn/v1")
    api_key: str = os.getenv("LLM_API_KEY", "")
    model: str = os.getenv("LLM_MODEL", "glm-5.2")
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class AppConfig:
    llm: LLMConfig = None
    output_dir: str = "output"

    def __post_init__(self):
        if self.llm is None:
            self.llm = LLMConfig()


config = AppConfig()
