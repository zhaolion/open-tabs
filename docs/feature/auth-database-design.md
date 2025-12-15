# 用户认证系统数据库设计

## 概述

本文档描述 TabAPI 平台用户认证系统的数据库设计方案。

### 功能需求

- Email 注册（email + password + 验证码）
- Google OAuth2 登录
- GitHub OAuth 登录
- 管理员/普通用户区分
- 一个用户可绑定多种登录方式

### 设计决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 主键类型 | 自增ID + UID（雪花ID Base62编码）| 内部用id高效，uid对外安全防枚举 |
| 枚举字段 | String + 代码约束 | 避免 PostgreSQL ENUM 的迁移复杂性 |
| 会话管理 | 无状态 JWT | 简单高效，无需会话表 |
| OAuth配置 | 数据库表存储 | 支持运行时动态管理 |
| 审计日志 | 后续迭代 | 先聚焦核心功能 |

---

## 枚举类型（代码约束）

数据库使用 `VARCHAR(20)` 存储，应用代码通过 Python Enum 进行约束验证。

### AuthProviderType - 认证提供商类型

| 值 | 说明 |
|----|------|
| `email` | Email + 密码认证 |
| `google` | Google OAuth |
| `github` | GitHub OAuth |

### VerificationCodePurpose - 验证码用途

| 值 | 说明 |
|----|------|
| `registration` | 注册验证 |
| `login` | 登录验证 |
| `password_reset` | 密码重置 |
| `sensitive_op` | 敏感操作确认 |

### UserStatus - 用户状态

| 值 | 说明 |
|----|------|
| `pending` | 待验证 |
| `active` | 正常 |
| `suspended` | 停用 |
| `deleted` | 已删除 |

### AdminRole - 管理员角色

| 值 | 说明 |
|----|------|
| `super_admin` | 超级管理员 |
| `admin` | 管理员 |
| `moderator` | 版主/协管 |

---

## 数据库表设计

### 1. users - 用户主表

存储用户核心身份信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO_INCREMENT | 内部主键 |
| uid | String(16) | UNIQUE, NOT NULL, INDEX | 对外ID（雪花ID Base62编码）|
| username | String(50) | UNIQUE, NOT NULL, INDEX | 用户名 |
| email | String(255) | UNIQUE, NOT NULL, INDEX | 邮箱地址 |
| display_name | String(100) | NULLABLE | 显示名称 |
| avatar_url | String(500) | NULLABLE | 头像URL |
| status | String(20) | NOT NULL, DEFAULT='pending' | 账户状态 |
| email_verified_at | Timestamp | NULLABLE | 邮箱验证时间 |
| is_admin | Boolean | NOT NULL, DEFAULT=false, INDEX | 是否管理员 |
| metadata | JSONB | DEFAULT={} | 扩展元数据 |
| deleted_at | Timestamp | NULLABLE | 软删除时间 |
| created_at | Timestamp | NOT NULL | 创建时间 |
| updated_at | Timestamp | NOT NULL | 更新时间 |

**索引**:
- `users_uid_key` (UNIQUE): uid
- `users_username_key` (UNIQUE): username
- `users_email_key` (UNIQUE): email
- `idx_users_status_admin`: (status, is_admin)
- `idx_users_email_lower`: lower(email)

**metadata 示例**:
```json
{
  "locale": "zh-CN",
  "timezone": "Asia/Shanghai",
  "feature_flags": {}
}
```

---

### 2. user_authentications - 用户鉴权表

存储用户的各种认证方式，支持一个用户绑定多种登录方式。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO_INCREMENT | 主键 |
| user_id | Integer | FK(users.id), NOT NULL, INDEX | 关联用户 |
| provider_type | String(20) | NOT NULL | 认证类型 |
| provider_user_id | String(255) | NOT NULL | 提供商用户ID |
| password_hash | String(255) | NULLABLE | 密码哈希（仅EMAIL类型） |
| provider_data | JSONB | DEFAULT={} | OAuth令牌和数据 |
| is_primary | Boolean | NOT NULL, DEFAULT=false | 是否主要方式 |
| last_used_at | Timestamp | NULLABLE | 最后使用时间 |
| created_at | Timestamp | NOT NULL | 创建时间 |
| updated_at | Timestamp | NOT NULL | 更新时间 |

