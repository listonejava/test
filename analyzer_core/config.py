# -*- coding: utf-8 -*-
"""
SpringBoot + Vue 全链路静态分析工具 - 配置模块
"""

# 日志配置
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# 匹配阈值
MATCH_THRESHOLD_EXACT = 100      # 精确匹配
MATCH_THRESHOLD_CONTAINS = 80    # 包含匹配
MATCH_THRESHOLD_MODULE = 30      # 模块名匹配
MIN_CONFIDENCE = 30              # 最低置信度

# API 前缀过滤列表
API_PREFIXES_TO_STRIP = ['dev-api', 'prod-api', 'api']

# 服务命名规范
SERVICE_INTERFACE_PREFIXES = ['I']
SERVICE_IMPL_SUFFIXES = ['Impl', 'Service']

# 文件过滤
EXCLUDE_DIRS = ['node_modules', '.git', 'target', 'dist', '.idea', '.vscode']
JAVA_FILE_EXT = '.java'
VUE_FILE_EXT = '.vue'
JS_FILE_EXT = '.js'
XML_FILE_EXT = '.xml'

# 输出配置
DEFAULT_PROJECT_NAME = "ShuBiProject"
DEFAULT_OUTPUT_DIR = "./analysis_output"
OUTPUT_DATE_FORMAT = '%Y%m%d_%H%M%S'
