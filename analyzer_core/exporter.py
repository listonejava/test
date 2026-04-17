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
    
    def export(self, chains: List[BusinessChain], output_file: str):
        """导出 JSON 报告"""
        data = {
            "project_name": self.project_name,
            "analysis_time": datetime.now().isoformat(),
            "summary": {
                "total_chains": len(chains),
                "high_confidence_chains": sum(1 for c in chains if c.confidence >= 80)
            },
            "business_chains": []
        }
        
        # 按置信度排序
        chains.sort(key=lambda x: x.confidence, reverse=True)
        
        for chain in chains:
            item = {
                "business_function": chain.business_function,
                "front_end_request": chain.front_end_request,
                "back_end_api": chain.back_end_api,
                "services": chain.services,
                "storage_access": chain.storage_access,
                "受影响代码路径": chain.code_paths
            }
            data["business_chains"].append(item)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"报告已保存至：{output_file}")
