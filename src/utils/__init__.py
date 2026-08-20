"""
工具函数
"""

import json
import logging
import os
from datetime import datetime


def setup_logging(level: str = "INFO"):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def ensure_dir(path: str):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def save_markdown(content: str, filename: str, output_dir: str = "output"):
    """保存Markdown文件"""
    ensure_dir(output_dir)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def save_json(data: dict, filename: str, output_dir: str = "output"):
    """保存JSON文件"""
    ensure_dir(output_dir)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


def timestamp() -> str:
    """当前时间戳字符串"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
