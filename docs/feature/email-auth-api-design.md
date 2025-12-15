# Email 认证系统 API 设计文档

## 概述

本文档描述 TabAPI 平台基于 Email 的用户认证系统 API 设计，包括注册、登录、邮箱绑定和密码重置功能。

### 功能范围

| 功能 | 描述 |
|------|------|
| Email 注册 | 用户通过邮箱 + 密码 + 验证码完成注册 |
| 密码登录 | 已注册用户通过邮箱 + 密码登录 |
| 验证码登录 | 用户通过邮箱 + 验证码无密码登录 |
| 邮箱绑定 | OAuth 用户补充邮箱 / 已有用户更换邮箱 |
| 密码重置 | 通过邮箱验证码重置账户密码 |

### 相关数据库表

- `users` - 用户主表
- `user_authentications` - 用户鉴权表（存储 email 密码）
- `verification_codes` - 验证码表

详见 [auth-database-design.md](./auth-database-design.md)

---

## 业务流程设计

### 1. Email 注册流程

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  用户   │────>│ 发送验证码  │────>│ 验证码验证  │────>│ 完成注册   │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                      │                    │                    │
                      v                    v                    v
               检查 email 是否      验证码有效性检查      创建 user 记录
               已被注册            尝试次数检查          创建 authentication
               速率限制检查                              标记验证码已使用
```

**步骤说明：**

1. 用户提交 email，系统检查是否已注册
2. 发送 6 位数字验证码到用户邮箱（purpose=`registration`）
3. 用户提交 email + 验证码 + 密码 + username + nonce + auth_at + signature 完成注册
4. 系统创建用户记录，状态为 `active`（已通过邮箱验证）

**安全字段说明：**

| 字段 | 说明 |
|------|------|
| nonce | 一次性随机数，防止重放攻击 |
| auth_at | 认证时间戳，用于时效性验证 |
| signature | 客户端和服务端针对 `email + nonce + auth_at + purpose` 进行对称加密生成的签名 |

### 2. Email 密码登录流程

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐
│  用户   │────>│ 提交凭证    │────>│ 返回 Token  │
└─────────┘     └─────────────┘     └─────────────┘
                      │                    │
                      v                    v
               验证 email + 密码      生成 JWT Access Token
               检查用户状态          更新 last_used_at
               速率限制检查
```

**步骤说明：**

1. 用户提交 email + password + nonce + auth_at + signature
2. 系统验证凭证，检查用户状态（不能是 `suspended`/`deleted`）
3. 验证成功返回 JWT Token

**安全字段说明：**

| 字段 | 说明 |
|------|------|
| nonce | 一次性随机数，防止重放攻击 |
| auth_at | 认证时间戳，用于时效性验证 |
| signature | 客户端和服务端针对 `email + nonce + auth_at + password` 进行对称加密生成的签名 |

### 3. Email 验证码登录流程

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  用户   │────>│ 发送验证码  │────>│ 验证码验证  │────>│ 返回 Token  │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                      │                    │                    │
                      v                    v                    v
               检查 email 是否存在   验证码有效性检查      生成 JWT Token
               检查用户状态         尝试次数检查          更新 last_used_at
               速率限制检查
```

**步骤说明：**

1. 用户提交 email 请求发送登录验证码
2. 系统发送 6 位数字验证码（purpose=`login`）
3. 用户提交 email + 验证码 + nonce + auth_at + signature 完成登录
4. 系统返回 JWT Token

**安全字段说明：**

| 字段 | 说明 |
|------|------|
| nonce | 一次性随机数，防止重放攻击 |
| auth_at | 认证时间戳，用于时效性验证 |
| signature | 客户端和服务端针对 `email + nonce + auth_at + purpose` 进行对称加密生成的签名 |

### 4. 邮箱绑定流程

#### 4.1 OAuth 用户首次绑定邮箱

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│OAuth用户│────>│ 发送验证码  │────>│ 验证码验证  │────>│ 绑定完成   │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                      │                    │                    │
                      v                    v                    v
               检查 email 未被占用   验证码有效性检查      更新 user.email
               发送验证码到新邮箱                         创建 email authentication
                                                         设置 email_verified_at
```

