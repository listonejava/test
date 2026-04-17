# -*- coding: utf-8 -*-
"""
前端 API 模块解析器
解析 src/api 目录下的 JS 文件，建立函数名到 URL 的映射
"""
import os
import re
from typing import Dict, List
import logging

from ..models import ApiFunction
from ..config import LOG_LEVEL, LOG_FORMAT

logger = logging.getLogger(__name__)


class ApiModuleParser:
    """解析 src/api 目录下的 JS 文件"""
    
    def __init__(self):
        self.func_pattern = re.compile(
            r'//\s*([^\n]+)\n\s*export\s+function\s+(\w+)\s*\(([^)]*)\)\s*\{[\s\S]*?return\s+request\s*\(\s*\{[\s\S]*?url:\s*["\']([^"\']+)["\'][\s\S]*?method:\s*["\'](\w+)["\']',
            re.IGNORECASE | re.MULTILINE
        )
        self.simple_func_pattern = re.compile(
            r'export\s+function\s+(\w+)\s*\(([^)]*)\)\s*\{[\s\S]*?return\s+request\s*\(\s*\{[\s\S]*?url:\s*["\']([^"\']+)["\'][\s\S]*?method:\s*["\'](\w+)["\']',
            re.IGNORECASE | re.MULTILINE
        )
        self.base_api_patterns = [
            re.compile(r'VUE_APP_BASE_API\s*=\s*["\']([^"\']+)["\']'),
            re.compile(r'baseURL:\s*["\']([^"\']+)["\']')
        ]

    def detect_base_api(self, api_root: str) -> str:
        """推断 Base API 前缀"""
        src_root = os.path.dirname(api_root)
        env_files = ['.env', '.env.development', '.env.production']
        
        for env_file in env_files:
            f_path = os.path.join(src_root, env_file)
            if os.path.exists(f_path):
                try:
                    with open(f_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    for pattern in self.base_api_patterns:
                        match = pattern.search(content)
                        if match:
                            return match.group(1).strip()
                except:
                    pass
        
        req_js = os.path.join(src_root, 'utils', 'request.js')
        if os.path.exists(req_js):
            try:
                with open(req_js, 'r', encoding='utf-8') as f:
                    content = f.read()
                for pattern in self.base_api_patterns:
                    match = pattern.search(content)
                    if match:
                        return match.group(1).strip()
            except:
                pass
            
        return ""

    def parse_api_file(self, file_path: str, base_prefix: str) -> List[ApiFunction]:
        """解析单个 API 文件"""
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"读取 API 文件失败 {file_path}: {e}")
            return results
            
        try:
            rel_path = os.path.relpath(file_path, os.path.dirname(os.path.dirname(file_path)))
            parts = rel_path.split(os.sep)
            module_name = parts[0] if len(parts) > 1 else "unknown"
        except:
            module_name = "unknown"
        
        # 1. 尝试带注释模式
        matches = self.func_pattern.findall(content)
        for match in matches:
            comment, func_name, params, url, method = match
            clean_url = url.strip()
            
            if base_prefix and not clean_url.startswith(base_prefix):
                prefix = base_prefix.rstrip('/')
                u = clean_url.lstrip('/')
                full_url = f"{prefix}/{u}" if u else prefix
            else:
                full_url = clean_url
                
            results.append(ApiFunction(
                name=func_name,
                url=clean_url,
                method=method.upper(),
                file_path=os.path.abspath(file_path),
                module_name=module_name,
                description=comment.strip(),
                full_url=full_url
            ))
            
        # 2. 尝试简单模式
        if not matches:
            simple_matches = self.simple_func_pattern.findall(content)
            for match in simple_matches:
                func_name, params, url, method = match
                clean_url = url.strip()
                
                desc = "无描述"
                pos = content.find(f"export function {func_name}")
                if pos > 0:
                    before = content[max(0, pos-100):pos]
                    lines = before.split('\n')[::-1]
                    for line in lines:
                        if '//' in line:
                            desc = line.split('//', 1)[1].strip()
                            break
                        elif line.strip() and not line.strip().startswith('export'):
                            break
                            
                if not any(f.name == func_name for f in results):
                    if base_prefix and not clean_url.startswith(base_prefix):
                        prefix = base_prefix.rstrip('/')
                        u = clean_url.lstrip('/')
                        full_url = f"{prefix}/{u}" if u else prefix
                    else:
                        full_url = clean_url

                    results.append(ApiFunction(
                        name=func_name,
                        url=clean_url,
                        method=method.upper(),
                        file_path=os.path.abspath(file_path),
                        module_name=module_name,
                        description=desc,
                        full_url=full_url
                    ))
                
        return results

    def scan_api_directory(self, api_root: str) -> Dict[str, ApiFunction]:
        """扫描整个 api 目录"""
        api_map = {}
        
        if not os.path.exists(api_root):
            logger.warning(f"API 目录不存在：{api_root}")
            return api_map
            
        base_prefix = self.detect_base_api(api_root)
        if base_prefix:
            logger.info(f"检测到 API 前缀：{base_prefix}")
        else:
            logger.info("未检测到显式 API 前缀，将使用原始路径")
            
        js_files = []
        for root, dirs, files in os.walk(api_root):
            dirs[:] = [d for d in dirs if d != 'node_modules']
            for file in files:
                if file.endswith('.js'):
                    js_files.append(os.path.join(root, file))
                    
        logger.info(f"发现 {len(js_files)} 个 API 定义文件")
        
        for file in js_files:
            funcs = self.parse_api_file(file, base_prefix)
            for func in funcs:
                api_map[func.name] = func
                
        logger.info(f"解析出 {len(api_map)} 个 API 函数")
        return api_map
