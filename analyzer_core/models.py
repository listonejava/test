# -*- coding: utf-8 -*-
"""
数据模型定义模块
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class ApiFunction:
    """API 函数定义"""
    name: str
    url: str                 # 纯净的 API 路径
    method: str
    file_path: str           # 绝对路径
    module_name: str
    description: str
    full_url: str = ""       # 带前缀的完整路径 (用于内部匹配)


@dataclass
class VueApiRequest:
    """前端 API 请求信息"""
    component_file: str      # 绝对路径
    component_name: str
    function_name: str
    request_path: str        # 输出用：纯净路径
    method: str
    protocol: str = "https"
    parameters: List[str] = field(default_factory=list)
    api_file: str = ""       # 绝对路径
    raw_path: str = ""       # 匹配用：可能带前缀


@dataclass
class MethodInfo:
    """后端方法信息"""
    name: str
    signature: str
    description: str
    annotations: List[str] = field(default_factory=list)


@dataclass
class BackEndAPI:
    """后端 API 信息"""
    controller_file: str     # 绝对路径
    controller_class: str
    method: MethodInfo
    dependencies: List[str] = field(default_factory=list)
    base_mapping: str = ""
    full_path: str = ""


@dataclass
class ServiceInfo:
    """服务层信息"""
    service_file: str        # 绝对路径
    service_class: str
    methods: List[str]
    dependencies: List[str] = field(default_factory=list)


@dataclass
class StorageAccess:
    """数据存储层信息"""
    repository_file: str     # 绝对路径
    repository_class: str
    database_table: str
    operations: List[str] = field(default_factory=list)
    xml_file: str = ""       # 绝对路径


@dataclass
class BusinessChain:
    """业务全链路"""
    business_function: str
    front_end_request: Dict[str, Any]
    back_end_api: Dict[str, Any]
    services: List[Dict[str, Any]]
    storage_access: List[Dict[str, Any]]
    code_paths: List[str]
    confidence: float = 0.0
