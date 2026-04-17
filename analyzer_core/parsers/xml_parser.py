# -*- coding: utf-8 -*-
"""
MyBatis XML 解析器
"""
import os
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class XmlMapperParser:
    """MyBatis XML 解析器"""
    
    def __init__(self):
        self.namespace_pattern = re.compile(r'mapper\s+namespace=["\']([^"\']+)["\']')
        self.select_pattern = re.compile(r'<select[^>]*>([\s\S]*?)</select>')
        self.insert_pattern = re.compile(r'<insert[^>]*>([\s\S]*?)</insert>')
        self.update_pattern = re.compile(r'<update[^>]*>([\s\S]*?)</update>')
        self.delete_pattern = re.compile(r'<delete[^>]*>([\s\S]*?)</delete>')
        self.table_pattern = re.compile(r'(?:FROM|INTO|UPDATE|JOIN)\s+[`"\']?(\w+)[`"\']?', re.IGNORECASE)

    def parse_xml(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {}
            
        ns_match = self.namespace_pattern.search(content)
        if not ns_match:
            return {}
        namespace = ns_match.group(1)
        
        operations = set()
        tables = set()
        
        for pattern, op in [
            (self.select_pattern, "SELECT"),
            (self.insert_pattern, "INSERT"),
            (self.update_pattern, "UPDATE"),
            (self.delete_pattern, "DELETE")
        ]:
            for match in pattern.finditer(content):
                operations.add(op)
                sql_content = match.group(1)
                for tbl_match in self.table_pattern.finditer(sql_content):
                    tables.add(tbl_match.group(1))
                    
        return {
            "namespace": namespace,
            "operations": list(operations),
            "tables": list(tables),
            "xml_file": os.path.abspath(file_path)
        }