**约束与索引**:
- `uq_auth_provider_user`: UNIQUE(provider_type, provider_user_id) - 防止同一OAuth账号绑定多个用户
- `idx_auth_user_primary`: UNIQUE(user_id) WHERE is_primary=true - 每用户仅一个主要认证方式
- `idx_auth_provider_lookup`: (provider_type, provider_user_id) - OAuth登录查询

**provider_data 示例** (OAuth):
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_expires_at": "2024-01-01T00:00:00Z",
  "scope": "email profile",
  "raw_user_info": {
    "name": "User Name",
    "picture": "https://..."
  }
}
```

---

### 3. verification_codes - 验证码表

存储各类验证码，支持注册、登录、密码重置、敏感操作等场景。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO_INCREMENT | 主键 |
| user_id | Integer | FK(users.id), NULLABLE, INDEX | 关联用户（注册前可空）|
| email | String(255) | NOT NULL, INDEX | 目标邮箱 |
| code | String(32) | NOT NULL | 验证码（建议哈希存储）|
| purpose | String(20) | NOT NULL | 用途 |
| expires_at | Timestamp | NOT NULL, INDEX | 过期时间 |
| used_at | Timestamp | NULLABLE | 使用时间 |
| attempts | Integer | NOT NULL, DEFAULT=0 | 尝试次数 |
| max_attempts | Integer | NOT NULL, DEFAULT=5 | 最大尝试次数 |
| ip_address | String(45) | NULLABLE | 请求IP（支持IPv6）|
| user_agent | String(500) | NULLABLE | 用户代理 |
| context | JSONB | DEFAULT={} | 操作上下文 |
| created_at | Timestamp | NOT NULL | 创建时间 |
| updated_at | Timestamp | NOT NULL | 更新时间 |

**索引**:
- `idx_vc_email_purpose`: (email, purpose)
- `idx_vc_code_lookup`: (code, purpose, email)
- `idx_vc_active`: (email, purpose) WHERE used_at IS NULL - 查找未使用的验证码

**context 示例**:
```json
{
  "redirect_url": "/dashboard",
  "action": "delete_account",
  "device_info": {
    "os": "macOS",
    "browser": "Chrome"
  }
}
```

---

### 4. user_admin_profiles - 管理员配置文件表

存储管理员特有的配置信息，与 users 表 1:1 关系。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO_INCREMENT | 主键 |
| user_id | Integer | FK(users.id), UNIQUE, NOT NULL | 关联用户（1:1）|
| role | String(20) | NOT NULL, DEFAULT='moderator' | 管理员角色 |
| permissions | JSONB | NOT NULL, DEFAULT={} | 细粒度权限 |
| preferences | JSONB | NOT NULL, DEFAULT={} | UI偏好设置 |
| last_admin_action_at | Timestamp | NULLABLE | 最后管理操作时间 |
| notes | Text | NULLABLE | 内部备注 |
| granted_by_user_id | Integer | FK(users.id), NULLABLE | 授权人 |
| granted_at | Timestamp | NOT NULL | 授权时间 |
| created_at | Timestamp | NOT NULL | 创建时间 |
| updated_at | Timestamp | NOT NULL | 更新时间 |

**索引**:
- `user_admin_profiles_user_id_key`: UNIQUE(user_id)
- `idx_admin_role`: (role)
- `idx_admin_granted_by`: (granted_by_user_id)

**permissions 示例**:
```json
{
  "users": {"read": true, "write": true, "delete": false},
  "content": {"read": true, "write": true, "delete": true},
  "settings": {"read": true, "write": false},
  "billing": {"read": false, "write": false}
}
```

**preferences 示例**:
```json
{
  "theme": "dark",
  "language": "zh-CN",
  "notifications": {"email": true, "slack": false},
  "dashboard_layout": "compact"
}
```

---

### 5. oauth_provider_configs - OAuth配置表

存储 OAuth 提供商的配置信息，支持运行时动态管理。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO_INCREMENT | 主键 |
| provider | String(20) | UNIQUE, NOT NULL | 提供商类型 |
| display_name | String(100) | NOT NULL | 显示名称 |
| icon_url | String(500) | NULLABLE | 图标URL |
| client_id | String(255) | NOT NULL | OAuth Client ID |
| client_secret_encrypted | String(500) | NOT NULL | 加密的 Client Secret |
| authorization_url | String(500) | NULLABLE | 授权URL |
| token_url | String(500) | NULLABLE | Token URL |
| userinfo_url | String(500) | NULLABLE | 用户信息URL |
| default_scopes | JSONB | DEFAULT=[] | 默认权限范围 |
| config | JSONB | DEFAULT={} | 提供商特定配置 |
| is_enabled | Boolean | NOT NULL, DEFAULT=true | 是否启用 |
| created_at | Timestamp | NOT NULL | 创建时间 |
| updated_at | Timestamp | NOT NULL | 更新时间 |

**索引**:
- `oauth_provider_configs_provider_key`: UNIQUE(provider)
- `idx_oauth_provider_enabled`: (provider, is_enabled)

**config 示例**:
```json
{
  "pkce_enabled": true,
  "state_ttl_seconds": 600,
  "allowed_domains": ["example.com"]
}
```

---

## ER 关系图

```
+------------------+       +------------------------+
|      users       |       | user_authentications   |
+------------------+       +------------------------+
| id (PK)          |<──┬───| user_id (FK)          |
| uid (UQ)         |   │   | provider_type         |
| username (UQ)    |   │   | provider_user_id      |
| email (UQ)       |   │   | password_hash         |
| display_name     |   │   | provider_data (JSONB) |
| avatar_url       |   │   | is_primary            |
| status           |   │   | last_used_at          |
| email_verified_at|   │   +------------------------+
| is_admin         |   │          1:N
| metadata (JSONB) |   │
| deleted_at       |   │   +------------------------+
| created_at       |   ├───| verification_codes     |
| updated_at       |   │   +------------------------+
+------------------+   │   | user_id (FK, nullable)|
        │              │   | email                 |
        │              │   | code                  |
        │  1:1         │   | purpose               |
        v              │   | expires_at            |
