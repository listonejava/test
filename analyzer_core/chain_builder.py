# -*- coding: utf-8 -*-
"""
业务链路构建器
构建从前端到后端的完整调用链
"""
from typing import List, Dict, Any
import logging

from .models import VueApiRequest, BackEndAPI, ServiceInfo, StorageAccess, BusinessChain, MethodInfo
from .matchers.service_matcher import ServiceMatcher
from .matchers.path_matcher import PathMatcher
from .config import MATCH_THRESHOLD_MODULE

logger = logging.getLogger(__name__)


class ChainBuilder:
    """业务链路构建器"""
    
    def __init__(self, controllers: List[BackEndAPI], services: List[ServiceInfo], 
                 mappers: List[Dict], entities: List[Dict], xml_maps: Dict[str, Dict]):
        self.controllers = controllers
        self.services = services
        self.mappers = mappers
        self.entities = entities
        self.xml_maps = xml_maps
        
        # 初始化服务匹配器
        self.service_matcher = ServiceMatcher(services)
    
    def build(self, vue_requests: List[VueApiRequest]) -> List[BusinessChain]:
        """构建所有业务链路"""
        chains = []
        
        for vue_req in vue_requests:
            chain = self._build_single_chain(vue_req)
            if chain:
                chains.append(chain)
        
        return chains
    
    def _build_single_chain(self, vue_req: VueApiRequest) -> BusinessChain:
        """构建单个业务链路"""
        # 1. 匹配 Controller
        matched_ctrl, best_score = self._find_best_controller(vue_req)
        
        if not matched_ctrl or best_score < MATCH_THRESHOLD_MODULE:
            return None
        
        # 2. 匹配 Services（增强版）
        matched_services = self._find_services(matched_ctrl)
        
        # 3. 匹配 Storage
        matched_storage = self._find_storage(matched_services)
        
        # 4. 创建链路对象
        return self._create_chain(vue_req, matched_ctrl, matched_services, matched_storage, best_score)
    
    def _find_best_controller(self, vue_req: VueApiRequest) -> tuple:
        """找到最佳匹配的 Controller"""
        matched_ctrl = None
        best_score = 0
        
        for ctrl in self.controllers:
            _, score = PathMatcher.match(
                vue_req.request_path,
                vue_req.raw_path,
                ctrl.base_mapping,
                ctrl.method.annotations
            )
            
            if score > best_score:
                best_score = score
                matched_ctrl = ctrl
        
        return matched_ctrl, best_score
    
    def _find_services(self, ctrl: BackEndAPI) -> List[ServiceInfo]:
        """查找相关服务（增强版：支持包名启发式）"""
        matched_services = []
        seen = set()
        
        # 策略 1: 基于依赖名称匹配
        for dep in ctrl.dependencies:
            found = self.service_matcher.match(dep, ctrl.controller_class)
            for svc in found:
                if svc.service_class not in seen:
                    matched_services.append(svc)
                    seen.add(svc.service_class)
        
        # 策略 2: 如果没有找到，尝试包名启发式匹配
        if not matched_services:
            fallback_services = self.service_matcher.match_all_relevant(ctrl.controller_class)
            for svc in fallback_services:
                if svc.service_class not in seen:
                    matched_services.append(svc)
                    seen.add(svc.service_class)
        
        return matched_services
    
    def _find_storage(self, services: List[ServiceInfo]) -> List[StorageAccess]:
        """查找数据存储层"""
        matched_storage = []
        
        for svc in services:
            for dep in svc.dependencies:
                for mp in self.mappers:
                    mp_name = mp['name']
                    if dep == mp_name or dep.lower() in mp_name.lower():
                        xml_info = self.xml_maps.get(mp['class'], {})
                        tables = xml_info.get('tables', [])
                        ops = xml_info.get('operations', [])
                        
                        # 如果没有找到表，尝试从 Entity 推断
                        if not tables:
                            for ent in self.entities:
                                if ent['class'].lower().endswith(mp_name.lower()):
                                    tables = [ent['table']]
                        
                        if tables:
                            storage = StorageAccess(
                                repository_file=mp['file'],
                                repository_class=mp['class'],
                                database_table=tables[0],
                                operations=ops if ops else ["SELECT"],
                                xml_file=xml_info.get('xml_file', '')
                            )
                            matched_storage.append(storage)
        
        return matched_storage
    
    def _create_chain(self, vue: VueApiRequest, ctrl: BackEndAPI,
                      services: List[ServiceInfo], storage: List[StorageAccess],
                      confidence_score: int) -> BusinessChain:
        """创建业务链路对象"""
        # 生成业务功能名称
        path_parts = vue.request_path.strip('/').split('/')
        if len(path_parts) >= 2:
            func_name = path_parts[-2].title() + " " + path_parts[-1].replace('/', ' ').title()
        else:
            func_name = vue.request_path.strip('/').replace('/', ' ').title()
        
        # 构建前端请求字典
        front_dict = {
            "component": vue.component_file,
            "request_path": vue.request_path,
            "parameters": vue.parameters
        }
        
        # 构建后端 API 字典
        back_dict = {
            "controller": ctrl.controller_class + ".java",
            "method": {
                "name": ctrl.method.name,
                "signature": ctrl.method.signature,
                "description": ctrl.method.description
            },
            "dependencies": ctrl.dependencies
        }
        
        # 构建服务列表
        svc_list = []
        for svc in services:
            svc_list.append({
                "service": svc.service_class + ".java",
                "methods": svc.methods[:5],
                "dependencies": svc.dependencies
            })
        
        # 构建存储访问列表
        stor_list = []
        for st in storage:
            stor_list.append({
                "repository": st.repository_class + ".java",
                "database_table": st.database_table,
                "operations": st.operations
            })
        
        # 生成代码路径
        paths = self._generate_code_paths(vue, ctrl, services, storage)
        
        # 计算置信度
        confidence = float(confidence_score)
        if services:
            confidence = min(100, confidence + 10)
        if storage:
            confidence = min(100, confidence + 10)
        
        return BusinessChain(
            business_function=func_name,
            front_end_request=front_dict,
            back_end_api=back_dict,
            services=svc_list,
            storage_access=stor_list,
            code_paths=paths,
            confidence=confidence
        )
    
    def _generate_code_paths(self, vue: VueApiRequest, ctrl: BackEndAPI,
                             services: List[ServiceInfo], storage: List[StorageAccess]) -> List[str]:
        """生成包含完整绝对路径的代码调用链"""
        paths = []
        
        vue_path = vue.component_file
        ctrl_path = ctrl.controller_file
        
        base_path = f"{vue_path} -> {ctrl_path}"
        
        if not services:
            paths.append(base_path + " -> Database")
            return paths
        
        for svc in services:
            svc_path = svc.service_file
            path = base_path + f" -> {svc_path}"
            
            found_storage = False
            for dep in svc.dependencies:
                for st in storage:
                    repo_path = st.repository_file
                    repo_name = st.repository_class.split('.')[-1]
                    
                    if dep == repo_name or dep.lower() in repo_name.lower():
                        path += f" -> {repo_path} -> {st.database_table}"
                        paths.append(path)
                        found_storage = True
                        break
                if found_storage:
                    break
            
            if not found_storage:
                paths.append(path + " -> Database")
        
        return paths
