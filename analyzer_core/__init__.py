# -*- coding: utf-8 -*-
"""
SpringBoot + Vue 全链路静态分析工具核心模块
"""
from .config import *
from .models import *
from .parsers import ApiModuleParser, VueParser, JavaParser, XmlMapperParser
from .matchers import ServiceMatcher, PathMatcher
from .chain_builder import ChainBuilder
from .exporter import JsonExporter

__version__ = "3.6.0"
__all__ = [
    # 配置
    'LOG_FORMAT', 'LOG_LEVEL',
    'MATCH_THRESHOLD_EXACT', 'MATCH_THRESHOLD_CONTAINS', 'MATCH_THRESHOLD_MODULE', 'MIN_CONFIDENCE',
    'API_PREFIXES_TO_STRIP',
    'SERVICE_INTERFACE_PREFIXES', 'SERVICE_IMPL_SUFFIXES',
    'EXCLUDE_DIRS', 'JAVA_FILE_EXT', 'VUE_FILE_EXT', 'JS_FILE_EXT', 'XML_FILE_EXT',
    'DEFAULT_PROJECT_NAME', 'DEFAULT_OUTPUT_DIR', 'OUTPUT_DATE_FORMAT',
    
    # 数据模型
    'ApiFunction', 'VueApiRequest', 'MethodInfo', 'BackEndAPI', 
    'ServiceInfo', 'StorageAccess', 'BusinessChain',
    
    # 解析器
    'ApiModuleParser', 'VueParser', 'JavaParser', 'XmlMapperParser',
    
    # 匹配器
    'ServiceMatcher', 'PathMatcher',
    
    # 构建器和导出器
    'ChainBuilder', 'JsonExporter',
]
