# 数币工程验证测试 - 全链路分析报告

**分析时间**: 2026-04-16T01:47:29.786013
**后端路径**: ./demo-backend
**前端路径**: ./demo-frontend

## 📊 统计概览

- **controllers_count**: 2
- **services_count**: 2
- **mappers_count**: 2
- **entities_count**: 2
- **vue_components_count**: 2
- **full_chains_count**: 8
- **high_confidence_chains**: 0
- **medium_confidence_chains**: 8
- **low_confidence_chains**: 0

## 💾 数据源配置

- **类型**: mysql
- **URL**: jdbc:mysql://localhost:3306/demo_db?useSSL=false&serverTimezone=UTC
- **用户名**: root

## 🔗 全链路追踪

### CHAIN_0001

**业务功能**: OrderList.loadOrders
**置信度**: 66.7%

- 🖥️ **前端组件**: `OrderList`
  - 文件：`demo-frontend/src/components/OrderList.vue`
  - 函数：`loadOrders`
- 🌐 **API**: `GET /api/order/list`
- 🎮 **Controller**: `OrderController`
  - 文件：`demo-backend/src/main/java/com/example/demo/controller/OrderController.java`
- ⚙️ **Service**: `OrderServiceImpl`
  - 文件：`demo-backend/src/main/java/com/example/demo/service/OrderServiceImpl.java`
- 🗂️ **Mapper**: `OrderMapper`
  - 文件：`demo-backend/src/main/java/com/example/demo/mapper/OrderMapper.java`

### CHAIN_0002

**业务功能**: OrderList.deleteOrder
**置信度**: 66.7%

- 🖥️ **前端组件**: `OrderList`
  - 文件：`demo-frontend/src/components/OrderList.vue`
  - 函数：`deleteOrder`
- 🌐 **API**: `GET /api/order/{id}`
- 🎮 **Controller**: `OrderController`
  - 文件：`demo-backend/src/main/java/com/example/demo/controller/OrderController.java`
- ⚙️ **Service**: `OrderServiceImpl`
  - 文件：`demo-backend/src/main/java/com/example/demo/service/OrderServiceImpl.java`
- 🗂️ **Mapper**: `OrderMapper`
  - 文件：`demo-backend/src/main/java/com/example/demo/mapper/OrderMapper.java`

### CHAIN_0003

**业务功能**: UserList.loadUsers
**置信度**: 66.7%

- 🖥️ **前端组件**: `UserList`
  - 文件：`demo-frontend/src/components/UserList.vue`
  - 函数：`loadUsers`
- 🌐 **API**: `GET /api/user/list`
- 🎮 **Controller**: `UserController`
  - 文件：`demo-backend/src/main/java/com/example/demo/controller/UserController.java`
- ⚙️ **Service**: `UserServiceImpl`
  - 文件：`demo-backend/src/main/java/com/example/demo/service/UserServiceImpl.java`
- 🗂️ **Mapper**: `UserMapper`
  - 文件：`demo-backend/src/main/java/com/example/demo/mapper/UserMapper.java`

### CHAIN_0004

**业务功能**: UserList.deleteUser
**置信度**: 66.7%

- 🖥️ **前端组件**: `UserList`
  - 文件：`demo-frontend/src/components/UserList.vue`
  - 函数：`deleteUser`
- 🌐 **API**: `GET /api/user/{id}`
- 🎮 **Controller**: `UserController`
  - 文件：`demo-backend/src/main/java/com/example/demo/controller/UserController.java`
- ⚙️ **Service**: `UserServiceImpl`
  - 文件：`demo-backend/src/main/java/com/example/demo/service/UserServiceImpl.java`
- 🗂️ **Mapper**: `UserMapper`
  - 文件：`demo-backend/src/main/java/com/example/demo/mapper/UserMapper.java`

### CHAIN_0005

**业务功能**: Backend API: REQUEST /api/order/api/order
**置信度**: 50.0%

- 🌐 **API**: `REQUEST /api/order/api/order`
- 🎮 **Controller**: `OrderController`
  - 文件：`demo-backend/src/main/java/com/example/demo/controller/OrderController.java`
- ⚙️ **Service**: `OrderServiceImpl`
  - 文件：`demo-backend/src/main/java/com/example/demo/service/OrderServiceImpl.java`
- 🗂️ **Mapper**: `OrderMapper`
  - 文件：`demo-backend/src/main/java/com/example/demo/mapper/OrderMapper.java`

### CHAIN_0006

**业务功能**: Backend API: GET /api/order/user/{userId}
**置信度**: 50.0%

- 🌐 **API**: `GET /api/order/user/{userId}`
- 🎮 **Controller**: `OrderController`
  - 文件：`demo-backend/src/main/java/com/example/demo/controller/OrderController.java`
- ⚙️ **Service**: `OrderServiceImpl`
  - 文件：`demo-backend/src/main/java/com/example/demo/service/OrderServiceImpl.java`
- 🗂️ **Mapper**: `OrderMapper`
  - 文件：`demo-backend/src/main/java/com/example/demo/mapper/OrderMapper.java`

### CHAIN_0007

**业务功能**: Backend API: REQUEST /api/user/api/user
**置信度**: 50.0%

- 🌐 **API**: `REQUEST /api/user/api/user`
- 🎮 **Controller**: `UserController`
  - 文件：`demo-backend/src/main/java/com/example/demo/controller/UserController.java`
- ⚙️ **Service**: `UserServiceImpl`
  - 文件：`demo-backend/src/main/java/com/example/demo/service/UserServiceImpl.java`
- 🗂️ **Mapper**: `UserMapper`
  - 文件：`demo-backend/src/main/java/com/example/demo/mapper/UserMapper.java`

### CHAIN_0008

**业务功能**: Backend API: GET /api/user/username/{username}
**置信度**: 50.0%

- 🌐 **API**: `GET /api/user/username/{username}`
- 🎮 **Controller**: `UserController`
  - 文件：`demo-backend/src/main/java/com/example/demo/controller/UserController.java`
- ⚙️ **Service**: `UserServiceImpl`
  - 文件：`demo-backend/src/main/java/com/example/demo/service/UserServiceImpl.java`
- 🗂️ **Mapper**: `UserMapper`
  - 文件：`demo-backend/src/main/java/com/example/demo/mapper/UserMapper.java`

## 🎮 Controllers

### OrderController
- **包**: com.example.demo.controller
- **基础路径**: /api/order
- **端点**: 6
  - `REQUEST /api/order/api/order`
  - `GET /api/order/{id}`
  - `GET /api/order/user/{userId}`
  - `GET /api/order/list`
  - `PUT /api/order/{id}`
  - `DELETE /api/order/{id}`

### UserController
- **包**: com.example.demo.controller
- **基础路径**: /api/user
- **端点**: 6
  - `REQUEST /api/user/api/user`
  - `GET /api/user/{id}`
  - `GET /api/user/list`
  - `PUT /api/user/{id}`
  - `DELETE /api/user/{id}`
  - `GET /api/user/username/{username}`

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
- **文件**: demo-frontend/src/components/OrderList.vue
- **API 调用数**: 2
**函数列表**:
- `loadOrders` (1 API calls)
- `deleteOrder` (1 API calls)

### UserList
- **文件**: demo-frontend/src/components/UserList.vue
- **API 调用数**: 2
**函数列表**:
- `loadUsers` (1 API calls)
- `deleteUser` (1 API calls)

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
