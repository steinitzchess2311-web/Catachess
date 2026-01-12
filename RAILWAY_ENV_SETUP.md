# Railway 环境变量配置清单

## 🚨 立即修复部署错误

在 Railway 项目的 **Variables** 选项卡中，设置以下环境变量：

### 1. 数据库连接（必需）

```bash
DATABASE_URL=postgresql://postgres:yRuedDjiwzhbrBKDbIDCtCxTMzzRDQTL@postgres.railway.internal:5432/railway
```

**重要**：
- 使用 `postgres.railway.internal` 作为主机名（Railway 内部服务）
- 端口是 `5432`（PostgreSQL 默认端口）
- 确保 Railway 项目中已添加 PostgreSQL 数据库服务

### 2. 安全密钥（必需）

```bash
JWT_SECRET_KEY=你的超级安全密钥_请更改这个值_使用随机字符串
```

**建议**：使用以下命令生成安全密钥
```bash
openssl rand -hex 32
```

### 3. 环境设置（推荐）

```bash
ENV=production
DEBUG=false
```

### 4. 引擎配置（可选，如果你有独立的引擎服务）

```bash
ENGINE_URL=http://你的引擎地址:8001
ENGINE_TIMEOUT=60
ENABLE_MULTI_SPOT=false
```

### 5. R2 存储配置（如使用 workspace 模块）

```bash
R2_ENDPOINT=https://5f5a0298fe2da24a34b1fd0d3f795807.r2.cloudflarestorage.com
R2_ACCESS_KEY=2e32a213937e6b75316c0d4ea8f4a6e1
R2_SECRET_KEY=81b411967073f620788ad66c5118165b3f48f3363d88a558f0822cf0bc551f05
R2_BUCKET=workspace
```

## 📋 快速设置步骤

1. **在 Railway 控制台**：
   - 选择你的项目
   - 进入 "Variables" 选项卡
   - 点击 "New Variable"

2. **添加数据库 URL**（最重要）：
   ```
   变量名：DATABASE_URL
   值：postgresql://postgres:yRuedDjiwzhbrBKDbIDCtCxTMzzRDQTL@postgres.railway.internal:5432/railway
   ```

3. **添加 JWT 密钥**：
   ```
   变量名：JWT_SECRET_KEY
   值：[生成一个随机字符串]
   ```

4. **保存并重新部署**：
   - 点击 "Deploy" 或推送新代码触发部署

## 🔍 验证配置

部署后检查日志：
- ✅ 成功：日志中没有 `ValueError: invalid literal for int()` 错误
- ✅ 成功：日志中没有 `password authentication failed` 错误
- ✅ 成功：应用正常启动，healthcheck 通过

## ⚠️ 常见错误

### 错误 1: `ValueError: invalid literal for int() with base 10: 'port'`
**原因**：DATABASE_URL 包含占位符文本
**解决**：使用上面提供的实际 DATABASE_URL

### 错误 2: `password authentication failed`
**原因**：数据库密码不正确或数据库未创建
**解决**：
1. 确认 Railway 项目中已添加 PostgreSQL 服务
2. 检查密码是否正确
3. 使用 Railway 自动生成的 DATABASE_URL

### 错误 3: `database "railway'" does not exist`
**原因**：DATABASE_URL 格式错误，可能有多余的引号
**解决**：确保 DATABASE_URL 没有多余的引号或转义字符

## 🔐 安全建议

1. **永远不要**在代码仓库中提交真实的密钥和密码
2. **生产环境**必须使用强随机密钥
3. **定期轮换** JWT_SECRET_KEY 和数据库密码
4. 使用 Railway 的 **Secrets** 功能保护敏感信息

## 📞 需要帮助？

如果问题仍未解决：
1. 检查 Railway 部署日志的完整错误信息
2. 确认 PostgreSQL 服务在 Railway 项目中正常运行
3. 验证所有环境变量都已正确设置
