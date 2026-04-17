# -*- coding: utf-8 -*-
"""
路径匹配器
智能匹配前端请求路径与后端 API 路径
"""
import re
from typing import Tuple, Optional
import logging

from ..config import MATCH_THRESHOLD_EXACT, MATCH_THRESHOLD_CONTAINS, MATCH_THRESHOLD_MODULE, API_PREFIXES_TO_STRIP, MIN_CONFIDENCE

logger = logging.getLogger(__name__)


class PathMatcher:
    """路径匹配器"""
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """标准化路径：去除前后缀，转小写"""
        normalized = path.rstrip('/').lower()
        
        # 去除常见前缀
        for prefix in API_PREFIXES_TO_STRIP:
            if normalized.startswith(f'/{prefix}'):
                normalized = normalized[len(prefix)+1:]
                break
        
        return normalized
    
    @staticmethod
    def match(request_path: str, raw_path: str, ctrl_base: str, method_annotations: list) -> Tuple[Optional[str], int]:
        """
        匹配请求路径与控制器路径
        返回：(匹配类型，置信度分数)
        """
        match_path = raw_path if raw_path else request_path
        normalized_req = PathMatcher.normalize_path(match_path)
        
        # 构建后端完整路径
        ctrl_base_clean = ctrl_base.rstrip('/').lower()
        method_path = ""
        
        for ann in method_annotations:
            m = re.search(r'\(["\']([^"\']*)["\']\)', ann)
            if m:
                method_path = m.group(1).rstrip('/').lower()
                break
            elif '()' in ann:
                method_path = ""
                break
        
        # 组合后端路径
        if ctrl_base_clean and method_path:
            combined_backend = (ctrl_base_clean + '/' + method_path).rstrip('/')
        elif ctrl_base_clean:
            combined_backend = ctrl_base_clean.rstrip('/')
        elif method_path:
            combined_backend = method_path.rstrip('/')
        else:
            combined_backend = ""
        
        # 精确匹配
        if combined_backend and (normalized_req.endswith(combined_backend) or normalized_req == combined_backend):
            return "exact", MATCH_THRESHOLD_EXACT
        
        # 包含匹配
        if combined_backend and combined_backend in normalized_req:
            return "contains", MATCH_THRESHOLD_CONTAINS
        
        # 模块名匹配
        path_parts = match_path.strip('/').split('/')
        significant_parts = [p for p in path_parts if p not in API_PREFIXES_TO_STRIP]
        
        if significant_parts:
            module_part = significant_parts[0]
            # 这里需要传入 controller_class 来判断，简化处理返回低分
            return "module", MATCH_THRESHOLD_MODULE
        
        return None, 0
    
    @staticmethod
    def should_accept(score: int) -> bool:
        """判断是否接受该匹配"""
        return score >= MIN_CONFIDENCE
