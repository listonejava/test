#!/usr/bin/env python3
"""
SpringBoot + Vue 全链路静态分析工具
=====================================
功能：
1. 前端 Vue 组件分析（功能请求、API 调用）
2. 后端 SpringBoot API 分析（Controller、Service、DAO）
3. 数据库映射分析（Entity、Mapper、SQL）
4. 生成全链路追踪报告（JSON/MD 格式）
5. 支持需求影响性分析和增量开发辅助

要求：Python 3.12+
"""

import os
import re
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path
from datetime import datetime


@dataclass
class DataSource:
    """数据源信息"""
    type: str  # mysql, postgres, oracle, etc.
    url: str
    username: str
    driver_class: str


@dataclass
class DatabaseTable:
    """数据库表结构"""
    table_name: str
    columns: list[dict] = field(default_factory=list)
    primary_key: Optional[str] = None
    indexes: list[str] = field(default_factory=list)


@dataclass
class Entity:
    """Java Entity 实体类"""
    class_name: str
    package: str
    file_path: str
    table_name: Optional[str] = None
    fields: list[dict] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)  # @OneToMany, @ManyToOne, etc.


@dataclass
class Mapper:
    """MyBatis Mapper / JPA Repository"""
    interface_name: str
    package: str
    file_path: str
    methods: list[dict] = field(default_factory=list)
    sql_statements: list[dict] = field(default_factory=list)
    associated_entity: Optional[str] = None


@dataclass
class Service:
    """Spring Service 层"""
    class_name: str
    package: str
    file_path: str
    is_interface: bool = False
    methods: list[dict] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # 依赖的 Mapper/Repository


@dataclass
class Controller:
    """Spring Controller 层"""
    class_name: str
    package: str
    file_path: str
    base_url: str
    endpoints: list[dict] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # 依赖的 Service


@dataclass
class FrontendFunction:
    """前端功能函数"""
    function_name: str
    component: str
    file_path: str
    api_calls: list[dict] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class VueComponent:
    """Vue 组件"""
    component_name: str
    file_path: str
    template_tags: list[str] = field(default_factory=list)
    functions: list[FrontendFunction] = field(default_factory=list)
    api_imports: list[str] = field(default_factory=list)
    props: list[dict] = field(default_factory=list)
    emits: list[str] = field(default_factory=list)


@dataclass
class FullChainLink:
    """全链路节点"""
    chain_id: str
    business_function: str
    frontend_component: Optional[str] = None
    frontend_file: Optional[str] = None
    frontend_function: Optional[str] = None
    api_method: Optional[str] = None
    api_url: Optional[str] = None
    controller_class: Optional[str] = None
    controller_file: Optional[str] = None
    service_class: Optional[str] = None
    service_file: Optional[str] = None
    service_method: Optional[str] = None
    mapper_class: Optional[str] = None
    mapper_file: Optional[str] = None
    mapper_method: Optional[str] = None
    entity_class: Optional[str] = None
    entity_file: Optional[str] = None
    table_name: Optional[str] = None
    sql_type: Optional[str] = None  # SELECT, INSERT, UPDATE, DELETE
    confidence: float = 0.0  # 链路置信度 0-1


@dataclass
class AnalysisResult:
    """分析结果"""
    project_name: str
    analysis_time: str
    backend_path: str
    frontend_path: str
    data_source: Optional[DataSource] = None
    controllers: list[Controller] = field(default_factory=list)
    services: list[Service] = field(default_factory=list)
    mappers: list[Mapper] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    tables: list[DatabaseTable] = field(default_factory=list)
    vue_components: list[VueComponent] = field(default_factory=list)
    full_chains: list[FullChainLink] = field(default_factory=list)
    statistics: dict = field(default_factory=dict)


