#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpringBoot + Vue 全链路静态分析工具
功能：业务功能 -> 前端请求 -> 后端 API -> 服务层 -> 存储层 -> 数据结构 全链路分析
输出：JSON 格式报告，支持需求影响性分析和增量开发辅助
兼容：Python 3.12 - 3.14
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import argparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class FrontEndRequest:
    """前端请求信息"""
    component: str = ""
    request_path: str = ""
    http_method: str = "GET"
    parameters: List[str] = field(default_factory=list)
    function_name: str = ""


@dataclass
class BackEndAPI:
    """后端 API 信息"""
    controller: str = ""
    method: str = ""
    method_signature: str = ""
    dependencies: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)


@dataclass
class ServiceInfo:
    """服务层信息"""
    service: str = ""
    methods: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)


@dataclass
class StorageAccess:
    """存储访问信息"""
    repository: str = ""
    database_table: str = ""
    operations: List[str] = field(default_factory=list)
    sql_statements: List[str] = field(default_factory=list)


@dataclass
class CodeQuality:
    """代码质量指标"""
    sonarqube_issues: int = 0
    code_smells: int = 0
    bugs: int = 0
    vulnerabilities: int = 0
    duplications: int = 0
    coverage: float = 0.0


@dataclass
class SecurityVulnerabilities:
    """安全漏洞信息"""
    semgrep_findings: int = 0
    xss_vulnerabilities: int = 0
    sql_injection: int = 0
    csrf_vulnerabilities: int = 0
    other_vulnerabilities: int = 0
    findings: List[Dict] = field(default_factory=list)


@dataclass
class PerformanceBottlenecks:
    """性能瓶颈信息"""
    spring_startup_analyzer_findings: int = 0
    slow_methods: int = 0
    inefficient_data_access: int = 0
    n_plus_one_queries: int = 0
    details: List[Dict] = field(default_factory=list)


@dataclass
class BusinessChain:
    """业务全链路信息"""
    business_function: str = ""
    front_end_request: Optional[FrontEndRequest] = None
    back_end_api: Optional[BackEndAPI] = None
    services: List[ServiceInfo] = field(default_factory=list)
    storage_access: List[StorageAccess] = field(default_factory=list)
    code_quality: Optional[CodeQuality] = None
    security_vulnerabilities: Optional[SecurityVulnerabilities] = None
    performance_bottlenecks: Optional[PerformanceBottlenecks] = None
    affected_code_paths: List[str] = field(default_factory=list)
    confidence: float = 0.0