**前置条件：** 用户已通过 OAuth 登录，当前未绑定 email

**安全字段说明：**

| 字段 | 说明 |
|------|------|
| nonce | 一次性随机数，防止重放攻击 |
| auth_at | 认证时间戳，用于时效性验证 |
| signature | 客户端和服务端针对 `email + nonce + auth_at + purpose` 进行对称加密生成的签名 |

#### 4.2 已有用户更换邮箱

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│已有用户 │────>│ 身份验证    │────>│ 新邮箱验证  │────>│ 更换完成   │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                      │                    │                    │
                      v                    v                    v
               密码验证 或           发送验证码到新邮箱    更新 user.email
               旧邮箱验证码验证      验证新邮箱验证码      更新 authentication
                                                         记录操作日志
```

**步骤说明：**

1. 用户发起更换邮箱请求，需先验证身份（密码 或 发送验证码到旧邮箱）
2. 身份验证通过后，发送验证码到新邮箱
3. 用户提交新邮箱验证码 + nonce + auth_at + signature 完成更换

**安全字段说明：**

| 字段 | 说明 |
|------|------|
| nonce | 一次性随机数，防止重放攻击 |
| auth_at | 认证时间戳，用于时效性验证 |
| signature | 客户端和服务端针对 `email + nonce + auth_at + purpose` 进行对称加密生成的签名 |

### 5. 密码重置流程

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  用户   │────>│ 发送验证码  │────>│ 验证码验证  │────>│ 重置密码   │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                      │                    │                    │
                      v                    v                    v
               检查 email 存在       验证码有效性检查      更新 password_hash
               发送重置验证码        生成重置 Token        使旧 Token 失效
               (purpose=password_reset)
```

**步骤说明：**

1. 用户提交 email 请求重置密码
2. 系统发送验证码（purpose=`password_reset`）
3. 用户提交 email + 验证码 + 新密码 + nonce + auth_at + signature 完成重置
4. 系统更新密码，使该用户所有现有 JWT Token 失效

**安全字段说明：**

| 字段 | 说明 |
|------|------|
| nonce | 一次性随机数，防止重放攻击 |
| auth_at | 认证时间戳，用于时效性验证 |
| signature | 客户端和服务端针对 `email + nonce + auth_at + purpose` 进行对称加密生成的签名 |

---

## API 接口规范

### API 基础信息

- **未授权接口 Base URL**: `/auth/v1` （注册、登录、密码重置等无需登录的接口）
- **授权接口 Base URL**: `/api/v1` （需要登录后访问的接口）
- **Content-Type**: `application/json`
- **认证方式**: Bearer Token (JWT)

### 通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

```json
{
  "code": 40001,
  "message": "Invalid email format",
  "data": null
}
```

---

### 1. 验证码相关 API

#### 1.1 发送验证码

**POST** `/auth/v1/verification-code/send`

发送验证码到指定邮箱，支持多种用途。

**Request Body:**

```json
{
  "email": "user@example.com",
  "purpose": "registration"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 目标邮箱地址 |
| purpose | string | 是 | 用途：`registration`, `login`, `password_reset`, `email_binding`, `email_change` |

**Response (200 OK):**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "expires_in": 600,
    "next_send_available_at": "2024-01-01T00:01:00Z"
  }
}
```

**Schema 定义:**

```python
class VerificationCodePurpose(str, Enum):
    REGISTRATION = "registration"
    LOGIN = "login"
    PASSWORD_RESET = "password_reset"
    EMAIL_BINDING = "email_binding"
    EMAIL_CHANGE = "email_change"

class SendVerificationCodeRequest(BaseModel):
    email: EmailStr
    purpose: VerificationCodePurpose

class SendVerificationCodeResponse(BaseModel):
    expires_in: int = Field(description="验证码有效期（秒）")
    next_send_available_at: datetime = Field(description="下次可发送时间")
```

**错误码:**

