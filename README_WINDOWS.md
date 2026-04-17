# SpringBoot + Vue 全链路静态分析工具 v2.0

## 📋 工具说明

本工具用于对 SpringBoot + Vue 项目进行全链路静态分析，生成 JSON 格式的业务链路报告，支持需求影响性分析和增量开发辅助。

### 分析链路
```
业务功能 → 前端请求 → 后端 API → 服务层 → 存储层 → 数据结构
```

### 输出格式
JSON 文件，包含以下结构：
```json
{
  "business_function": "用户管理",
  "front_end_request": {
    "component": "UserManagement.vue",
    "request_path": "/api/user/management",
    "parameters": ["userId", "action"]
  },
  "back_end_api": {
    "controller": "UserManagementController.java",
    "method": "manageUser(String userId, String action)",
    "dependencies": ["UserService", "PermissionService"]
  },
  "services": [...],
  "storage_access": [...],
  "code_quality": {...},
  "security_vulnerabilities": {...},
  "performance_bottlenecks": {...},
  "受影响代码路径": [...]
}
```

## 🚀 Windows 使用方法

### 方法 1: 双击运行（推荐）

1. **复制文件到 E 盘**
   ```
   E:\workspace-analysis\AI4DC\tools\
   ├── fullchain_analyzer.py    # 主程序
   └── run_analysis.bat         # 批处理脚本
   ```

2. **编辑批处理文件**
   
   用记事本打开 `run_analysis.bat`，修改以下路径：
   ```batch
   SET BACKEND_PATH=E:\workspace-analysis\AI4DC\05 源码\你的后端目录
   SET FRONTEND_PATH=E:\workspace-analysis\AI4DC\05 源码\你的前端目录
   SET OUTPUT_DIR=E:\workspace-analysis\AI4DC\05 源码\analysis_output
   SET PROJECT_NAME=数币工程
   ```

3. **双击运行**
   
   双击 `run_analysis.bat` 即可自动执行分析

### 方法 2: 命令行运行

```cmd
cd E:\workspace-analysis\AI4DC\tools
python fullchain_analyzer.py ^
  --backend "E:\workspace-analysis\AI4DC\05 源码\backend" ^
  --frontend "E:\workspace-analysis\AI4DC\05 源码\frontend" ^
  --output "E:\workspace-analysis\AI4DC\05 源码\output" ^
  --project-name "数币工程"
```

## 📊 输出说明

分析完成后，在输出目录生成 JSON 文件：
- `fullchain_analysis_YYYYMMDD_HHMMSS.json` - 业务全链路分析报告

## 🔍 分析内容

### 前端分析 (Vue)
- ✅ Vue 组件识别
- ✅ axios/API 调用提取
- ✅ 请求路径和参数解析
- ✅ HTTP 方法识别 (GET/POST/PUT/DELETE)

### 后端分析 (SpringBoot)
- ✅ Controller 识别 (@RestController, @Controller)
- ✅ API 端点映射 (@GetMapping, @PostMapping 等)
- ✅ Service 层分析 (@Service)
- ✅ Repository/Mapper 识别 (@Repository, @Mapper)
- ✅ Entity 实体识别 (@Entity, @Table)
- ✅ 依赖注入分析 (@Autowired, @Resource)

### 全链路构建
- ✅ 前后端 API 匹配
- ✅ 服务层依赖追踪
- ✅ 数据库表映射
- ✅ 受影响代码路径生成
- ✅ 置信度评分 (0-100%)

### 代码质量与安全（模拟）
- ✅ SonarQube 问题统计
- ✅ 安全漏洞扫描 (Semgrep, XSS, SQL 注入)
- ✅ 性能瓶颈分析

## ⚙️ 系统要求

- **操作系统**: Windows 10/11
- **Python 版本**: Python 3.12 - 3.14
- **项目类型**: SpringBoot + Vue 项目

## 💡 使用场景

### 1. 需求影响性分析
当需要修改某个业务功能时，通过 JSON 报告可以快速定位：
- 哪些前端组件调用了相关 API
- 涉及哪些后端 Controller、Service、Repository
- 影响哪些数据库表

### 2. 增量开发辅助
开发新功能时，参考现有业务链路的实现模式：
- 前端组件如何组织
- API 设计规范
- 服务层划分
- 数据访问模式

### 3. 代码审查
- 识别未使用的 API 端点
- 发现缺少前端调用的后端代码
- 评估代码质量和安全风险

## ⚠️ 注意事项

1. **路径配置**: 确保批处理文件中的路径与实际项目路径一致
2. **项目结构**: 工具假设标准的 SpringBoot + Vue 项目结构
3. **编码**: 支持 UTF-8 编码的源代码文件
4. **中文路径**: Python 3.12+ 完全支持中文路径

## 🔧 常见问题

**Q: 提示找不到 Python？**  
A: 确保 Python 已安装并添加到系统 PATH，重新安装时勾选"Add Python to PATH"

**Q: 分析结果为空？**  
A: 检查后端和前端路径是否正确，确保包含 Java 和 Vue 源代码

**Q: 置信度较低怎么办？**  
A: 工具使用启发式匹配，可手动检查 JSON 报告中的链路关系

**Q: 如何集成到 CI/CD？**  
A: 可直接调用 `python fullchain_analyzer.py` 命令，解析生成的 JSON 文件

## 📞 技术支持

如有问题，请检查：
1. Python 版本是否为 3.12+
2. 项目路径是否正确
3. 源代码文件编码是否为 UTF-8

---

**版本**: v2.0  
**更新日期**: 2024  
**兼容**: Python 3.12 - 3.14
