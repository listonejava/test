# -*- coding: utf-8 -*-
"""
服务层匹配器
增强版：支持若依框架命名规范和包名启发式匹配
"""
from typing import List, Set
import logging

from ..models import ServiceInfo
from ..config import SERVICE_INTERFACE_PREFIXES, SERVICE_IMPL_SUFFIXES

logger = logging.getLogger(__name__)


class ServiceMatcher:
    """服务层模糊匹配器"""
    
    def __init__(self, services: List[ServiceInfo]):
        self.services = services
        # 建立索引加速查找
        self._build_index()
    
    def _build_index(self):
        """构建服务索引"""
        self.name_to_service = {}
        self.package_services = {}
        
        for svc in self.services:
            svc_name = svc.service_class.split('.')[-1]
            pkg = '.'.join(svc.service_class.split('.')[:-1])
            
            # 名称索引
            self.name_to_service[svc_name.lower()] = svc
            
            # 包名索引
            if pkg not in self.package_services:
                self.package_services[pkg] = []
            self.package_services[pkg].append(svc)
    
    def match(self, dep_name: str, controller_package: str = "") -> List[ServiceInfo]:
        """
        匹配服务层
        策略：
        1. 精确匹配
        2. 去除 I 前缀/Impl 后缀匹配
        3. 包名启发式匹配
        """
        matched = []
        dep_lower = dep_name.lower()
        dep_clean = dep_lower
        
        # 预处理依赖名
        if dep_lower.startswith('i') and len(dep_lower) > 1:
            dep_clean = dep_lower[1:]
        
        seen = set()
        
        # 规则 1: 精确匹配和变形匹配
        for svc in self.services:
            svc_name = svc.service_class.split('.')[-1]
            svc_lower = svc_name.lower()
            svc_clean = svc_lower
            
            if svc_lower.endswith('impl'):
                svc_clean = svc_lower[:-4]
            
            if dep_lower == svc_lower or dep_clean == svc_clean:
                if svc.service_class not in seen:
                    matched.append(svc)
                    seen.add(svc.service_class)
        
        # 规则 2: 包含匹配（长度差异较大时）
        if len(dep_clean) > 3:
            for svc in self.services:
                svc_name = svc.service_class.split('.')[-1]
                svc_lower = svc_name.lower()
                svc_clean = svc_lower
                
                if svc_lower.endswith('impl'):
                    svc_clean = svc_lower[:-4]
                
                if dep_clean in svc_clean and svc.service_class not in seen:
                    matched.append(svc)
                    seen.add(svc.service_class)
        
        # 规则 3: 包名启发式匹配（如果提供了 Controller 包名）
        if controller_package and not matched:
            # 尝试在同包或子包中查找
            base_pkg_parts = controller_package.split('.')
            for i in range(len(base_pkg_parts)):
                candidate_pkg = '.'.join(base_pkg_parts[:i+1])
                if 'controller' in candidate_pkg.lower():
                    # 尝试找对应的 service 包
                    service_pkg = candidate_pkg.replace('controller', 'service')
                    if service_pkg in self.package_services:
                        for svc in self.package_services[service_pkg]:
                            if svc.service_class not in seen:
                                matched.append(svc)
                                seen.add(svc.service_class)
                        break
        
        return matched
    
    def match_all_relevant(self, controller_package: str) -> List[ServiceInfo]:
        """
        基于包名匹配所有相关服务
        用于当 Controller 没有显式依赖时的回退策略
        """
        if not controller_package:
            return []
        
        matched = []
        seen = set()
        
        # 从 controller 包推导 service 包
        if 'controller' in controller_package.lower():
            service_pkg = controller_package.replace('controller', 'service')
            if service_pkg in self.package_services:
                for svc in self.package_services[service_pkg]:
                    if svc.service_class not in seen:
                        matched.append(svc)
                        seen.add(svc.service_class)
        
        # 也检查 system、business 等常见包
        base_pkg = controller_package.split('.web')[0] if '.web' in controller_package else controller_package
        potential_pkgs = [
            f"{base_pkg}.system.service",
            f"{base_pkg}.service",
        ]
        
        for pkg in potential_pkgs:
            if pkg in self.package_services:
                for svc in self.package_services[pkg]:
                    if svc.service_class not in seen:
                        matched.append(svc)
                        seen.add(svc.service_class)
        
        return matched