class JavaAnalyzer:
    """Java 代码分析器"""
    
    # Spring MVC 注解匹配
    CONTROLLER_PATTERN = re.compile(r'@(?:Rest)?Controller\s*(?:\([^)]*\))?')
    REQUEST_MAPPING_PATTERN = re.compile(r'@(?:Get|Post|Put|Delete|Patch|Request)Mapping\s*(?:\([^)]*\))?')
    METHOD_MAP = {
        'GetMapping': 'GET',
        'PostMapping': 'POST',
        'PutMapping': 'PUT',
        'DeleteMapping': 'DELETE',
        'PatchMapping': 'PATCH',
        'RequestMapping': 'REQUEST'
    }
    
    # Service 层注解
    SERVICE_PATTERN = re.compile(r'@Service\s*(?:\([^)]*\))?')
    
    # Mapper/Repository 注解
    MAPPER_PATTERN = re.compile(r'@Mapper\s*(?:\([^)]*\))?')
    REPOSITORY_PATTERN = re.compile(r'@Repository\s*(?:\([^)]*\))?')
    
    # Entity 注解
    ENTITY_PATTERN = re.compile(r'@Entity\s*(?:\([^)]*\))?')
    TABLE_PATTERN = re.compile(r'@Table\s*\(\s*name\s*=\s*["\']([^"\']+)["\']\s*\)')
    
    # 依赖注入
    AUTOWIRED_PATTERN = re.compile(r'@Autowired\s+(?:private\s+)?(\w+)\s+(\w+);')
    
    # 方法签名
    METHOD_PATTERN = re.compile(
        r'(public|private|protected)?\s*(?:static)?\s*(?:final)?\s*'
        r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+\w+)?\s*\{'
    )
    
    def __init__(self, backend_path: str):
        self.backend_path = Path(backend_path)
        self.controllers: list[Controller] = []
        self.services: list[Service] = []
        self.mappers: list[Mapper] = []
        self.entities: list[Entity] = []
        
    def analyze(self):
        """执行完整分析"""
        if not self.backend_path.exists():
            print(f"警告：后端路径不存在：{self.backend_path}")
            return
            
        # 查找所有 Java 文件
        java_files = list(self.backend_path.rglob("*.java"))
        print(f"发现 {len(java_files)} 个 Java 文件")
        
        for java_file in java_files:
            self._analyze_java_file(java_file)
            
        # 解析 XML Mapper 文件
        xml_mappers = list(self.backend_path.rglob("*.xml"))
        for xml_file in xml_mappers:
            if 'mapper' in str(xml_file).lower() or 'mybatis' in str(xml_file).lower():
                self._parse_xml_mapper(xml_file)
                
    def _analyze_java_file(self, file_path: Path):
        """分析单个 Java 文件"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return
            
        # 提取包名
        package_match = re.search(r'package\s+([\w.]+);', content)
        package = package_match.group(1) if package_match else ""
        
        # 检查是否为 Controller
        if self.CONTROLLER_PATTERN.search(content):
            self._parse_controller(file_path, content, package)
            
        # 检查是否为 Service
        if self.SERVICE_PATTERN.search(content):
            self._parse_service(file_path, content, package)
            
        # 检查是否为 Mapper/Repository
        if self.MAPPER_PATTERN.search(content) or self.REPOSITORY_PATTERN.search(content):
            self._parse_mapper(file_path, content, package)
            
        # 检查是否为 Entity
        if self.ENTITY_PATTERN.search(content):
            self._parse_entity(file_path, content, package)
            
    def _parse_controller(self, file_path: Path, content: str, package: str):
        """解析 Controller 类"""
        class_match = re.search(r'(?:public\s+)?(?:abstract\s+)?(?:final\s+)?class\s+(\w+)', content)
        if not class_match:
            return
            
        class_name = class_match.group(1)
        
        # 提取基础路径 - 支持多种格式
        base_url = ""
        # 格式 1: @RequestMapping("/api/user")
        request_mapping = re.search(r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']', content)
        if not request_mapping:
            # 格式 2: @RequestMapping("/api/user")
            request_mapping = re.search(r'@RequestMapping\s*\(\s*value\s*=\s*["\']([^"\']+)["\']', content)
        if request_mapping:
            base_url = request_mapping.group(1)
            
        # 提取端点 - 改进正则表达式
        endpoints = []
        # 匹配各种格式：@GetMapping("/list"), @GetMapping(value="/list"), @GetMapping(path="/list")
        endpoint_patterns = [
            r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*\(\s*["\']([^"\']+)["\']',
            r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*\(\s*(?:value|path)\s*=\s*["\']([^"\']+)["\']',
            r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*\(\s*\)'  # 无路径的情况
        ]
        
        for pattern in endpoint_patterns:
            for match in re.finditer(pattern, content):
                groups = match.groups()
                method_type = groups[0] if groups[0] else 'Request'
                
                if len(groups) >= 2 and groups[1]:
                    path = groups[1]
                else:
                    path = ""
                    
                http_method = self.METHOD_MAP.get(f'{method_type}Mapping', 'GET')
                
                # 查找方法名
                method_context = content[match.end():match.end()+300]
                method_name_match = re.search(r'public\s+(?:\w+(?:<[^>]+>)?\s+)?(\w+)\s*\(', method_context)
                method_name = method_name_match.group(1) if method_name_match else "unknown"
                
                full_url = f"{base_url}{path}" if path else base_url
                if not full_url.startswith('/'):
                    full_url = f"/{full_url}"
                    
                endpoints.append({
                    'http_method': http_method,
                    'path': path,
                    'full_url': full_url,
                    'method_name': method_name
                })
            
        # 提取依赖
        dependencies = []
        for match in self.AUTOWIRED_PATTERN.finditer(content):
            dep_type = match.group(1)
            dep_name = match.group(2)
            dependencies.append(dep_type)
            
        controller = Controller(
            class_name=class_name,
            package=package,
            file_path=str(file_path),
            base_url=base_url,
            endpoints=endpoints,
            dependencies=list(set(dependencies))
        )
        self.controllers.append(controller)
        
    def _parse_service(self, file_path: Path, content: str, package: str):
        """解析 Service 类"""
        is_interface = 'interface' in content
        
        class_match = re.search(r'(?:public\s+)?(?:abstract\s+)?(?:final\s+)?(?:class|interface)\s+(\w+)', content)
        if not class_match:
            return
            
        class_name = class_match.group(1)
        
        # 提取方法
        methods = []
        for match in self.METHOD_PATTERN.finditer(content):
            modifier = match.group(1) or ''
            return_type = match.group(2)
            method_name = match.group(3)
            params = match.group(4)
            
            methods.append({
                'modifier': modifier,
                'return_type': return_type,
                'name': method_name,
                'params': params,
                'is_interface_method': is_interface or modifier == ''
            })
            
        # 提取依赖
        dependencies = []
        for match in self.AUTOWIRED_PATTERN.finditer(content):
            dep_type = match.group(1)
            dependencies.append(dep_type)
            
        service = Service(
            class_name=class_name,
            package=package,
            file_path=str(file_path),
            is_interface=is_interface,
            methods=methods,
            dependencies=list(set(dependencies))
        )
        self.services.append(service)
        
    def _parse_mapper(self, file_path: Path, content: str, package: str):
        """解析 Mapper/Repository"""
        class_match = re.search(r'(?:public\s+)?(?:abstract\s+)?(?:interface)\s+(\w+)', content)
        if not class_match:
            return
            
        interface_name = class_match.group(1)
        
        # 提取方法
        methods = []
        for match in re.finditer(r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\);', content):
            return_type = match.group(1)
            method_name = match.group(2)
            params = match.group(3)
            methods.append({
                'return_type': return_type,
                'name': method_name,
                'params': params
            })
            
        # 尝试关联 Entity
        associated_entity = None
        entity_match = re.search(r'<(\w+)>', interface_name)
        if entity_match:
            associated_entity = entity_match.group(1)
            
        mapper = Mapper(
            interface_name=interface_name,
            package=package,
            file_path=str(file_path),
            methods=methods,
            associated_entity=associated_entity
        )
        self.mappers.append(mapper)
        
    def _parse_entity(self, file_path: Path, content: str, package: str):
        """解析 Entity 类"""
        class_match = re.search(r'(?:public\s+)?(?:abstract\s+)?(?:final\s+)?class\s+(\w+)', content)
        if not class_match:
            return
            
        class_name = class_match.group(1)
        
        # 提取表名
        table_name = None
        table_match = self.TABLE_PATTERN.search(content)
        if table_match:
            table_name = table_match.group(1)
        else:
            # 默认驼峰转下划线
            table_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
            
        # 提取字段
        fields = []
        for match in re.finditer(
            r'@(?:Column|Id|GeneratedValue)[^(]*\([^)]*name\s*=\s*["\']([^"\']+)["\'][^)]*\)\s+'
            r'(?:private|protected|public)\s+(\w+(?:<[^>]+>)?)\s+(\w+);',
            content
        ):
            column_name = match.group(1)
            field_type = match.group(2)
            field_name = match.group(3)
            fields.append({
                'field_name': field_name,
                'field_type': field_type,
                'column_name': column_name
            })
            
        # 简单字段提取
        if not fields:
            for match in re.finditer(
                r'(?:private|protected|public)\s+(\w+(?:<[^>]+>)?)\s+(\w+);',
                content
            ):
                field_type = match.group(1)
                field_name = match.group(2)
                if field_name not in ['serialVersionUID']:
                    fields.append({
                        'field_name': field_name,
                        'field_type': field_type,
                        'column_name': re.sub(r'(?<!^)(?=[A-Z])', '_', field_name).lower()
                    })
                    
        entity = Entity(
            class_name=class_name,
            package=package,
            file_path=str(file_path),
            table_name=table_name,
            fields=fields
        )
        self.entities.append(entity)
        
    def _parse_xml_mapper(self, file_path: Path):
        """解析 MyBatis XML Mapper"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            return
            
        # 提取 namespace
        namespace_match = re.search(r'namespace\s*=\s*["\']([^"\']+)["\']', content)
        if not namespace_match:
            return
            
        namespace = namespace_match.group(1)
        
        # 查找对应的 Mapper 接口
        mapper = None
        for m in self.mappers:
            if f"{m.package}.{m.interface_name}" == namespace:
                mapper = m
                break
                
        if not mapper:
            return
            
        # 提取 SQL 语句
        sql_statements = []
        for sql_type in ['select', 'insert', 'update', 'delete']:
            pattern = rf'<{sql_type}[^>]*id\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</{sql_type}>'
            for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                statement_id = match.group(1)
                sql_content = match.group(2).strip()
                sql_statements.append({
                    'type': sql_type.upper(),
                    'id': statement_id,
                    'sql': sql_content[:200]  # 限制长度
                })
                
        mapper.sql_statements = sql_statements