+------------------------+ | used_at               |
| user_admin_profiles    | | attempts              |
+------------------------+ | context (JSONB)       |
| user_id (FK, UQ)      | +------------------------+
| role                  |        1:N (nullable)
| permissions (JSONB)   |
| preferences (JSONB)   |
| last_admin_action_at  |  +------------------------+
| notes                 |  | oauth_provider_configs |
| granted_by_user_id(FK)|  +------------------------+
| granted_at            |  | provider (UQ)         |
+------------------------+  | display_name          |
                           | client_id             |
                           | client_secret_encrypted|
                           | is_enabled            |
                           +------------------------+
                                  独立配置表
```

---

## UID 生成方案

使用雪花ID + Base62编码生成用户对外展示的 uid，长度约 11-12 字符。

### 雪花ID结构

```
| 1 bit | 41 bits    | 5 bits      | 5 bits     | 12 bits  |
| 符号  | 时间戳     | 数据中心ID  | 机器ID     | 序列号   |
```

- **时间戳**: 41位，毫秒级，可用约69年
- **数据中心ID**: 5位，支持32个数据中心
- **机器ID**: 5位，每个数据中心支持32台机器
- **序列号**: 12位，每毫秒支持4096个ID

### Base62编码

字符集: `0-9A-Za-z` (62个字符)

示例:
- 雪花ID: `1234567890123456789`
- Base62: `1LY7VK9h7J1`

---

## 文件结构

```
tabapi/app/modules/auth/
├── __init__.py
├── enums.py              # 枚举定义
├── models.py             # SQLAlchemy 模型
├── schemas.py            # Pydantic 验证模式（后续）
├── routes.py             # API 路由（后续）
└── utils/
    ├── __init__.py
    └── uid.py            # UID 生成工具
```

---

## 安全考虑

1. **密码存储**: 使用 bcrypt 或 argon2 哈希算法
2. **验证码**: 建议哈希存储，限制尝试次数
3. **OAuth Token**: 应用层加密存储
4. **Client Secret**: 使用 AES 等对称加密存储
5. **软删除**: 用户数据保留但标记删除，满足合规要求

---

## 后续扩展

本设计预留了以下扩展点：

1. **更多OAuth提供商**: 只需在 AuthProviderType 枚举添加值
2. **角色权限系统**: permissions JSONB 支持细粒度控制
3. **组织/团队**: 可新增 organizations 和 organization_members 表
4. **审计日志**: 可新增 audit_logs 表记录操作历史
5. **MFA/2FA**: 可在 user_authentications 表添加 mfa_secret 字段
