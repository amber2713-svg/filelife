# WSGI 配置文件 - PythonAnywhere
import sys
import os

# 添加项目路径
project_home = '/home/你的用户名/filelife'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.chdir(project_home)

# 设置环境变量（在 PythonAnywhere Web 配置页面设置）
# LLM_API_BASE, LLM_API_KEY, LLM_MODEL

from app import app as application