class VueAnalyzer:
    """Vue 前端代码分析器"""
    
    # API 调用模式
    API_CALL_PATTERNS = [
        re.compile(r'(?:axios|http|request)\s*\.\s*(get|post|put|delete|patch)\s*\(\s*[`"\']([^`"\']+)["\']'),
        re.compile(r'axios\s*\.\s*(get|post|put|delete|patch)\s*\(\s*[`"\']([^`"\']+)["\']'),
        re.compile(r'(?:get|post|put|delete|patch)\s*\(\s*[`"\']([^`"\']+)["\']'),
    ]
    
    # 导入模式
    IMPORT_PATTERN = re.compile(r'import\s+.*?\s+from\s+["\']([^"\']+)["\']')
    
    def __init__(self, frontend_path: str):
        self.frontend_path = Path(frontend_path)
        self.components: list[VueComponent] = []
        
    def analyze(self):
        """执行完整分析"""
        if not self.frontend_path.exists():
            print(f"警告：前端路径不存在：{self.frontend_path}")
            return
            
        # 查找所有 Vue 文件
        vue_files = list(self.frontend_path.rglob("*.vue"))
        print(f"发现 {len(vue_files)} 个 Vue 文件")
        
        for vue_file in vue_files:
            self._analyze_vue_file(vue_file)
            
        # 也分析 TS/JS API 文件
        api_files = list(self.frontend_path.rglob("*.ts")) + list(self.frontend_path.rglob("*.js"))
        api_files = [f for f in api_files if 'api' in f.name.lower() or 'service' in f.name.lower()]
        for api_file in api_files[:50]:  # 限制数量
            self._analyze_api_file(api_file)
            
    def _analyze_vue_file(self, file_path: Path):
        """分析单个 Vue 文件"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return
            
        # 提取组件名
        component_name = file_path.stem
        
        # 提取模板标签
        template_tags = []
        template_match = re.search(r'<template[^>]*>(.*?)</template>', content, re.DOTALL)
        if template_match:
            template_content = template_match.group(1)
            template_tags = re.findall(r'<(\w+)', template_content)
            
        # 提取脚本内容
        script_match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        script_content = script_match.group(1) if script_match else ""
        
        # 提取导入
        api_imports = []
        imported_api_functions = {}
        for match in self.IMPORT_PATTERN.finditer(script_content):
            import_path = match.group(1)
            import_line = match.group(0)
            if 'api' in import_path.lower() or 'http' in import_path.lower() or 'request' in import_path.lower():
                api_imports.append(import_path)
                # 提取导入的函数名
                func_match = re.search(r'import\s*\{([^}]+)\}', import_line)
                if func_match:
                    funcs = [f.strip() for f in func_match.group(1).split(',')]
                    for func in funcs:
                        imported_api_functions[func] = import_path
                        
        # 提取函数 - 支持多种函数定义方式
        functions = []
        
        # 模式 1: const funcName = async () => {}
        func_pattern1 = re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>?\s*\{')
        # 模式 2: function funcName() {}
        func_pattern2 = re.compile(r'function\s+(\w+)\s*\([^)]*\)\s*\{')
        
        for pattern in [func_pattern1, func_pattern2]:
            for match in pattern.finditer(script_content):
                func_name = match.group(1)
                
                # 查找 API 调用
                api_calls = []
                func_end = script_content.find('}', match.end())
                if func_end == -1:
                    func_end = len(script_content)
                func_body = script_content[match.end():func_end]
                
                # 直接 axios 调用
                for pattern in self.API_CALL_PATTERNS:
                    for api_match in pattern.finditer(func_body):
                        groups = api_match.groups()
                        if len(groups) >= 2:
                            method = groups[0].upper() if groups[0] else 'GET'
                            url = groups[1]
                        else:
                            method = 'GET'
                            url = groups[0]
                        api_calls.append({
                            'method': method,
                            'url': url
                        })
                
                # 间接 API 函数调用（通过导入的 API 模块）
                for api_func_name, api_path in imported_api_functions.items():
                    if api_func_name in func_body:
                        # 从 API 路径推断 URL
                        # e.g., '../api/userApi' -> /api/user
                        base_url = re.sub(r'.*/api/(\w+)Api.*', r'/api/\1', api_path)
                        if base_url != api_path:
                            # 根据函数名推断具体端点
                            if 'list' in api_func_name.lower() or 'all' in api_func_name.lower():
                                api_calls.append({'method': 'GET', 'url': f'{base_url}/list'})
                            elif 'byid' in api_func_name.lower() or 'by_id' in api_func_name.lower():
                                api_calls.append({'method': 'GET', 'url': f'{base_url}/{{id}}'})
                            elif 'delete' in api_func_name.lower():
                                api_calls.append({'method': 'DELETE', 'url': f'{base_url}/{{id}}'})
                            elif 'create' in api_func_name.lower() or 'add' in api_func_name.lower():
                                api_calls.append({'method': 'POST', 'url': f'{base_url}'})
                            elif 'update' in api_func_name.lower():
                                api_calls.append({'method': 'PUT', 'url': f'{base_url}/{{id}}'})
                            elif 'get' in api_func_name.lower():
                                api_calls.append({'method': 'GET', 'url': f'{base_url}'})
                        
                if api_calls:
                    functions.append(FrontendFunction(
                        function_name=func_name,
                        component=component_name,
                        file_path=str(file_path),
                        api_calls=api_calls
                    ))
                
        # 提取 Props
        props = []
        props_match = re.search(r'props:\s*\{([^}]+)\}', script_content, re.DOTALL)
        if props_match:
            props_content = props_match.group(1)
            for prop_match in re.finditer(r'(\w+):\s*(\w+)', props_content):
                props.append({
                    'name': prop_match.group(1),
                    'type': prop_match.group(2)
                })
                
        # 提取 Emits
        emits = []
        emits_match = re.search(r'emits:\s*\[([^\]]+)\]', script_content)
        if emits_match:
            emits_content = emits_match.group(1)
            emits = re.findall(r'["\'](\w+)["\']', emits_content)
            
        component = VueComponent(
            component_name=component_name,
            file_path=str(file_path),
            template_tags=list(set(template_tags)),
            functions=functions,
            api_imports=list(set(api_imports)),
            props=props,
            emits=emits
        )
        self.components.append(component)
        
    def _analyze_api_file(self, file_path: Path):
        """分析 API 定义文件"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            return
            
        # 类似 Vue 文件的分析方法
        # ... (简化处理)