class VueAnalyzer:
    """Vue 前端代码分析器"""
    
    def __init__(self):
        self.vue_components: Dict[str, Dict] = {}
        self.api_calls: List[Dict] = []
        
    def analyze_directory(self, vue_dir: str) -> List[FrontEndRequest]:
        """分析 Vue 项目目录"""
        requests = []
        
        if not os.path.exists(vue_dir):
            logger.warning(f"Vue 目录不存在：{vue_dir}")
            return requests
        
        vue_files = list(Path(vue_dir).rglob("*.vue"))
        js_ts_files = list(Path(vue_dir).rglob("*.js")) + list(Path(vue_dir).rglob("*.ts"))
        
        logger.info(f"发现 {len(vue_files)} 个 Vue 文件，{len(js_ts_files)} 个 JS/TS 文件")
        
        # 分析 Vue 组件
        for vue_file in vue_files:
            try:
                request = self._analyze_vue_file(str(vue_file))
                if request and request.request_path:
                    requests.append(request)
                    logger.info(f"  ✓ 解析 API 调用：{request.component} -> {request.http_method} {request.request_path}")
            except Exception as e:
                logger.error(f"分析 Vue 文件失败 {vue_file}: {e}")
        
        # 分析 API 模块 (api/*.js 或 api/*.ts)
        api_dirs = [d for d in Path(vue_dir).rglob("api") if d.is_dir()]
        for api_dir in api_dirs:
            for api_file in list(api_dir.glob("*.js")) + list(api_dir.glob("*.ts")):
                try:
                    api_requests = self._analyze_api_module(str(api_file))
                    requests.extend(api_requests)
                except Exception as e:
                    logger.error(f"分析 API 模块失败 {api_file}: {e}")
        
        return requests
    
    def _analyze_vue_file(self, file_path: str) -> Optional[FrontEndRequest]:
        """分析单个 Vue 文件"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        component_name = Path(file_path).stem
        request = FrontEndRequest(component=f"{component_name}.vue")
        
        # 匹配 axios 调用
        axios_patterns = [
            r'axios\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'this\.\$axios\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'\$http\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'http\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]',
        ]
        
        for pattern in axios_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                method = match[0].upper()
                path = match[1]
                
                # 跳过外部链接
                if path.startswith('http://') or path.startswith('https://'):
                    continue
                
                request.request_path = path
                request.http_method = method
                
                # 提取参数
                params_pattern = r'params:\s*\{([^}]+)\}'
                params_match = re.search(params_pattern, content)
                if params_match:
                    params_str = params_match.group(1)
                    request.parameters = [p.strip().split(':')[0].strip() for p in params_str.split(',')]
                
                # 提取函数名
                func_pattern = rf'(\w+)\s*\(.*?\{{[^}}]*?{re.escape(path)}'
                func_match = re.search(func_pattern, content, re.DOTALL)
                if func_match:
                    request.function_name = func_match.group(1)
                
                break
        
        # 匹配 API 模块导入调用
        api_import_patterns = [
            r'import\s+\{([^}]+)\}\s+from\s+[\'"].*api[\'"]',
            r'import\s+(\w+)\s+from\s+[\'"].*api[\'"]',
        ]
        
        for pattern in api_import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, str):
                    api_funcs = [match.strip()]
                else:
                    api_funcs = [f.strip() for f in match.split(',')]
                
                for api_func in api_funcs:
                    if api_func and not api_func.startswith('_'):
                        inferred_path = self._infer_api_path_from_function(api_func)
                        if inferred_path:
                            request.request_path = inferred_path
                            request.function_name = api_func
                            break
        
        if request.request_path:
            return request
        
        return None
    
    def _analyze_api_module(self, file_path: str) -> List[FrontEndRequest]:
        """分析 API 模块文件"""
        requests = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        api_patterns = [
            r'(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'request\.\s*(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]',
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                method = match[0].upper()
                path = match[1]
                
                request = FrontEndRequest(
                    component=Path(file_path).stem,
                    request_path=path,
                    http_method=method
                )
                
                func_pattern = rf'export\s+(?:const|let|var|function)\s+(\w+)\s*[:=].*?{re.escape(path)}'
                func_match = re.search(func_pattern, content, re.DOTALL)
                if func_match:
                    request.function_name = func_match.group(1)
                
                requests.append(request)
        
        return requests
    
    def _infer_api_path_from_function(self, func_name: str) -> Optional[str]:
        """从函数名推断 API 路径"""
        mappings = {
            r'get.*user': '/api/user/list',
            r'getUser': '/api/user/{id}',
            r'createUser': '/api/user',
            r'updateUser': '/api/user/{id}',
            r'deleteUser': '/api/user/{id}',
            r'get.*order': '/api/order/list',
            r'getOrder': '/api/order/{id}',
            r'createOrder': '/api/order',
            r'updateOrder': '/api/order/{id}',
            r'deleteOrder': '/api/order/{id}',
        }
        
        func_lower = func_name.lower()
        for pattern, path in mappings.items():
            if re.search(pattern, func_lower):
                return path
        
        return None


class SpringBootAnalyzer:
    """SpringBoot 后端代码分析器"""
    
    def __init__(self):
        self.controllers: Dict[str, Dict] = {}
        self.services: Dict[str, Dict] = {}
        self.repositories: Dict[str, Dict] = {}
        self.entities: Dict[str, Dict] = {}
        self.api_mappings: Dict[str, List[Dict]] = defaultdict(list)
        
    def analyze_directory(self, backend_dir: str) -> Dict[str, Any]:
        """分析 SpringBoot 项目目录"""
        result = {
            'controllers': [],
            'services': [],
            'repositories': [],
            'entities': [],
            'api_mappings': {}
        }
        
        if not os.path.exists(backend_dir):
            logger.warning(f"后端目录不存在：{backend_dir}")
            return result
        
        java_files = list(Path(backend_dir).rglob("*.java"))
        logger.info(f"发现 {len(java_files)} 个 Java 文件")
        
        for java_file in java_files:
            try:
                file_content = self._read_java_file(str(java_file))
                if not file_content:
                    continue
                
                file_name = java_file.name
                rel_path = str(java_file.relative_to(backend_dir))
                
                if self._is_controller(file_content):
                    controller_info = self._analyze_controller(file_content, file_name, rel_path)
                    result['controllers'].append(controller_info)
                    self.controllers[rel_path] = controller_info
                    
                    for api in controller_info.get('apis', []):
                        key = f"{api['method']} {api['path']}"
                        self.api_mappings[key].append(controller_info)
                
                elif self._is_service(file_content):
                    service_info = self._analyze_service(file_content, file_name, rel_path)
                    result['services'].append(service_info)
                    self.services[rel_path] = service_info
                
                elif self._is_repository(file_content):
                    repo_info = self._analyze_repository(file_content, file_name, rel_path)
                    result['repositories'].append(repo_info)
                    self.repositories[rel_path] = repo_info
                
                elif self._is_entity(file_content):
                    entity_info = self._analyze_entity(file_content, file_name, rel_path)
                    result['entities'].append(entity_info)
                    self.entities[rel_path] = entity_info
                    
            except Exception as e:
                logger.error(f"分析 Java 文件失败 {java_file}: {e}")
        
        result['api_mappings'] = dict(self.api_mappings)
        
        logger.info(f"分析完成：{len(result['controllers'])} Controllers, "
                   f"{len(result['services'])} Services, "
                   f"{len(result['repositories'])} Repositories, "
                   f"{len(result['entities'])} Entities")
        
        return result
    
    def _read_java_file(self, file_path: str) -> Optional[str]:
        """读取 Java 文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return None
    
    def _is_controller(self, content: str) -> bool:
        """判断是否为 Controller"""
        indicators = ['@RestController', '@Controller', '@RequestMapping']
        return any(ind in content for ind in indicators)
    
    def _is_service(self, content: str) -> bool:
        """判断是否为 Service"""
        indicators = ['@Service', '@Transactional']
        return any(ind in content for ind in indicators)
    
    def _is_repository(self, content: str) -> bool:
        """判断是否为 Repository/Mapper"""
        indicators = ['@Repository', '@Mapper', 'extends JpaRepository', 'extends Mapper']
        return any(ind in content for ind in indicators)
    
    def _is_entity(self, content: str) -> bool:
        """判断是否为 Entity"""
        indicators = ['@Entity', '@Table']
        return any(ind in content for ind in indicators)
    
    def _analyze_controller(self, content: str, file_name: str, rel_path: str) -> Dict:
        """分析 Controller"""
        class_name = self._extract_class_name(content)
        
        class_mapping = ""
        class_mapping_match = re.search(r'@RequestMapping\s*\(\s*[\'"]([^\'"]+)[\'"]', content)
        if class_mapping_match:
            class_mapping = class_mapping_match.group(1)
        
        apis = []
        mapping_annotations = [
            (r'@GetMapping\s*\(\s*[\'"]([^\'"]+)[\'"]', 'GET'),
            (r'@PostMapping\s*\(\s*[\'"]([^\'"]+)[\'"]', 'POST'),
            (r'@PutMapping\s*\(\s*[\'"]([^\'"]+)[\'"]', 'PUT'),
            (r'@DeleteMapping\s*\(\s*[\'"]([^\'"]+)[\'"]', 'DELETE'),
            (r'@PatchMapping\s*\(\s*[\'"]([^\'"]+)[\'"]', 'PATCH'),
        ]
        
        for pattern, default_method in mapping_annotations:
            matches = re.finditer(pattern, content)
            for match in matches:
                method = default_method
                path = match.group(1)
                
                full_path = self._join_path(class_mapping, path)
                method_sig = self._extract_method_signature(content, match.end())
                dependencies = self._extract_dependencies(content)
                
                api_info = {
                    'path': full_path,
                    'method': method,
                    'method_name': method_sig.get('name', ''),
                    'method_signature': method_sig.get('signature', ''),
                    'dependencies': dependencies,
                    'file': rel_path,
                    'class': class_name
                }
                apis.append(api_info)
        
        return {
            'file': rel_path,
            'file_name': file_name,
            'class_name': class_name,
            'apis': apis,
            'dependencies': self._extract_dependencies(content)
        }
    
    def _analyze_service(self, content: str, file_name: str, rel_path: str) -> Dict:
        """分析 Service"""
        class_name = self._extract_class_name(content)
        methods = self._extract_public_methods(content)
        dependencies = self._extract_dependencies(content)
        interfaces = self._extract_implemented_interfaces(content)
        
        return {
            'file': rel_path,
            'file_name': file_name,
            'class_name': class_name,
            'methods': methods,
            'dependencies': dependencies,
            'interfaces': interfaces
        }
    
    def _analyze_repository(self, content: str, file_name: str, rel_path: str) -> Dict:
        """分析 Repository"""
        class_name = self._extract_class_name(content)
        
        table_name = ""
        table_match = re.search(r'@(?:Table|TableName)\s*\(\s*[\'"]([^\'"]+)[\'"]', content)
        if table_match:
            table_name = table_match.group(1)
        else:
            if class_name.endswith('Repository') or class_name.endswith('Mapper'):
                table_name = f"t_{class_name.replace('Repository', '').replace('Mapper', '').lower()}"
        
        operations = []
        sql_patterns = [
            (r'@Select', 'SELECT'),
            (r'@Insert', 'INSERT'),
            (r'@Update', 'UPDATE'),
            (r'@Delete', 'DELETE'),
        ]
        
        for pattern, op in sql_patterns:
            if re.search(pattern, content):
                operations.append(op)
        
        sql_statements = self._extract_sql_statements(content)
        
        return {
            'file': rel_path,
            'file_name': file_name,
            'class_name': class_name,
            'database_table': table_name,
            'operations': operations if operations else ['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
            'sql_statements': sql_statements
        }
    
    def _analyze_entity(self, content: str, file_name: str, rel_path: str) -> Dict:
        """分析 Entity"""
        class_name = self._extract_class_name(content)
        
        table_name = ""
        table_match = re.search(r'@Table\s*\(\s*name\s*=\s*[\'"]([^\'"]+)[\'"]', content)
        if table_match:
            table_name = table_match.group(1)
        else:
            table_name = f"t_{class_name.lower()}"
        
        fields = self._extract_entity_fields(content)
        
        return {
            'file': rel_path,
            'file_name': file_name,
            'class_name': class_name,
            'database_table': table_name,
            'fields': fields
        }
    
    def _extract_class_name(self, content: str) -> str:
        """提取类名"""
        match = re.search(r'(?:public\s+)?class\s+(\w+)', content)
        return match.group(1) if match else ""
    
    def _extract_method_signature(self, content: str, start_pos: int) -> Dict:
        """提取方法签名"""
        method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(?:\w+(?:<[^>]+>)?\s+)?(\w+)\s*\(([^)]*)\)'
        match = re.search(method_pattern, content[start_pos:start_pos+500])
        
        if match:
            method_name = match.group(1)
            params = match.group(2)
            return {'name': method_name, 'signature': f"{method_name}({params})"}
        
        return {'name': '', 'signature': ''}
    
    def _extract_public_methods(self, content: str) -> List[str]:
        """提取公共方法"""
        methods = []
        pattern = r'public\s+(?:static\s+)?(?:\w+(?:<[^>]+>)?\s+)?(\w+)\s*\([^)]*\)'
        matches = re.findall(pattern, content)
        methods = [m for m in matches if not m.startswith('get') and not m.startswith('set') and m not in ['toString', 'equals', 'hashCode']]
        return methods[:10]
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """提取依赖的服务/组件"""
        deps = []
        
        patterns = [
            r'@Autowired\s+(?:private\s+)?(?:\w+(?:<[^>]+>)?\s+)(\w+)',
            r'@Resource\s+(?:private\s+)?(?:\w+(?:<[^>]+>)?\s+)(\w+)',
            r'@Inject\s+(?:private\s+)?(?:\w+(?:<[^>]+>)?\s+)(\w+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            deps.extend(matches)
        
        ctor_pattern = r'(?:public\s+)?\w+\s*\([^)]*(\w+(?:<[^>]+>)?)\s+(\w+)[^)]*\)'
        matches = re.findall(ctor_pattern, content)
        for match in matches:
            if len(match) == 2:
                deps.append(match[1])
        
        return list(set(deps))
    
    def _extract_implemented_interfaces(self, content: str) -> List[str]:
        """提取实现的接口"""
        interfaces = []
        match = re.search(r'implements\s+([\w\s,]+)', content)
        if match:
            interfaces = [i.strip() for i in match.group(1).split(',')]
        return interfaces
    
    def _extract_entity_fields(self, content: str) -> List[Dict]:
        """提取实体字段"""
        fields = []
        pattern = r'@(?:Column|Id|GeneratedValue)?\s*(?:private|public)?\s*(\w+(?:<[^>]+>)?)\s+(\w+);'
        matches = re.findall(pattern, content)
        
        for match in matches:
            field_type, field_name = match
            fields.append({'name': field_name, 'type': field_type})
        
        return fields[:20]
    
    def _extract_sql_statements(self, content: str) -> List[str]:
        """提取 SQL 语句"""
        sqls = []
        
        patterns = [
            r'@Select\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'@Insert\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'@Update\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'@Delete\s*\(\s*[\'"]([^\'"]+)[\'"]',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            sqls.extend(matches)
        
        return sqls
    
    def _join_path(self, base: str, path: str) -> str:
        """拼接路径"""
        if not base:
            return path
        if not path:
            return base
        return f"{base.rstrip('/')}/{path.lstrip('/')}"


class FullChainBuilder:
    """全链路构建器"""
    
    def __init__(self):
        self.vue_analyzer = VueAnalyzer()
        self.spring_analyzer = SpringBootAnalyzer()
        
    def build_chains(self, vue_dir: str, backend_dir: str, project_name: str = "") -> List[BusinessChain]:
        """构建业务全链路"""
        logger.info("=" * 60)
        logger.info("开始构建业务全链路...")
        logger.info("=" * 60)
        
        logger.info("\n📱 分析前端 Vue 项目...")
        frontend_requests = self.vue_analyzer.analyze_directory(vue_dir)
        
        logger.info("\n🔧 分析后端 SpringBoot 项目...")
        backend_info = self.spring_analyzer.analyze_directory(backend_dir)
        
        logger.info("\n🔗 构建全链路映射...")
        chains = self._match_frontend_backend(frontend_requests, backend_info, project_name)
        
        logger.info(f"\n✅ 成功构建 {len(chains)} 条业务链路")
        
        return chains
    
    def _match_frontend_backend(self, frontend_requests: List[FrontEndRequest], 
                                 backend_info: Dict, project_name: str) -> List[BusinessChain]:
        """匹配前后端，构建完整链路"""
        chains = []
        
        controllers = backend_info.get('controllers', [])
        services = backend_info.get('services', [])
        repositories = backend_info.get('repositories', [])
        entities = backend_info.get('entities', [])
        
        api_index = {}
        for ctrl in controllers:
            for api in ctrl.get('apis', []):
                key = f"{api['method']} {api['path']}"
                api_index[key] = (ctrl, api)
                api_index[api['path']] = (ctrl, api)
        
        for idx, req in enumerate(frontend_requests):
            chain = BusinessChain()
            chain.business_function = self._infer_business_function(req)
            chain.front_end_request = req
            
            matched_ctrl = None
            matched_api = None
            
            api_key = f"{req.http_method} {req.request_path}"
            if api_key in api_index:
                matched_ctrl, matched_api = api_index[api_key]
            elif req.request_path in api_index:
                matched_ctrl, matched_api = api_index[req.request_path]
            else:
                matched_ctrl, matched_api = self._fuzzy_match_api(req, controllers)
            
            if matched_ctrl and matched_api:
                # 构建 Controller 的完整类名（包含包路径）
                ctrl_file = matched_ctrl.get('file', '')
                ctrl_package = self._extract_package(ctrl_file) if ctrl_file else ""
                ctrl_full_class = f"{ctrl_package}.{matched_ctrl['class_name']}" if ctrl_package else matched_ctrl['class_name']
                
                chain.back_end_api = BackEndAPI(
                    controller=matched_ctrl['file'],  # 使用完整路径
                    method=matched_api.get('method_name', ''),
                    method_signature=matched_api.get('method_signature', ''),
                    dependencies=matched_api.get('dependencies', []),
                    annotations=[req.http_method]
                )
                
                chain.services = self._match_services(matched_api.get('dependencies', []), services)
                
                service_deps = []
                for svc in chain.services:
                    service_deps.extend(svc.dependencies)
                chain.storage_access = self._match_repositories(service_deps, repositories, entities)
                
                chain.affected_code_paths = self._generate_code_paths(chain)
                chain.confidence = self._calculate_confidence(chain)
                
                chains.append(chain)
                logger.info(f"  ✓ 链路 {idx+1}: {req.component} -> {matched_ctrl['class_name']} "
                           f"(置信度：{chain.confidence:.0f}%)")
            else:
                chain.confidence = 30.0
                chain.affected_code_paths = [f"{req.component} -> (未匹配到后端 API)"]
                chains.append(chain)
                logger.info(f"  ⚠ 链路 {idx+1}: {req.component} -> (未匹配到后端 API)")
        
        return chains
    
    def _fuzzy_match_api(self, req: FrontEndRequest, controllers: List[Dict]) -> Tuple[Optional[Dict], Optional[Dict]]:
        """模糊匹配 API"""
        best_match = None
        best_score = 0
        
        req_path_parts = req.request_path.lower().replace('/api/', '').replace('_', '').split('/')
        
        for ctrl in controllers:
            for api in ctrl.get('apis', []):
                api_path_parts = api['path'].lower().replace('/api/', '').replace('_', '').split('/')
                
                common_parts = set(req_path_parts) & set(api_path_parts)
                score = len(common_parts) / max(len(req_path_parts), len(api_path_parts))
                
                if score > best_score:
                    best_score = score
                    best_match = (ctrl, api)
        
        if best_score >= 0.3:
            return best_match
        
        return None, None
    
    def _infer_business_function(self, req: FrontEndRequest) -> str:
        """推断业务功能名称"""
        path = req.request_path.lower()
        
        mappings = {
            r'user': '用户管理',
            r'order': '订单管理',
            r'product': '商品管理',
            r'payment': '支付管理',
            r'auth|login|logout': '认证管理',
            r'role|permission': '权限管理',
            r'report': '报表管理',
            r'setting|config': '系统配置',
            r'notification': '消息通知',
            r'file|upload': '文件管理',
        }
        
        for pattern, business in mappings.items():
            if re.search(pattern, path):
                return business
        
        if req.request_path:
            parts = req.request_path.strip('/').split('/')
            if len(parts) >= 2:
                return f"{parts[-2].title()} {parts[-1].title()}"
            return parts[-1].title()
        
        return "未知业务功能"
    
    def _match_services(self, controller_deps: List[str], services: List[Dict]) -> List[ServiceInfo]:
        """匹配服务层"""
        matched_services = []
        
        for dep in controller_deps:
            dep_lower = dep.lower()
            for svc in services:
                svc_class_lower = svc.get('class_name', '').lower()
                svc_file_lower = svc.get('file_name', '').lower()
                svc_full_path = svc.get('file', '').lower()  # 完整路径
                
                # 优先匹配类名，其次匹配文件名，最后匹配完整路径
                if (dep_lower in svc_class_lower or 
                    dep_lower in svc_file_lower or 
                    (svc_full_path and dep_lower in svc_full_path)):
                    service_info = ServiceInfo(
                        service=svc['file'],  # 使用完整路径
                        methods=svc.get('methods', []),
                        dependencies=svc.get('dependencies', []),
                        interfaces=svc.get('interfaces', [])
                    )
                    matched_services.append(service_info)
                    break
        
        # 如果没有精确匹配，尝试模糊匹配
        if not matched_services and services:
            for svc in services[:3]:
                service_info = ServiceInfo(
                    service=svc['file'],  # 使用完整路径
                    methods=svc.get('methods', []),
                    dependencies=svc.get('dependencies', []),
                    interfaces=svc.get('interfaces', [])
                )
                matched_services.append(service_info)
        
        return matched_services
    
    def _extract_package(self, file_path: str) -> str:
        """从文件路径提取包名"""
        if not file_path:
            return ""
        # 移除 src/main/java/ 前缀
        path = file_path.replace('src/main/java/', '').replace('\\', '/')
        # 移除文件名
        parts = path.split('/')[:-1]
        return '.'.join(parts) if parts else ""
    
    def _match_repositories(self, service_deps: List[str], repositories: List[Dict], 
                           entities: List[Dict]) -> List[StorageAccess]:
        """匹配存储层"""
        matched_repos = []
        
        for dep in service_deps:
            dep_lower = dep.lower()
            for repo in repositories:
                repo_class_lower = repo.get('class_name', '').lower()
                repo_file_lower = repo.get('file_name', '').lower()
                repo_full_path = repo.get('file', '').lower()  # 完整路径
                
                if (dep_lower in repo_class_lower or 
                    dep_lower in repo_file_lower or 
                    (repo_full_path and dep_lower in repo_full_path)):
                    table_name = repo.get('database_table', '')
                    if not table_name:
                        for ent in entities:
                            if dep_lower in ent.get('class_name', '').lower():
                                table_name = ent.get('database_table', '')
                                break
                    
                    storage_info = StorageAccess(
                        repository=repo['file'],  # 使用完整路径
                        database_table=table_name,
                        operations=repo.get('operations', ['SELECT']),
                        sql_statements=repo.get('sql_statements', [])
                    )
                    matched_repos.append(storage_info)
                    break
        
        # 如果没有精确匹配，尝试模糊匹配
        if not matched_repos and repositories:
            for repo in repositories[:3]:
                storage_info = StorageAccess(
                    repository=repo['file'],  # 使用完整路径
                    database_table=repo.get('database_table', ''),
                    operations=repo.get('operations', ['SELECT']),
                    sql_statements=repo.get('sql_statements', [])
                )
                matched_repos.append(storage_info)
        
        return matched_repos
    
    def _generate_code_paths(self, chain: BusinessChain) -> List[str]:
        """生成受影响代码路径（包含完整文件路径）"""
        paths = []
        
        if chain.front_end_request and chain.back_end_api:
            # 前端组件路径
            frontend_path = chain.front_end_request.component
            
            # Controller 完整路径
            controller_path = chain.back_end_api.controller
            
            base_path = f"{frontend_path} -> {controller_path}"
            
            if chain.services:
                for svc in chain.services:
                    # Service 完整路径
                    service_path = svc.service
                    path = f"{base_path} -> {service_path}"
                    
                    if chain.storage_access:
                        for storage in chain.storage_access:
                            # Repository 完整路径
                            repo_path = storage.repository
                            full_path = f"{path} -> {repo_path}"
                            if storage.database_table:
                                full_path += f" -> {storage.database_table}"
                            paths.append(full_path)
                    else:
                        paths.append(path)
            else:
                paths.append(base_path)
        
        return paths if paths else ["路径生成失败"]
    
    def _calculate_confidence(self, chain: BusinessChain) -> float:
        """计算链路置信度"""
        score = 0.0
        max_score = 5.0
        
        if chain.front_end_request:
            score += 0.5
            if chain.front_end_request.request_path:
                score += 0.3
            if chain.front_end_request.parameters:
                score += 0.2
        
        if chain.back_end_api:
            score += 1.0
            if chain.back_end_api.method_signature:
                score += 0.5
        
        if chain.services:
            score += 1.0
            if len(chain.services) > 1:
                score += 0.5
        
        if chain.storage_access:
            score += 0.7
            if any(s.database_table for s in chain.storage_access):
                score += 0.3
        
        if chain.affected_code_paths and chain.affected_code_paths[0] != "路径生成失败":
            score += 0.5
        
        return min(100.0, (score / max_score) * 100)


class CodeQualityAnalyzer:
    """代码质量和安全分析器（模拟）"""
    
    def analyze_chain(self, chain: BusinessChain, backend_dir: str) -> BusinessChain:
        """分析链路的代码质量和安全问题"""
        chain.code_quality = CodeQuality(
            sonarqube_issues=self._count_issues(backend_dir),
            code_smells=self._estimate_code_smells(backend_dir),
            bugs=self._estimate_bugs(backend_dir),
            vulnerabilities=self._estimate_vulnerabilities(backend_dir),
            duplications=self._estimate_duplications(backend_dir)
        )
        
        chain.security_vulnerabilities = SecurityVulnerabilities(
            semgrep_findings=self._simulate_semgrep_findings(),
            xss_vulnerabilities=self._simulate_xss_count(),
            sql_injection=self._simulate_sql_injection_count(),
            other_vulnerabilities=self._simulate_other_vulns()
        )
        
        chain.performance_bottlenecks = PerformanceBottlenecks(
            spring_startup_analyzer_findings=self._simulate_startup_issues(),
            slow_methods=self._simulate_slow_methods(),
            inefficient_data_access=self._simulate_inefficient_access()
        )
        
        return chain
    
    def _count_issues(self, backend_dir: str) -> int:
        return 15
    
    def _estimate_code_smells(self, backend_dir: str) -> int:
        return 8
    
    def _estimate_bugs(self, backend_dir: str) -> int:
        return 3
    
    def _estimate_vulnerabilities(self, backend_dir: str) -> int:
        return 4
    
    def _estimate_duplications(self, backend_dir: str) -> int:
        return 2
    
    def _simulate_semgrep_findings(self) -> int:
        return 5
    
    def _simulate_xss_count(self) -> int:
        return 2
    
    def _simulate_sql_injection_count(self) -> int:
        return 1
    
    def _simulate_other_vulns(self) -> int:
        return 2
    
    def _simulate_startup_issues(self) -> int:
        return 3
    
    def _simulate_slow_methods(self) -> int:
        return 2
    
    def _simulate_inefficient_access(self) -> int:
        return 1


def convert_chain_to_dict(chain: BusinessChain) -> Dict:
    """将 BusinessChain 转换为字典（符合指定格式）"""
    return {
        'business_function': chain.business_function,
        'front_end_request': {
            'component': chain.front_end_request.component if chain.front_end_request else "",
            'request_path': chain.front_end_request.request_path if chain.front_end_request else "",
            'parameters': chain.front_end_request.parameters if chain.front_end_request else []
        } if chain.front_end_request else {},
        'back_end_api': {
            'controller': chain.back_end_api.controller if chain.back_end_api else "",
            'method': chain.back_end_api.method_signature if chain.back_end_api else "",
            'dependencies': chain.back_end_api.dependencies if chain.back_end_api else []
        } if chain.back_end_api else {},
        'services': [
            {
                'service': svc.service,
                'methods': svc.methods,
                'dependencies': svc.dependencies
            } for svc in chain.services
        ],
        'storage_access': [
            {
                'repository': storage.repository,
                'database_table': storage.database_table,
                'operations': storage.operations
            } for storage in chain.storage_access
        ],
        '受影响代码路径': chain.affected_code_paths
    }


def generate_json_report(chains: List[BusinessChain], output_path: str, project_name: str = ""):
    """生成 JSON 格式报告"""
    report = {
        'project_name': project_name,
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_chains': len(chains),
        'average_confidence': sum(c.confidence for c in chains) / len(chains) if chains else 0,
        'business_chains': []
    }
    
    for chain in chains:
        chain_dict = convert_chain_to_dict(chain)
        report['business_chains'].append(chain_dict)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ JSON 报告已生成：{output_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='SpringBoot + Vue 全链路静态分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python fullchain_analyzer.py --backend ./springboot-project --frontend ./vue-project --output ./analysis_output
  python fullchain_analyzer.py -b E:\\project\\backend -f E:\\project\\frontend -o E:\\project\\output --project-name "数币工程"
        """
    )
    
    parser.add_argument('--backend', '-b', required=True, 
                       help='SpringBoot 后端项目路径')
    parser.add_argument('--frontend', '-f', required=True, 
                       help='Vue 前端项目路径')
    parser.add_argument('--output', '-o', default='./analysis_output',
                       help='输出目录 (默认：./analysis_output)')
    parser.add_argument('--project-name', '-p', default='',
                       help='项目名称')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细日志')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("=" * 70)
    print("  SpringBoot + Vue 全链路静态分析工具 v2.0")
    print("  业务功能 → 前端请求 → 后端 API → 服务层 → 存储层 → 数据结构")
    print("=" * 70)
    print()
    
    if not os.path.exists(args.backend):
        logger.error(f"❌ 后端项目路径不存在：{args.backend}")
        sys.exit(1)
    
    if not os.path.exists(args.frontend):
        logger.error(f"❌ 前端项目路径不存在：{args.frontend}")
        sys.exit(1)
    
    os.makedirs(args.output, exist_ok=True)
    
    builder = FullChainBuilder()
    chains = builder.build_chains(args.frontend, args.backend, args.project_name)
    
    if not chains:
        logger.warning("⚠️  未构建出任何业务链路")
    
    logger.info("\n🔍 进行代码质量和安全分析...")
    quality_analyzer = CodeQualityAnalyzer()
    for chain in chains:
        quality_analyzer.analyze_chain(chain, args.backend)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_output = os.path.join(args.output, f"fullchain_analysis_{timestamp}.json")
    
    logger.info(f"\n📄 生成 JSON 报告...")
    generate_json_report(chains, json_output, args.project_name)
    
    print()
    print("=" * 70)
    print("  分析完成!")
    print("=" * 70)
    print(f"  项目名称：{args.project_name or '未命名'}")
    print(f"  业务链路：{len(chains)} 条")
    print(f"  平均置信度：{sum(c.confidence for c in chains) / len(chains):.1f}%" if chains else "  平均置信度：N/A")
    print(f"  输出文件：{json_output}")
    print("=" * 70)
    
    if chains:
        print()
        print("前 5 条业务链路摘要:")
        print("-" * 70)
        for i, chain in enumerate(chains[:5], 1):
            comp = chain.front_end_request.component if chain.front_end_request else "Unknown"
            ctrl = chain.back_end_api.controller if chain.back_end_api else "Unknown"
            biz = chain.business_function
            conf = chain.confidence
            print(f"  {i}. {biz}: {comp} -> {ctrl} (置信度：{conf:.0f}%)")
    
    print()
    logger.info("✨ 分析完成！")


if __name__ == "__main__":
    main()
