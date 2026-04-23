# -*- coding: utf-8 -*-
"""
JSON 导出器
"""
import json
import os
from datetime import datetime
from typing import List
import logging

from .models import BusinessChain
from .config import DEFAULT_PROJECT_NAME

logger = logging.getLogger(__name__)


class JsonExporter:
    """JSON 导出器"""
    
    def __init__(self, project_name: str = DEFAULT_PROJECT_NAME):
        self.project_name = project_name
    
    def export(self, chains: List[BusinessChain], output_file: str, frontend_analysis: dict = None):
        """导出 JSON 报告"""
        data = {
            "project_name": self.project_name,
            "analysis_time": datetime.now().isoformat(),
            "summary": {
                "total_chains": len(chains),
                "high_confidence_chains": sum(1 for c in chains if c.confidence >= 80)
            },
            "frontend_analysis": frontend_analysis or {},
            "business_modules": [],
            "business_chains": []
        }
        
        # 按置信度排序
        chains.sort(key=lambda x: x.confidence, reverse=True)
        
        # 构建业务模块
        business_modules = {}
        for i, chain in enumerate(chains):
            chain_id = f"chain_{i:03d}"
            item = {
                "id": chain_id,
                "business_function": chain.business_function,
                "business_module": chain.business_module,
                "front_end_request": chain.front_end_request,
                "back_end_api": chain.back_end_api,
                "services": chain.services,
                "storage_access": chain.storage_access,
                "affected_code_paths": chain.code_paths,
                "confidence": chain.confidence,
                "confidence_level": "高" if chain.confidence >= 80 else "中" if chain.confidence >= 60 else "低"
            }
            data["business_chains"].append(item)
            
            # 构建业务模块
            module_name = chain.business_module
            if module_name not in business_modules:
                business_modules[module_name] = {
                    "name": module_name,
                    "description": "",
                    "routes": [],
                    "business_chains": []
                }
            business_modules[module_name]["business_chains"].append(chain_id)
        
        # 添加业务模块到数据
        data["business_modules"] = list(business_modules.values())
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"报告已保存至：{output_file}")