class ConfigAnalyzer:
    """配置文件分析器"""
    
    def __init__(self, backend_path: str):
        self.backend_path = Path(backend_path)
        self.data_source: Optional[DataSource] = None
        self.properties: dict = {}
        
    def analyze(self):
        """分析配置文件"""
        # 查找 application.properties 或 application.yml
        prop_files = list(self.backend_path.rglob("application.properties"))
        yml_files = list(self.backend_path.rglob("application.yml")) + \
                   list(self.backend_path.rglob("application.yaml"))
                   
        for prop_file in prop_files:
            self._parse_properties(prop_file)
            
        for yml_file in yml_files:
            self._parse_yaml(yml_file)
            
    def _parse_properties(self, file_path: Path):
        """解析 properties 文件"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return
            
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                self.properties[key.strip()] = value.strip()
                
        # 提取数据源配置
        self._extract_datasource_from_props()
        
    def _parse_yaml(self, file_path: Path):
        """解析 YAML 文件（简单解析）"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return
            
        # 简单键值对提取
        for line in content.split('\n'):
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    self.properties[key] = value
                    
        self._extract_datasource_from_props()
        
    def _extract_datasource_from_props(self):
        """从属性中提取数据源信息"""
        url = self.properties.get('spring.datasource.url', '')
        username = self.properties.get('spring.datasource.username', '')
        driver = self.properties.get('spring.datasource.driver-class-name', '')
        
        if url:
            db_type = 'unknown'
            if 'mysql' in url.lower():
                db_type = 'mysql'
            elif 'postgres' in url.lower():
                db_type = 'postgresql'
            elif 'oracle' in url.lower():
                db_type = 'oracle'
            elif 'sqlserver' in url.lower():
                db_type = 'sqlserver'
                
            self.data_source = DataSource(
                type=db_type,
                url=url,
                username=username,
                driver_class=driver
            )


