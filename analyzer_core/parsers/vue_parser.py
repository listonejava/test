# -*- coding: utf-8 -*-
"""
Vue 组件解析器
识别 API 导入和调用
"""
import os
import re
from typing import Dict, List
import logging

from ..models import VueApiRequest, ApiFunction
from ..config import API_PREFIXES_TO_STRIP

logger = logging.getLogger(__name__)


class VueParser:
    """Vue 解析器：识别 API 导入和调用"""
    
    def __init__(self, api_map: Dict[str, ApiFunction]):
        self.api_map = api_map
        self.import_pattern = re.compile(r'import\s+\{([^}]+)\}\s+from\s+["\'](@/api/[^"\']+)["\']')

    def parse_vue_file(self, file_path: str) -> List[VueApiRequest]:
        """解析 Vue 文件"""
        results = []
        abs_path = os.path.abspath(file_path)
        file_name = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"读取 Vue 文件失败 {file_path}: {e}")
            return results
            
        imported_funcs = set()
        imports = self.import_pattern.findall(content)
        for imp in imports:
            if isinstance(imp, tuple):
                func_str = imp[0]
            else:
                func_str = imp
            funcs = [f.strip() for f in func_str.split(',') if f.strip()]
            imported_funcs.update(funcs)
            
        found_api_calls = False
        for func_name in imported_funcs:
            if func_name not in self.api_map:
                continue
                
            api_func = self.api_map[func_name]
            found_api_calls = True
            
            safe_func_name = re.escape(func_name)
            call_regex = re.compile(rf'(?:this\.)?{safe_func_name}\s*\(([^)]*)\)')
            
            for match in call_regex.finditer(content):
                params_str = match.group(1).strip()
                params = []
                if params_str:
                    params = [p.strip().split('=')[0].strip() for p in params_str.split(',') if p.strip()]
                    
                req = VueApiRequest(
                    component_file=abs_path,
                    component_name=file_name,
                    function_name=func_name,
                    request_path=api_func.url,
                    method=api_func.method,
                    protocol="https",
                    parameters=params,
                    api_file=api_func.file_path,
                    raw_path=api_func.full_url
                )
                results.append(req)
        
        # 兜底机制
        if not found_api_calls or True:
            direct_patterns = [
                re.compile(r'(?:axios|this.\$axios|request)\s*\.\s*(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'),
            ]
            for pattern in direct_patterns:
                for match in pattern.finditer(content):
                    groups = match.groups()
                    if len(groups) == 2:
                        method = groups[0].upper()
                        path = groups[1]
                        
                        if any(r.request_path == path for r in results):
                            continue
                            
                        protocol = "https"
                        if path.startswith("http://"):
                            protocol = "http"
                            path = path[7:]
                        elif path.startswith("https://"):
                            protocol = "https"
                            path = path[8:]
                            
                        # 去除可能的前缀
                        prefix_stripped = False
                        for prefix in API_PREFIXES_TO_STRIP:
                            if f'/{prefix}/' in path:
                                path = path.split(f'/{prefix}', 1)[1]
                                prefix_stripped = True
                                break
                        if not prefix_stripped:
                            if path.startswith('/dev-api'):
                                path = path.split('/dev-api', 1)[1]
                            elif path.startswith('/prod-api'):
                                path = path.split('/prod-api', 1)[1]
                            
                        params = []
                        if '?' in path:
                            query_str = path.split('?')[1]
                            params = [p.split('=')[0] for p in query_str.split('&') if '=' in p]
                            
                        req = VueApiRequest(
                            component_file=abs_path,
                            component_name=file_name,
                            function_name="direct_call",
                            request_path=path,
                            method=method,
                            protocol=protocol,
                            raw_path=path
                        )
                        results.append(req)
                    
        return results
