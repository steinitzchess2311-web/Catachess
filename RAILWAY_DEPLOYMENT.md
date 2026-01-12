# Railway 部署说明

## 问题诊断

如果遇到以下错误：
```
ValueError: invalid literal for int() with base 10: 'port'
FATAL:  password authentication failed for user "postgres"
FATAL:  database "railway'" does not exist
```

**原因**：Railway 环境变量中的 `DATABASE_URL` 包含了占位符文本（如 `postgresql://user:password@host:port/database`），而不是实际的数据库连接信息。

## 解决方案

### 方法 1：使用 Railway PostgreSQL 插件（推荐）

1. 在 Railway 项目控制台中，点击 "New" → "Database" → "Add PostgreSQL"
2. Railway 会自动创建 PostgreSQL 数据库并设置 `DATABASE_URL` 环境变量
3. **重要**：删除任何手动设置的 `DATABASE_URL` 变量，使用 Railway 自动提供的版本
4. 重新部署应用

### 方法 2：使用外部数据库

如果你想使用外部 PostgreSQL 数据库（如 Railway 提供的共享数据库），需要手动设置 `DATABASE_URL`：

1. 在 Railway 项目设置中，进入 "Variables" 选项卡
2. 添加或更新 `DATABASE_URL` 环境变量，格式：
   ```
   postgresql://用户名:密码@主机:端口/数据库名
   ```

   **示例**：
   ```
   postgresql://postgres:mypassword@yamabiko.proxy.rlwy.net:20407/railway
   ```

3. **确保值中不包含占位符文本**（如 "user", "password", "host", "port", "database"）
4. 保存后重新部署

### 方法 3：检查现有环境变量

1. 在 Railway 控制台中，进入项目的 "Variables" 选项卡
2. 检查 `DATABASE_URL` 的值
3. 如果值类似 `postgresql://user:password@host:port/database`，说明是占位符
4. 需要替换为实际的数据库连接信息

## 必需的环境变量

在 Railway 部署时，请确保设置以下环境变量：

### 核心变量（必需）
```bash
DATABASE_URL=postgresql://实际用户名:实际密码@实际主机:实际端口/实际数据库名
JWT_SECRET_KEY=你的安全密钥（生产环境必须更改）
```

### 可选变量
```bash
ENV=production
DEBUG=false
ENGINE_URL=http://your-engine-url:8001
ENGINE_TIMEOUT=60
```

### R2 存储（如使用 workspace 模块）
```bash
R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com
R2_ACCESS_KEY=你的访问密钥
R2_SECRET_KEY=你的密钥
R2_BUCKET=workspace
```

## 验证部署

部署后，应用会自动验证 `DATABASE_URL`：
- 如果包含占位符，会在启动时报错并提供详细说明
- 错误日志会显示当前的 DATABASE_URL 值（密码部分会被隐藏）

## 常见问题

### Q: 如何获取 Railway PostgreSQL 的连接信息？

A: Railway 会自动将连接信息注入 `DATABASE_URL` 环境变量，无需手动获取。

### Q: 密码中包含特殊字符怎么办？

A: 需要对密码进行 URL 编码。例如：
- `@` → `%40`
- `:` → `%3A`
- `/` → `%2F`

### Q: 如何验证 DATABASE_URL 是否正确？

A: 可以使用 `psql` 命令测试：
```bash
psql "postgresql://user:pass@host:port/dbname"
```

## 调试建议

1. 检查 Railway 部署日志中的错误信息
2. 确认数据库服务正在运行
3. 验证网络连接（防火墙、安全组设置）
4. 使用 Railway 的 "Logs" 功能查看实时日志

## 联系支持

如果问题仍未解决：
1. 检查 Railway 状态页面：https://railway.app/status
2. 查看 Railway 文档：https://docs.railway.app
3. 在项目仓库提交 issue