| Code | Message | 说明 |
|------|---------|------|
| 40001 | Invalid email format | 邮箱格式不正确 |
| 40002 | Email already registered | 邮箱已注册（仅 registration） |
| 40003 | Email not found | 邮箱未注册（仅 login/password_reset） |
| 40004 | User is suspended | 用户已被停用 |
| 42901 | Rate limit exceeded | 发送频率超限 |

---

### 2. 注册 API

#### 2.1 Email 注册

**POST** `/auth/v1/register/email`

使用邮箱、密码和验证码完成注册。

**Request Body:**

```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecureP@ss123",
  "verification_code": "123456",
  "display_name": "John Doe"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| username | string | 是 | 用户名（3-50字符，字母数字下划线连字符）|
| password | string | 是 | 密码（8-128字符，需包含大小写字母和数字）|
| verification_code | string | 是 | 6位数字验证码 |
| display_name | string | 否 | 显示名称 |

**Response (201 Created):**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user": {
      "uid": "1LY7VK9h7J1",
      "username": "johndoe",
      "email": "user@example.com",
      "display_name": "John Doe",
      "avatar_url": null,
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**Schema 定义:**

```python
class EmailRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(min_length=8, max_length=128)
    verification_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    display_name: str | None = Field(default=None, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

class UserResponse(BaseModel):
    uid: str
    username: str
    email: str
    display_name: str | None
    avatar_url: str | None
    status: str
    created_at: datetime

class AuthTokenResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    expires_in: int
```

**错误码:**

| Code | Message | 说明 |
|------|---------|------|
| 40001 | Invalid email format | 邮箱格式不正确 |
| 40002 | Email already registered | 邮箱已被注册 |
| 40005 | Username already taken | 用户名已被占用 |
| 40006 | Invalid verification code | 验证码无效或已过期 |
| 40007 | Verification code expired | 验证码已过期 |
| 40008 | Too many verification attempts | 验证码尝试次数过多 |
| 40009 | Weak password | 密码强度不足 |

---

### 3. 登录 API

#### 3.1 密码登录

**POST** `/auth/v1/login/password`

使用邮箱和密码登录。

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码 |

**Response (200 OK):**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user": {
      "uid": "1LY7VK9h7J1",
      "username": "johndoe",
      "email": "user@example.com",
      "display_name": "John Doe",
      "avatar_url": null,
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**Schema 定义:**

```python
class PasswordLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
```

**错误码:**

| Code | Message | 说明 |
|------|---------|------|
| 40101 | Invalid credentials | 邮箱或密码错误 |
| 40102 | User not found | 用户不存在 |
| 40103 | User is suspended | 用户已被停用 |
| 40104 | Email not verified | 邮箱未验证 |
| 42901 | Rate limit exceeded | 登录尝试次数超限 |

---

#### 3.2 验证码登录

**POST** `/auth/v1/login/verification-code`

使用邮箱和验证码登录（无密码登录）。

**Request Body:**

```json
{
  "email": "user@example.com",
  "verification_code": "123456"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| verification_code | string | 是 | 6位数字验证码 |

**Response (200 OK):**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user": { ... },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**Schema 定义:**

```python
class VerificationCodeLoginRequest(BaseModel):
    email: EmailStr
    verification_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
```

**错误码:**

| Code | Message | 说明 |
|------|---------|------|
| 40006 | Invalid verification code | 验证码无效 |
| 40007 | Verification code expired | 验证码已过期 |
| 40008 | Too many verification attempts | 验证码尝试次数过多 |
| 40102 | User not found | 用户不存在 |
| 40103 | User is suspended | 用户已被停用 |

---

### 4. 邮箱绑定 API

#### 4.1 绑定邮箱（OAuth 用户）

**POST** `/api/v1/auth/email/bind`

OAuth 登录用户首次绑定邮箱。需要先调用发送验证码接口（purpose=`email_binding`）。

**Request Headers:**

```
Authorization: Bearer <access_token>
```

**Request Body:**

```json
{
  "email": "user@example.com",
  "verification_code": "123456",
  "password": "SecureP@ss123"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 要绑定的邮箱地址 |
| verification_code | string | 是 | 6位数字验证码 |
| password | string | 否 | 设置密码（可选，设置后可用密码登录）|

**Response (200 OK):**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "email": "user@example.com",
    "email_verified_at": "2024-01-01T00:00:00Z"
  }
}
```

**Schema 定义:**

```python
class BindEmailRequest(BaseModel):
    email: EmailStr
    verification_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    password: str | None = Field(default=None, min_length=8, max_length=128)

class BindEmailResponse(BaseModel):
    email: str
    email_verified_at: datetime
```

**错误码:**

| Code | Message | 说明 |
|------|---------|------|
| 40002 | Email already registered | 邮箱已被其他用户注册 |
| 40006 | Invalid verification code | 验证码无效 |
| 40010 | Email already bound | 当前用户已绑定邮箱 |
| 40101 | Unauthorized | 未登录 |

---

#### 4.2 更换邮箱 - 身份验证

**POST** `/api/v1/auth/email/change/verify-identity`

更换邮箱前的身份验证。支持密码验证或旧邮箱验证码验证。

**Request Headers:**

```
Authorization: Bearer <access_token>
```

**Request Body（密码验证）:**

```json
{
  "method": "password",
  "password": "CurrentP@ss123"
}
```

**Request Body（验证码验证）:**

```json
{
  "method": "verification_code",
  "verification_code": "123456"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| method | string | 是 | 验证方式：`password` 或 `verification_code` |
| password | string | 条件 | method=password 时必填 |
| verification_code | string | 条件 | method=verification_code 时必填 |

**Response (200 OK):**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "change_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 600
  }
}
```

**Schema 定义:**

```python
class IdentityVerifyMethod(str, Enum):
    PASSWORD = "password"
    VERIFICATION_CODE = "verification_code"

class VerifyIdentityRequest(BaseModel):
    method: IdentityVerifyMethod
    password: str | None = Field(default=None, min_length=1, max_length=128)
    verification_code: str | None = Field(default=None, min_length=6, max_length=6)

    @model_validator(mode="after")
    def validate_credentials(self):
        if self.method == IdentityVerifyMethod.PASSWORD and not self.password:
            raise ValueError("Password is required when method is password")
        if self.method == IdentityVerifyMethod.VERIFICATION_CODE and not self.verification_code:
            raise ValueError("Verification code is required when method is verification_code")
        return self

class VerifyIdentityResponse(BaseModel):
    change_token: str = Field(description="用于后续更换邮箱的临时 Token")
    expires_in: int = Field(description="Token 有效期（秒）")
```

**错误码:**

| Code | Message | 说明 |
|------|---------|------|
| 40101 | Invalid credentials | 密码错误 |
| 40006 | Invalid verification code | 验证码无效 |
| 40011 | No email authentication | 用户未绑定邮箱登录方式 |

---

#### 4.3 更换邮箱 - 确认新邮箱

**POST** `/api/v1/auth/email/change/confirm`

验证新邮箱并完成更换。需要先通过身份验证获取 `change_token`。

**Request Headers:**

```
Authorization: Bearer <access_token>
```

**Request Body:**

```json
{
  "change_token": "eyJhbGciOiJIUzI1NiIs...",
  "new_email": "new@example.com",
  "verification_code": "123456"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| change_token | string | 是 | 身份验证后获取的 Token |
| new_email | string | 是 | 新邮箱地址 |
| verification_code | string | 是 | 发送到新邮箱的验证码 |

**Response (200 OK):**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "old_email": "old@example.com",
    "new_email": "new@example.com",
    "changed_at": "2024-01-01T00:00:00Z"
  }
}
```

**Schema 定义:**

```python
class ConfirmEmailChangeRequest(BaseModel):
    change_token: str
    new_email: EmailStr
    verification_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")

class ConfirmEmailChangeResponse(BaseModel):
    old_email: str
    new_email: str
    changed_at: datetime
```

**错误码:**

| Code | Message | 说明 |
|------|---------|------|
| 40002 | Email already registered | 新邮箱已被其他用户注册 |
| 40006 | Invalid verification code | 验证码无效 |
| 40012 | Invalid or expired change token | change_token 无效或已过期 |

---

### 5. 密码重置 API

#### 5.1 重置密码

**POST** `/auth/v1/auth/password/reset`

通过邮箱验证码重置密码。需要先调用发送验证码接口（purpose=`password_reset`）。

**Request Body:**

```json
{
  "email": "user@example.com",
  "verification_code": "123456",
  "new_password": "NewSecureP@ss123"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| verification_code | string | 是 | 6位数字验证码 |
| new_password | string | 是 | 新密码（8-128字符）|

**Response (200 OK):**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "reset_at": "2024-01-01T00:00:00Z"
  }
}
```

**Schema 定义:**

```python
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    verification_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

class ResetPasswordResponse(BaseModel):
    reset_at: datetime
```

**错误码:**

| Code | Message | 说明 |
|------|---------|------|
| 40006 | Invalid verification code | 验证码无效 |
| 40007 | Verification code expired | 验证码已过期 |
| 40009 | Weak password | 密码强度不足 |
| 40102 | User not found | 用户不存在 |
| 40011 | No email authentication | 用户未设置密码登录方式 |

---

#### 5.2 修改密码（已登录用户）

**POST** `/api/v1/auth/password/change`

已登录用户修改密码。

**Request Headers:**

```
Authorization: Bearer <access_token>
```

**Request Body:**

```json
{
  "current_password": "CurrentP@ss123",
  "new_password": "NewSecureP@ss123"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| current_password | string | 是 | 当前密码 |
| new_password | string | 是 | 新密码（8-128字符）|

**Response (200 OK):**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "changed_at": "2024-01-01T00:00:00Z"
  }
}
```

**Schema 定义:**

```python
class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        # 同上
        ...
```

**错误码:**

| Code | Message | 说明 |
|------|---------|------|
| 40101 | Invalid credentials | 当前密码错误 |
| 40009 | Weak password | 新密码强度不足 |
| 40011 | No email authentication | 用户未设置密码登录方式 |
| 40013 | Same as current password | 新密码与当前密码相同 |

---

## 安全策略设计

### 1. 验证码安全

#### 1.1 验证码生成规则

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 长度 | 6 位 | 数字验证码 |
| 字符集 | 0-9 | 纯数字，便于用户输入 |
| 生成方式 | 密码学安全随机 | 使用 `secrets.randbelow()` |

#### 1.2 验证码存储

- **哈希存储**: 验证码使用 SHA-256 哈希后存储，数据库不存明文
- **关联数据**: 存储时同时记录 email、purpose、expires_at、IP、User-Agent

#### 1.3 验证码有效期

| 用途 | 有效期 | 说明 |
|------|--------|------|
| registration | 10 分钟 | 注册验证 |
| login | 5 分钟 | 登录验证（更短，安全性更高）|
| password_reset | 10 分钟 | 密码重置 |
| email_binding | 10 分钟 | 邮箱绑定 |
| email_change | 10 分钟 | 邮箱更换 |

#### 1.4 验证码尝试限制

```
max_attempts = 5
```

- 单个验证码最多尝试 5 次
- 超过次数后验证码自动失效
- 每次验证失败 `attempts` 计数 +1

#### 1.5 验证码唯一性

- 同一 email + 同一 purpose 同时只保留一个有效验证码
- 发送新验证码时，自动使旧验证码失效

### 2. 速率限制策略

#### 2.1 验证码发送限制

| 维度 | 限制 | 窗口 | 说明 |
|------|------|------|------|
| 同一 Email | 1 次 | 60 秒 | 防止频繁请求 |
| 同一 Email | 5 次 | 1 小时 | 防止滥用 |
| 同一 IP | 10 次 | 1 小时 | 防止批量攻击 |
| 全局 | 1000 次 | 1 小时 | 系统保护 |

**实现方式**: Redis 滑动窗口计数器

```python
# Redis Key 设计
f"rate_limit:email_send:{email}:minute"    # 60秒窗口
f"rate_limit:email_send:{email}:hour"      # 1小时窗口
f"rate_limit:email_send:ip:{ip}:hour"      # IP 维度
```

#### 2.2 登录尝试限制

| 维度 | 限制 | 窗口 | 处理 |
|------|------|------|------|
| 同一 Email | 5 次 | 15 分钟 | 返回错误，建议使用验证码登录 |
| 同一 Email | 10 次 | 1 小时 | 临时锁定账户 15 分钟 |
| 同一 IP | 20 次 | 15 分钟 | 要求验证码/CAPTCHA |
| 同一 IP | 50 次 | 1 小时 | 临时封禁 IP 1 小时 |

**失败登录计数器**:

```python
# Redis Key 设计
f"login_attempts:{email}:count"
f"login_attempts:ip:{ip}:count"

# 账户锁定状态
f"account_locked:{email}"
```

#### 2.3 验证码验证限制

| 维度 | 限制 | 窗口 | 说明 |
|------|------|------|------|
| 同一验证码 | 5 次 | - | 数据库 attempts 字段 |
| 同一 Email | 10 次 | 15 分钟 | 防止暴力破解 |
| 同一 IP | 30 次 | 15 分钟 | 防止批量尝试 |

### 3. 密码安全策略

#### 3.1 密码强度要求

| 要求 | 说明 |
|------|------|
| 最小长度 | 8 字符 |
| 最大长度 | 128 字符 |
| 必须包含 | 至少一个小写字母 |
| 必须包含 | 至少一个大写字母 |
| 必须包含 | 至少一个数字 |
| 可选 | 特殊字符（提高强度评分）|

#### 3.2 密码存储

- **算法**: bcrypt (cost factor = 12)
- **替代方案**: argon2id（内存硬化，更安全）

```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)
```

#### 3.3 密码历史

- 暂不实现，后续可扩展
- 可在 `user_authentications.provider_data` 中存储最近 N 个密码哈希

### 4. JWT Token 安全

#### 4.1 Token 配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 算法 | HS256 或 RS256 | 对称/非对称加密 |
| 有效期 | 1 小时 | Access Token |
| 刷新机制 | Refresh Token | 有效期 30 天 |

#### 4.2 Token 失效策略

- **密码重置**: 使该用户所有 Token 失效
- **主动登出**: 使当前 Token 失效
- **全部登出**: 使该用户所有 Token 失效

**实现方式**: Token 黑名单 (Redis) 或 Token 版本号

```python
# 方案1: Token 黑名单
f"token_blacklist:{jti}"

# 方案2: 用户 Token 版本
f"user_token_version:{user_id}"  # 版本号，重置时 +1
```

### 5. 防御措施汇总

| 攻击类型 | 防御措施 |
|----------|----------|
| 暴力破解密码 | 登录尝试限制 + 账户锁定 |
| 验证码枚举 | 尝试次数限制 + 哈希存储 |
| 邮箱枚举 | 统一响应消息（避免泄露邮箱是否存在）|
| 重放攻击 | 验证码一次性使用 + Token 过期 |
| CSRF | SameSite Cookie + CSRF Token |
| 时序攻击 | 密码比对使用恒定时间算法 |

---

## 错误码汇总

### 通用错误码 (400xx)

| Code | Message | 说明 |
|------|---------|------|
| 40001 | Invalid email format | 邮箱格式不正确 |
| 40002 | Email already registered | 邮箱已被注册 |
| 40003 | Email not found | 邮箱未注册 |
| 40004 | User is suspended | 用户已被停用 |
| 40005 | Username already taken | 用户名已被占用 |
| 40006 | Invalid verification code | 验证码无效 |
| 40007 | Verification code expired | 验证码已过期 |
| 40008 | Too many verification attempts | 验证码尝试次数过多 |
| 40009 | Weak password | 密码强度不足 |
| 40010 | Email already bound | 已绑定邮箱 |
| 40011 | No email authentication | 未设置邮箱登录方式 |
| 40012 | Invalid or expired change token | 更换 Token 无效或已过期 |
| 40013 | Same as current password | 新旧密码相同 |

### 认证错误码 (401xx)

| Code | Message | 说明 |
|------|---------|------|
| 40101 | Invalid credentials | 凭证无效（密码错误）|
| 40102 | User not found | 用户不存在 |
| 40103 | User is suspended | 用户已被停用 |
| 40104 | Email not verified | 邮箱未验证 |
| 40105 | Token expired | Token 已过期 |
| 40106 | Token invalid | Token 无效 |

### 限流错误码 (429xx)

| Code | Message | 说明 |
|------|---------|------|
| 42901 | Rate limit exceeded | 请求频率超限 |
| 42902 | Account temporarily locked | 账户临时锁定 |
| 42903 | IP temporarily blocked | IP 临时封禁 |

---

## 数据库表关联

本设计基于 [auth-database-design.md](./auth-database-design.md) 中定义的表结构：

### users 表使用

- 注册时创建记录，`status='active'`（已通过邮箱验证）
- `email` 字段存储用户邮箱
- `email_verified_at` 记录邮箱验证时间
- 邮箱更换时更新 `email` 和 `email_verified_at`

### user_authentications 表使用

- Email 注册/绑定时创建记录，`provider_type='email'`
- `provider_user_id` 存储邮箱地址（与 users.email 一致）
- `password_hash` 存储密码哈希
- 密码重置/修改时更新 `password_hash`

### verification_codes 表使用

- 发送验证码时创建记录
- `purpose` 区分用途：`registration`, `login`, `password_reset`, `email_binding`, `email_change`
- `code` 字段建议存储哈希值
- 验证成功后更新 `used_at`
- `attempts` 记录尝试次数
- `context` 可存储设备信息等上下文

---

## 附录

### A. 验证码邮件模板

#### 注册验证码

```
主题: [TabAPI] 您的注册验证码

您好，

您正在注册 TabAPI 账户，验证码为：

{{ code }}

验证码有效期为 10 分钟，请勿泄露给他人。

如果这不是您的操作，请忽略此邮件。

TabAPI 团队
```

#### 登录验证码

```
主题: [TabAPI] 您的登录验证码

您好，

您正在登录 TabAPI，验证码为：

{{ code }}

验证码有效期为 5 分钟，请勿泄露给他人。

如果这不是您的操作，建议您立即修改密码。

TabAPI 团队
```

### B. 配置项清单

```python
# app/modules/auth/config.py

from pydantic_settings import BaseSettings

class AuthConfig(BaseSettings):
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # 验证码
    VERIFICATION_CODE_LENGTH: int = 6
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 10
    VERIFICATION_CODE_LOGIN_EXPIRE_MINUTES: int = 5
    VERIFICATION_CODE_MAX_ATTEMPTS: int = 5

    # 密码
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 128
    BCRYPT_ROUNDS: int = 12

    # 速率限制
    RATE_LIMIT_EMAIL_SEND_PER_MINUTE: int = 1
    RATE_LIMIT_EMAIL_SEND_PER_HOUR: int = 5
    RATE_LIMIT_LOGIN_PER_15MIN: int = 5
    RATE_LIMIT_LOGIN_PER_HOUR: int = 10
    ACCOUNT_LOCK_DURATION_MINUTES: int = 15

auth_settings = AuthConfig()
```

### C. 文件结构

```
tabapi/app/modules/auth/
├── __init__.py
├── config.py              # 认证配置
├── constants.py           # 常量和错误码
├── dependencies.py        # 路由依赖项
├── enums.py               # 枚举定义
├── exceptions.py          # 自定义异常
├── models.py              # SQLAlchemy 模型
├── router.py              # API 路由
├── schemas.py             # Pydantic 模式
├── service.py             # 业务逻辑
└── utils/
    ├── __init__.py
    ├── jwt.py             # JWT 工具
    ├── password.py        # 密码工具
    ├── rate_limit.py      # 速率限制
    ├── uid.py             # UID 生成
    └── verification.py    # 验证码工具
```
