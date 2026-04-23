#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpringBoot + Vue 全链路静态分析工具 (v3.6 - 模块化重构版)
================================================================
主要改进：
  1. 【架构】代码拆分为多个模块，提高可维护性
  2. 【修复】彻底解决 Unicode 转义错误
  3. 【增强】Services 匹配算法优化，减少空数组情况
     - 支持若依框架命名规范 (IUserService -> UserServiceImpl)
     - 包名启发式匹配回退策略
  4. 【保持】完整绝对路径输出
  5. 【保持】纯净 request_path 输出
  6. 【保持】智能路径匹配和置信度评分
================================================================
兼容：Python 3.12 - 3.14
"""

import os
import sys
import argparse
from datetime import datetime
import logging

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer_core import (
    ApiModuleParser, VueParser, JavaParser, XmlMapperParser,
    ChainBuilder, JsonExporter,
    LOG_FORMAT, LOG_LEVEL, DEFAULT_PROJECT_NAME, DEFAULT_OUTPUT_DIR, OUTPUT_DATE_FORMAT,
    EXCLUDE_DIRS
)

# 配置日志
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT, encoding='utf-8')
logger = logging.getLogger(__name__)


class FullChainAnalyzer:
    """全链路分析主控制器"""
    
    def __init__(self, backend_root: str, frontend_root: str):
        self.backend_root = os.path.abspath(backend_root)
        self.frontend_root = os.path.abspath(frontend_root)
        
        # 初始化解析器
        self.java_parser = JavaParser()
        self.xml_parser = XmlMapperParser()
        
        api_root = os.path.join(self.frontend_root, 'src', 'api')
        self.api_module_parser = ApiModuleParser()
        self.api_map = self.api_module_parser.scan_api_directory(api_root)
        
        self.vue_parser = VueParser(self.api_map)
        
        # 数据存储
        self.controllers = []
        self.services = []
        self.mappers = []
        self.entities = []
        self.xml_maps = {}
        self.vue_requests = []
        
    def scan_backend(self):
        """扫描后端"""
        logger.info(f"开始扫描后端目录：{self.backend_root}")
        
        java_files = []
        xml_files = []
        
        for root, dirs, files in os.walk(self.backend_root):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if file.endswith('.java'):
                    java_files.append(os.path.join(root, file))
                elif file.endswith('.xml') and 'mapper' in root.lower():
                    xml_files.append(os.path.join(root, file))
                    
        logger.info(f"发现 {len(java_files)} 个 Java 文件，{len(xml_files)} 个 XML 文件")
        
        for file in java_files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                self.controllers.extend(self.java_parser.parse_controller(file, content))
                self.services.extend(self.java_parser.parse_service(file, content))
                self.mappers.extend(self.java_parser.parse_mapper(file, content))
                self.entities.extend(self.java_parser.parse_entity(file, content))
            except Exception as e:
                logger.warning(f"解析 Java 文件失败 {file}: {e}")
                
        for file in xml_files:
            info = self.xml_parser.parse_xml(file)
            if info and info.get('namespace'):
                self.xml_maps[info['namespace']] = info
                
        logger.info(f"后端分析完成：{len(self.controllers)} Controllers, {len(self.services)} Services, {len(self.mappers)} Mappers")

    def scan_frontend(self):
        """扫描前端"""
        logger.info(f"开始扫描前端目录：{self.frontend_root}")
        
        vue_files = []
        for root, dirs, files in os.walk(self.frontend_root):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if file.endswith('.vue'):
                    vue_files.append(os.path.join(root, file))
                    
        logger.info(f"发现 {len(vue_files)} 个 Vue 文件")
        
        for file in vue_files:
            try:
                reqs = self.vue_parser.parse_vue_file(file)
                self.vue_requests.extend(reqs)
            except Exception as e:
                logger.error(f"解析 Vue 文件出错 {file}: {e}")
            
        logger.info(f"前端分析完成：{len(self.vue_requests)} API Requests Found")

    def build_chains(self):
        """构建业务链路"""
        logger.info("开始构建业务链路...")
        
        chain_builder = ChainBuilder(
            self.controllers,
            self.services,
            self.mappers,
            self.entities,
            self.xml_maps
        )
        
        chains = chain_builder.build(self.vue_requests)
        
        logger.info(f"构建完成：{len(chains)} 条业务链路")
        return chains

    def export_json(self, chains, output_file: str, project_name: str = DEFAULT_PROJECT_NAME, frontend_analysis: dict = None):
        """导出 JSON"""
        exporter = JsonExporter(project_name)
        exporter.export(chains, output_file, frontend_analysis)


def main():
    parser = argparse.ArgumentParser(description="SpringBoot + Vue 全链路静态分析工具")
    parser.add_argument("--backend", required=True, help="后端项目根目录")
    parser.add_argument("--frontend", required=True, help="前端项目根目录")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="输出目录")
    parser.add_argument("--project-name", default=DEFAULT_PROJECT_NAME, help="项目名称")
    
    args = parser.parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    output_file = os.path.join(args.output, f"fullchain_analysis_{datetime.now().strftime(OUTPUT_DATE_FORMAT)}.json")
    
    print(f"\n🚀 开始分析项目：{args.project_name}")
    print(f"   后端路径：{args.backend}")
    print(f"   前端路径：{args.frontend}")
    
    analyzer = FullChainAnalyzer(args.backend, args.frontend)
    
    analyzer.scan_backend()
    analyzer.scan_frontend()
    
    chains = analyzer.build_chains()
    
    analyzer.export_json(chains, output_file, args.project_name, frontend_analysis=None)
    
    print(f"\n✅ 分析完成!")
    print(f"📊 发现业务链路：{len(chains)} 条")
    print(f"⭐ 高置信度链路：{sum(1 for c in chains if c.confidence >= 80)} 条")
    print(f"💾 报告已保存至：{output_file}")


if __name__ == "__main__":
    main()
