# Demo Project - 全链路分析报告

**分析时间**: 2026-04-16T01:42:53.407214
**后端路径**: /workspace/demo-backend
**前端路径**: /workspace/demo-frontend

## 📊 统计概览

- **controllers_count**: 2
- **services_count**: 2
- **mappers_count**: 2
- **entities_count**: 2
- **vue_components_count**: 2
- **full_chains_count**: 0
- **high_confidence_chains**: 0
- **medium_confidence_chains**: 0
- **low_confidence_chains**: 0

## 💾 数据源配置

- **类型**: mysql
- **URL**: jdbc:mysql://localhost:3306/demo_db?useSSL=false&serverTimezone=UTC
- **用户名**: root

## 🔗 全链路追踪

*未找到完整链路*

## 🎮 Controllers

### OrderController
- **包**: com.example.demo.controller
- **基础路径**: /api/order
- **端点**: 0

### UserController
- **包**: com.example.demo.controller
- **基础路径**: /api/user
- **端点**: 0

## ⚙️ Services

### UserServiceImpl
- **包**: com.example.demo.service
- **接口**: 否
- **方法数**: 6

### OrderServiceImpl
- **包**: com.example.demo.service
- **接口**: 否
- **方法数**: 6

## 📦 Entities & Tables

### Order
- **表名**: sys_order
- **字段数**: 5
| 字段名 | 类型 | 列名 |
|--------|------|------|
| orderNo | String | order_no |
| userId | Long | user_id |
| totalAmount | Double | total_amount |
| status | Integer | status |
| createdAt | Date | created_at |

### User
- **表名**: sys_user
- **字段数**: 5
| 字段名 | 类型 | 列名 |
|--------|------|------|
| username | String | username |
| email | String | email |
| password | String | password |
| createdAt | Date | created_at |
| updatedAt | Date | updated_at |

## 🖥️ Vue Components

### OrderList
- **文件**: /workspace/demo-frontend/src/components/OrderList.vue
- **API 调用数**: 0

### UserList
- **文件**: /workspace/demo-frontend/src/components/UserList.vue
- **API 调用数**: 0

## 🔍 需求影响性分析指南

### 如何进行影响性分析

1. **前端变更影响**
   - 修改某个 Vue 组件时，查看其调用的 API
   - 根据 `CHAIN_XXXX` 找到对应的后端服务

2. **后端变更影响**
   - 修改某个 Service 时，查看哪些 Controller 依赖它
   - 根据 `CHAIN_XXXX` 找到对应的前端组件

3. **数据库变更影响**
   - 修改某个表结构时，查看对应的 Entity
   - 根据 `CHAIN_XXXX` 找到使用此 Entity 的所有链路

4. **增量开发辅助**
   - 新增功能时，参考现有相似功能的 `CHAIN_XXXX` 模式
   - 确保新功能的链路完整性（前端→API→Controller→Service→Mapper→Entity→Table）
