# -*- coding: utf-8 -*-
"""
Java 代码解析器
解析 Controller、Service、Mapper、Entity
"""
import os
import re
from typing import List, Dict, Any
import logging

from ..models import BackEndAPI, ServiceInfo, MethodInfo
from ..config import EXCLUDE_DIRS

logger = logging.getLogger(__name__)


class JavaParser:
    """Java 代码解析器"""
    
    def __init__(self):
        self.controller_pattern = re.compile(r'@(?:Rest)?Controller\s*(?:\([^)]*\))?\s*public\s+class\s+(\w+)')
        self.service_pattern = re.compile(r'@Service\s*(?:\([^)]*\))?\s*public\s+class\s+(\w+)')
        self.mapper_pattern = re.compile(r'public\s+interface\s+(\w+Mapper)\s+')
        self.entity_pattern = re.compile(r'@(?:Entity|TableName|Table)\s*(?:\([^)]*\))?\s*public\s+class\s+(\w+)')
        
        self.class_mapping_pattern = re.compile(r'@(?:Rest)?Controller\s*(?:\([^)]*\))?\s*@(?:Mapping|RequestMapping)\s*\(\s*["\']([^"\']+)["\']')
        
        self.method_pattern_with_path = re.compile(r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*\(\s*["\']([^"\']*)["\']\s*\)\s*public\s+(?:[\w<>]+\s+)?(\w+)\s*\(([^)]*)\)')
        self.method_pattern_no_path = re.compile(r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*\(\s*\)\s*public\s+(?:[\w<>]+\s+)?(\w+)\s*\(([^)]*)\)')
        
        self.autowired_pattern = re.compile(r'@Autowired\s+(?:private\s+)?([\w<>]+)\s+(\w+);')
        self.resource_pattern = re.compile(r'@Resource\s+(?:private\s+)?([\w<>]+)\s+(\w+);')
        self.package_pattern = re.compile(r'package\s+([\w.]+);')

    def parse_package(self, content: str) -> str:
        match = self.package_pattern.search(content)
        return match.group(1) if match else ""

    def extract_method_description(self, content: str, method_name: str) -> str:
        """增强版注释提取"""
        safe_name = re.escape(method_name)
        method_start_pattern = re.compile(r'(?:public|private|protected)\s+(?:[\w<>]+\s+)?' + safe_name + r'\s*\(')
        match = method_start_pattern.search(content)
        
        if match:
            end_pos = match.start()
            before = content[max(0, end_pos-500):end_pos]
            
            # 1. 查 Javadoc
            javadoc_match = re.search(r'/\*\*\s*([\s\S]*?)\*/\s*$', before)
            if javadoc_match:
                comment_text = javadoc_match.group(1).strip()
                clean_comment = re.sub(r'\s*\*\s*', ' ', comment_text)
                clean_comment = re.sub(r'\s+', ' ', clean_comment).strip()
                if clean_comment:
                    return clean_comment.split('.')[0].strip()
            
            # 2. 查单行注释
            lines = before.split('\n')[::-1]
            for line in lines:
                s_line = line.strip()
                if s_line.startswith('//'):
                    return s_line[2:].strip()
                elif s_line and not s_line.startswith('*') and not s_line.startswith('/**'):
                    break
                    
        return "无描述"

    def parse_controller(self, file_path: str, content: str) -> List[BackEndAPI]:
        results = []
        package_name = self.parse_package(content)
        class_match = self.controller_pattern.search(content)
        
        if not class_match:
            return results
            
        class_name = class_match.group(1)
        full_class_name = f"{package_name}.{class_name}" if package_name else class_name
        
        base_mapping = ""
        class_map_match = self.class_mapping_pattern.search(content)
        if class_map_match:
            base_mapping = class_map_match.group(1)
        
        dependencies = []
        for match in self.autowired_pattern.finditer(content):
            dependencies.append(match.group(2))
        for match in self.resource_pattern.finditer(content):
            dependencies.append(match.group(2))
            
        # 模式 A: @GetMapping("path")
        for match in self.method_pattern_with_path.finditer(content):
            http_method = match.group(1)
            path = match.group(2)
            method_name = match.group(3)
            params_str = match.group(4).strip()
            
            full_path = base_mapping.rstrip('/') + '/' + path.lstrip('/') if base_mapping and path else (base_mapping or path)
            if not full_path: full_path = "/"
            
            signature = f"{method_name}({params_str})"
            description = self.extract_method_description(content, method_name)
            
            method_info = MethodInfo(
                name=method_name,
                signature=signature,
                description=description,
                annotations=[f"@{http_method}Mapping({path})"]
            )
            
            api = BackEndAPI(
                controller_file=os.path.abspath(file_path),
                controller_class=full_class_name,
                method=method_info,
                dependencies=dependencies,
                base_mapping=base_mapping,
                full_path=full_path
            )
            results.append(api)

        # 模式 B: @GetMapping() (无路径)
        for match in self.method_pattern_no_path.finditer(content):
            http_method = match.group(1)
            method_name = match.group(2)
            params_str = match.group(3).strip()
            
            full_path = base_mapping if base_mapping else "/"
            
            signature = f"{method_name}({params_str})"
            description = self.extract_method_description(content, method_name)
            
            method_info = MethodInfo(
                name=method_name,
                signature=signature,
                description=description,
                annotations=[f"@{http_method}Mapping()"]
            )
            
            api = BackEndAPI(
                controller_file=os.path.abspath(file_path),
                controller_class=full_class_name,
                method=method_info,
                dependencies=dependencies,
                base_mapping=base_mapping,
                full_path=full_path
            )
            results.append(api)
            
        return results

    def parse_service(self, file_path: str, content: str) -> List[ServiceInfo]:
        results = []
        package_name = self.parse_package(content)
        class_match = self.service_pattern.search(content)
        
        if not class_match:
            return results
            
        class_name = class_match.group(1)
        full_class_name = f"{package_name}.{class_name}" if package_name else class_name
        
        dependencies = []
        for match in self.autowired_pattern.finditer(content):
            dependencies.append(match.group(2))
        for match in self.resource_pattern.finditer(content):
            dependencies.append(match.group(2))
            
        methods = []
        method_def_pattern = re.compile(r'public\s+(?:[\w<>]+\s+)?(\w+)\s*\([^)]*\)\s*(?:\{|;)')
        for match in method_def_pattern.finditer(content):
            method_name = match.group(1)
            if not method_name.startswith('<') and len(method_name) < 50:
                methods.append(method_name)
                
        service = ServiceInfo(
            service_file=os.path.abspath(file_path),
            service_class=full_class_name,
            methods=methods,
            dependencies=dependencies
        )
        results.append(service)
        return results

    def parse_mapper(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        results = []
        package_name = self.parse_package(content)
        class_match = self.mapper_pattern.search(content)
        
        if not class_match:
            general_interface = re.compile(r'public\s+interface\s+(\w+)\s+')
            class_match = general_interface.search(content)
        
        if not class_match:
            return results
            
        class_name = class_match.group(1)
        full_class_name = f"{package_name}.{class_name}" if package_name else class_name
        
        return [{
            "file": os.path.abspath(file_path),
            "class": full_class_name,
            "name": class_name
        }]

    def parse_entity(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        results = []
        package_name = self.parse_package(content)
        class_match = self.entity_pattern.search(content)
        
        if not class_match:
            return results
            
        class_name = class_match.group(1)
        full_class_name = f"{package_name}.{class_name}" if package_name else class_name
        
        table_name = class_name.lower()
        table_pattern = re.compile(r'@(?:TableName|Table)\s*\(\s*(?:name\s*=)?\s*["\']([^"\']+)["\']')
        match = table_pattern.search(content)
        if match:
            table_name = match.group(1)
            
        return [{
            "file": os.path.abspath(file_path),
            "class": full_class_name,
            "table": table_name
        }]