class FullChainBuilder:
    """全链路构建器"""
    
    def __init__(self, java_analyzer: JavaAnalyzer, vue_analyzer: VueAnalyzer):
        self.java_analyzer = java_analyzer
        self.vue_analyzer = vue_analyzer
        self.chains: list[FullChainLink] = []
        
    def build_chains(self):
        """构建全链路"""
        chain_id = 0
        
        # 从前端开始追踪
        for component in self.vue_analyzer.components:
            for func in component.functions:
                for api_call in func.api_calls:
                    chain = self._trace_backend(api_call, component, func)
                    if chain:
                        chain_id += 1
                        chain.chain_id = f"CHAIN_{chain_id:04d}"
                        
                        # 计算置信度
                        chain.confidence = self._calculate_confidence(chain)
                        self.chains.append(chain)
                        
        # 也从后端开始追踪（覆盖未在前端调用的 API）
        for controller in self.java_analyzer.controllers:
            for endpoint in controller.endpoints:
                # 检查是否已有此链路
                exists = any(
                    c.api_url == endpoint['full_url'] 
                    for c in self.chains
                )
                if not exists:
                    chain = self._trace_from_controller(controller, endpoint)
                    if chain:
                        chain_id += 1
                        chain.chain_id = f"CHAIN_{chain_id:04d}"
                        chain.business_function = f"Backend API: {endpoint['http_method']} {endpoint['full_url']}"
                        chain.confidence = 0.5  # 仅后端，置信度较低
                        self.chains.append(chain)
                        
    def _trace_backend(self, api_call: dict, component: VueComponent, func: FrontendFunction) -> Optional[FullChainLink]:
        """从前端 API 调用追踪到后端"""
        chain = FullChainLink(
            chain_id="",
            business_function=f"{component.component_name}.{func.function_name}",
            frontend_component=component.component_name,
            frontend_file=component.file_path,
            frontend_function=func.function_name,
            api_method=api_call['method'],
            api_url=api_call['url']
        )
        
        # 查找匹配的 Controller
        matched_controller = None
        matched_endpoint = None
        
        for controller in self.java_analyzer.controllers:
            for endpoint in controller.endpoints:
                # 简单路径匹配
                if self._url_matches(api_call['url'], endpoint['full_url']):
                    matched_controller = controller
                    matched_endpoint = endpoint
                    break
            if matched_controller:
                break
                
        if matched_controller:
            chain.controller_class = matched_controller.class_name
            chain.controller_file = matched_controller.file_path
            chain.api_url = matched_endpoint['full_url']
            chain.api_method = matched_endpoint['http_method']
            
            # 查找 Service
            for service in self.java_analyzer.services:
                for dep in matched_controller.dependencies:
                    if dep in service.class_name:
                        chain.service_class = service.class_name
                        chain.service_file = service.file_path
                        
                        # 查找 Mapper
                        for mapper in self.java_analyzer.mappers:
                            for svc_dep in service.dependencies:
                                if svc_dep in mapper.interface_name:
                                    chain.mapper_class = mapper.interface_name
                                    chain.mapper_file = mapper.file_path
                                    
                                    # 查找 Entity
                                    for entity in self.java_analyzer.entities:
                                        if mapper.associated_entity == entity.class_name:
                                            chain.entity_class = entity.class_name
                                            chain.entity_file = entity.file_path
                                            chain.table_name = entity.table_name
                                            
        return chain
        
    def _trace_from_controller(self, controller: Controller, endpoint: dict) -> Optional[FullChainLink]:
        """从 Controller 开始追踪"""
        chain = FullChainLink(
            chain_id="",
            business_function=f"API: {endpoint['http_method']} {endpoint['full_url']}",
            api_method=endpoint['http_method'],
            api_url=endpoint['full_url'],
            controller_class=controller.class_name,
            controller_file=controller.file_path
        )
        
        # 查找 Service
        for service in self.java_analyzer.services:
            for dep in controller.dependencies:
                if dep in service.class_name:
                    chain.service_class = service.class_name
                    chain.service_file = service.file_path
                    break
                    
        # 查找 Mapper
        if chain.service_class:
            for service in self.java_analyzer.services:
                if service.class_name == chain.service_class:
                    for dep in service.dependencies:
                        for mapper in self.java_analyzer.mappers:
                            if dep in mapper.interface_name:
                                chain.mapper_class = mapper.interface_name
                                chain.mapper_file = mapper.file_path
                                
        return chain
        
    def _url_matches(self, frontend_url: str, backend_url: str) -> bool:
        """检查 URL 是否匹配"""
        # 清理参数
        frontend_url = frontend_url.split('?')[0]
        backend_url = backend_url.split('?')[0]
        
        # 处理路径变量
        frontend_clean = re.sub(r'\$\{?\w+\}?', '{var}', frontend_url)
        backend_clean = re.sub(r'\{[^}]+\}', '{var}', backend_url)
        
        return frontend_clean == backend_clean or frontend_url in backend_url or backend_url in frontend_url
        
    def _calculate_confidence(self, chain: FullChainLink) -> float:
        """计算链路置信度"""
        score = 0.0
        max_score = 6.0
        
        if chain.frontend_component:
            score += 1.0
        if chain.controller_class:
            score += 1.0
        if chain.service_class:
            score += 1.0
        if chain.mapper_class:
            score += 1.0
        if chain.entity_class:
            score += 1.0
        if chain.table_name:
            score += 1.0
            
        return score / max_score


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, result: AnalysisResult):
        self.result = result
        
    def generate_json(self, output_path: str):
        """生成 JSON 报告"""
        data = asdict(self.result)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"JSON 报告已生成：{output_path}")
        
    def generate_markdown(self, output_path: str):
        """生成 Markdown 报告"""
        md_lines = []
        
        # 标题
        md_lines.append(f"# {self.result.project_name} - 全链路分析报告")
        md_lines.append("")
        md_lines.append(f"**分析时间**: {self.result.analysis_time}")
        md_lines.append(f"**后端路径**: {self.result.backend_path}")
        md_lines.append(f"**前端路径**: {self.result.frontend_path}")
        md_lines.append("")
        
        # 统计信息
        md_lines.append("## 📊 统计概览")
        md_lines.append("")
        stats = self.result.statistics
        for key, value in stats.items():
            md_lines.append(f"- **{key}**: {value}")
        md_lines.append("")
        
        # 数据源
        if self.result.data_source:
            md_lines.append("## 💾 数据源配置")
            md_lines.append("")
            md_lines.append(f"- **类型**: {self.result.data_source.type}")
            md_lines.append(f"- **URL**: {self.result.data_source.url}")
            md_lines.append(f"- **用户名**: {self.result.data_source.username}")
            md_lines.append("")
            
        # 全链路追踪
        md_lines.append("## 🔗 全链路追踪")
        md_lines.append("")
        
        if self.result.full_chains:
            for chain in self.result.full_chains[:50]:  # 限制显示数量
                md_lines.append(f"### {chain.chain_id}")
                md_lines.append("")
                md_lines.append(f"**业务功能**: {chain.business_function}")
                md_lines.append(f"**置信度**: {chain.confidence:.1%}")
                md_lines.append("")
                
                if chain.frontend_component:
                    md_lines.append(f"- 🖥️ **前端组件**: `{chain.frontend_component}`")
                    md_lines.append(f"  - 文件：`{chain.frontend_file}`")
                    md_lines.append(f"  - 函数：`{chain.frontend_function}`")
                    
                if chain.api_url:
                    md_lines.append(f"- 🌐 **API**: `{chain.api_method} {chain.api_url}`")
                    
                if chain.controller_class:
                    md_lines.append(f"- 🎮 **Controller**: `{chain.controller_class}`")
                    md_lines.append(f"  - 文件：`{chain.controller_file}`")
                    
                if chain.service_class:
                    md_lines.append(f"- ⚙️ **Service**: `{chain.service_class}`")
                    md_lines.append(f"  - 文件：`{chain.service_file}`")
                    
                if chain.mapper_class:
                    md_lines.append(f"- 🗂️ **Mapper**: `{chain.mapper_class}`")
                    md_lines.append(f"  - 文件：`{chain.mapper_file}`")
                    
                if chain.entity_class:
                    md_lines.append(f"- 📦 **Entity**: `{chain.entity_class}`")
                    md_lines.append(f"  - 文件：`{chain.entity_file}`")
                    
                if chain.table_name:
                    md_lines.append(f"- 🗄️ **数据表**: `{chain.table_name}`")
                    
                md_lines.append("")
        else:
            md_lines.append("*未找到完整链路*")
            md_lines.append("")
            
        # Controllers
        md_lines.append("## 🎮 Controllers")
        md_lines.append("")
        for ctrl in self.result.controllers[:20]:
            md_lines.append(f"### {ctrl.class_name}")
            md_lines.append(f"- **包**: {ctrl.package}")
            md_lines.append(f"- **基础路径**: {ctrl.base_url}")
            md_lines.append(f"- **端点**: {len(ctrl.endpoints)}")
            for ep in ctrl.endpoints:
                md_lines.append(f"  - `{ep['http_method']} {ep['full_url']}`")
            md_lines.append("")
            
        # Services
        md_lines.append("## ⚙️ Services")
        md_lines.append("")
        for svc in self.result.services[:20]:
            md_lines.append(f"### {svc.class_name}")
            md_lines.append(f"- **包**: {svc.package}")
            md_lines.append(f"- **接口**: {'是' if svc.is_interface else '否'}")
            md_lines.append(f"- **方法数**: {len(svc.methods)}")
            md_lines.append("")
            
        # Entities & Tables
        md_lines.append("## 📦 Entities & Tables")
        md_lines.append("")
        for entity in self.result.entities[:20]:
            md_lines.append(f"### {entity.class_name}")
            md_lines.append(f"- **表名**: {entity.table_name}")
            md_lines.append(f"- **字段数**: {len(entity.fields)}")
            if entity.fields:
                md_lines.append("| 字段名 | 类型 | 列名 |")
                md_lines.append("|--------|------|------|")
                for fld in entity.fields[:10]:
                    md_lines.append(f"| {fld['field_name']} | {fld['field_type']} | {fld['column_name']} |")
            md_lines.append("")
            
        # Vue Components
        md_lines.append("## 🖥️ Vue Components")
        md_lines.append("")
        for comp in self.result.vue_components[:20]:
            md_lines.append(f"### {comp.component_name}")
            md_lines.append(f"- **文件**: {comp.file_path}")
            md_lines.append(f"- **API 调用数**: {sum(len(f.api_calls) for f in comp.functions)}")
            if comp.functions:
                md_lines.append("**函数列表**:")
                for func in comp.functions[:5]:
                    md_lines.append(f"- `{func.function_name}` ({len(func.api_calls)} API calls)")
            md_lines.append("")
            
        # 影响性分析指南
        md_lines.append("## 🔍 需求影响性分析指南")
        md_lines.append("")
        md_lines.append("### 如何进行影响性分析")
        md_lines.append("")
        md_lines.append("1. **前端变更影响**")
        md_lines.append("   - 修改某个 Vue 组件时，查看其调用的 API")
        md_lines.append("   - 根据 `CHAIN_XXXX` 找到对应的后端服务")
        md_lines.append("")
        md_lines.append("2. **后端变更影响**")
        md_lines.append("   - 修改某个 Service 时，查看哪些 Controller 依赖它")
        md_lines.append("   - 根据 `CHAIN_XXXX` 找到对应的前端组件")
        md_lines.append("")
        md_lines.append("3. **数据库变更影响**")
        md_lines.append("   - 修改某个表结构时，查看对应的 Entity")
        md_lines.append("   - 根据 `CHAIN_XXXX` 找到使用此 Entity 的所有链路")
        md_lines.append("")
        md_lines.append("4. **增量开发辅助**")
        md_lines.append("   - 新增功能时，参考现有相似功能的 `CHAIN_XXXX` 模式")
        md_lines.append("   - 确保新功能的链路完整性（前端→API→Controller→Service→Mapper→Entity→Table）")
        md_lines.append("")
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
            
        print(f"Markdown 报告已生成：{output_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='SpringBoot + Vue 全链路静态分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python fullchain_analyzer.py --backend /path/to/springboot --frontend /path/to/vue
  python fullchain_analyzer.py -b ../backend -f ../frontend -o ./analysis_result
  python fullchain_analyzer.py --backend ./demo-backend --frontend ./demo-frontend --format both
        """
    )
    
    parser.add_argument('-b', '--backend', required=True, help='SpringBoot 后端项目路径')
    parser.add_argument('-f', '--frontend', required=True, help='Vue 前端项目路径')
    parser.add_argument('-o', '--output', default='./analysis_output', help='输出目录（默认：./analysis_output）')
    parser.add_argument('--format', choices=['json', 'md', 'both'], default='both', help='输出格式（默认：both）')
    parser.add_argument('--project-name', default='Unknown Project', help='项目名称')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SpringBoot + Vue 全链路静态分析工具")
    print("=" * 60)
    print(f"后端路径：{args.backend}")
    print(f"前端路径：{args.frontend}")
    print(f"输出目录：{args.output}")
    print(f"输出格式：{args.format}")
    print("")
    
    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化分析结果
    result = AnalysisResult(
        project_name=args.project_name,
        analysis_time=datetime.now().isoformat(),
        backend_path=args.backend,
        frontend_path=args.frontend
    )
    
    # 后端分析
    print("🔍 分析后端代码...")
    java_analyzer = JavaAnalyzer(args.backend)
    java_analyzer.analyze()
    
    result.controllers = java_analyzer.controllers
    result.services = java_analyzer.services
    result.mappers = java_analyzer.mappers
    result.entities = java_analyzer.entities
    
    print(f"  ✓ 发现 {len(result.controllers)} 个 Controllers")
    print(f"  ✓ 发现 {len(result.services)} 个 Services")
    print(f"  ✓ 发现 {len(result.mappers)} 个 Mappers")
    print(f"  ✓ 发现 {len(result.entities)} 个 Entities")
    print("")
    
    # 配置文件分析
    print("🔍 分析配置文件...")
    config_analyzer = ConfigAnalyzer(args.backend)
    config_analyzer.analyze()
    result.data_source = config_analyzer.data_source
    
    if result.data_source:
        print(f"  ✓ 数据源类型：{result.data_source.type}")
        print(f"  ✓ 数据源 URL: {result.data_source.url}")
    print("")
    
    # 前端分析
    print("🔍 分析前端代码...")
    vue_analyzer = VueAnalyzer(args.frontend)
    vue_analyzer.analyze()
    
    result.vue_components = vue_analyzer.components
    print(f"  ✓ 发现 {len(result.vue_components)} 个 Vue 组件")
    print("")
    
    # 构建全链路
    print("🔗 构建全链路...")
    chain_builder = FullChainBuilder(java_analyzer, vue_analyzer)
    chain_builder.build_chains()
    
    result.full_chains = chain_builder.chains
    print(f"  ✓ 构建 {len(result.full_chains)} 条完整链路")
    print("")
    
    # 统计信息
    result.statistics = {
        'controllers_count': len(result.controllers),
        'services_count': len(result.services),
        'mappers_count': len(result.mappers),
        'entities_count': len(result.entities),
        'vue_components_count': len(result.vue_components),
        'full_chains_count': len(result.full_chains),
        'high_confidence_chains': sum(1 for c in result.full_chains if c.confidence >= 0.8),
        'medium_confidence_chains': sum(1 for c in result.full_chains if 0.5 <= c.confidence < 0.8),
        'low_confidence_chains': sum(1 for c in result.full_chains if c.confidence < 0.5)
    }
    
    # 生成报告
    print("📝 生成报告...")
    report_generator = ReportGenerator(result)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if args.format in ['json', 'both']:
        json_path = output_dir / f"fullchain_analysis_{timestamp}.json"
        report_generator.generate_json(str(json_path))
        
    if args.format in ['md', 'both']:
        md_path = output_dir / f"fullchain_analysis_{timestamp}.md"
        report_generator.generate_markdown(str(md_path))
        
    print("")
    print("=" * 60)
    print("✅ 分析完成!")
    print("=" * 60)
    print(f"输出目录：{output_dir.absolute()}")
    print("")
    print("📊 统计摘要:")
    for key, value in result.statistics.items():
        print(f"  - {key}: {value}")
    print("")


if __name__ == '__main__':
    main()
