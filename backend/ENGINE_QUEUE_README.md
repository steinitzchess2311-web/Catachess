# Engine Request Queue - 防止单用户挤崩网站

## 问题背景

**原有架构缺陷：**
```
HTTP 请求 → Backend → 直接调用 sf.catachess（无限制）
```

**问题：**
- `/api/engine/analyze` 端点没有速率限制
- 每个请求直接调用引擎（450-600ms）
- 一个用户可以发送无限并发请求，挤崩整个后端

## 新架构

```
HTTP 请求
  ↓
Backend（速率限制：30次/分钟/IP）
  ↓
Engine Queue（排队 + 去重）
  ↓
Engine Workers（有限个：默认10个worker）
  ↓
本机 Stockfish / AlphaZero / Lichess Cloud Eval
```

## 核心功能

### 1. **请求排队**
- 所有引擎请求进入 FIFO 队列
- 队列大小无限，但只有有限 worker 并发处理，生产默认 10
- 本机 Stockfish 另有跨进程 slot lock，4 个 gunicorn worker 合计最多 10 个 Stockfish 进程
- 防止同时发送过多请求到本机或外部引擎

### 2. **请求去重**
- 相同的请求（FEN + depth + multipv + engine）自动合并
- 多个用户请求相同位置时，共享同一个引擎调用结果
- 大幅减少重复计算

### 3. **速率限制**
- 每个 IP：30 次请求/分钟
- 超过限制返回 `429 Too Many Requests`
- 可通过环境变量调整

### 4. **完整日志**
- 每个请求的入队、等待、处理时间
- 队列状态（队列长度、活跃 worker 数）
- 统计信息（总请求数、完成数、失败数）

## 配置参数

### 环境变量（.env）

```bash
# 引擎队列配置
ENGINE_QUEUE_MAX_WORKERS=10          # 最大并发 worker 数（不建议超过10）
ENGINE_RATE_LIMIT_PER_MINUTE=30      # 每分钟每 IP 的请求限制（推荐：30-60）
```

### 调整建议

| 场景 | MAX_WORKERS | RATE_LIMIT | 说明 |
|------|-------------|------------|------|
| **低流量** | 2 | 20 | 节省资源，适合开发环境 |
| **中流量** | 5 | 30 | 平衡性能和保护 |
| **高流量（生产上限）** | 10 | 60 | 提高吞吐量，但不允许无限制抢 CPU |
| **严格保护** | 2 | 10 | 防止滥用，适合公开测试 |

## API 端点

### 1. 分析位置（已更新）
```http
POST /api/engine/analyze
```

**速率限制：** 30 次/分钟/IP

**请求体：**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "depth": 20,
  "multipv": 3,
  "engine": "stockfish"
}
```

**响应：**
```json
{
  "lines": [
    {
      "multipv": 1,
      "score": {"type": "cp", "value": 25},
      "pv": ["e2e4", "e7e5", "g1f3"]
    }
  ],
  "source": "LocalStockfish",
  "cache_metadata": {
    "mongodb_hit": false,
    "engine_ms": 542.3,
    "total_ms": 558.1
  }
}
```

### 2. 队列统计（新增）
```http
GET /api/engine/queue/stats
```

**响应：**
```json
{
  "queue_size": 2,              // 当前队列中等待的请求数
  "active_workers": 3,          // 正在处理的 worker 数
  "max_workers": 10,            // 最大 worker 数
  "total_requests": 145,        // 总请求数（自启动以来）
  "total_completed": 140,       // 已完成数
  "total_failed": 3,            // 失败数
  "avg_wait_time_ms": 234.5,    // 平均等待时间（毫秒）
  "avg_processing_time_ms": 512.3  // 平均处理时间（毫秒）
}
```

### 3. 缓存统计（已有）
```http
GET /api/engine/cache/stats
```

## 日志示例

### 正常请求流程

```
[ENGINE ANALYZE] Request started
[ENGINE ANALYZE] FEN: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
[ENGINE ANALYZE] Depth: 20, MultiPV: 3, Engine: sf
[ENGINE ANALYZE] ✗ MongoDB cache MISS - enqueuing to engine queue
[ENGINE QUEUE] Enqueued request | Queue size: 0 | Active workers: 2
[ENGINE QUEUE] Worker 0 processing | Wait time: 5ms | Queue size: 0
[ENGINE QUEUE] Worker 0 completed | Processing time: 542ms | Total wait: 5ms
[ENGINE ANALYZE] Analysis complete
[ENGINE ANALYZE] Total duration: 0.558s
```

### 请求去重

```
[ENGINE QUEUE] Enqueued request | Queue size: 3 | Active workers: 3
[ENGINE QUEUE] Deduplicating request | Key: fen:...|depth:20|multipv:3|engine:sf
[ENGINE QUEUE] Worker 1 completed | Processing time: 489ms
# 两个请求共享同一个结果
```

### 速率限制触发

```
HTTP 429 Too Many Requests
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

## 监控建议

### 1. 实时队列监控

定期查询队列统计：
```bash
# 生产环境
curl https://api.catachess.com/api/engine/queue/stats

# 开发环境
curl http://localhost:8000/api/engine/queue/stats
```

**健康指标：**
- `queue_size < 10`: 队列正常
- `queue_size > 50`: 需要增加 MAX_WORKERS
- `avg_wait_time_ms < 500`: 响应及时
- `total_failed / total_completed < 0.05`: 失败率正常

### 2. 缓存命中率监控

```bash
# 生产环境
curl https://api.catachess.com/api/engine/cache/stats

# 开发环境
curl http://localhost:8000/api/engine/cache/stats
```

**优化建议：**
- 命中率 > 70%: 缓存效果好
- 命中率 < 30%: 考虑增加预计算范围

### 3. 日志分析

查找慢请求：
```bash
grep "Total duration:" backend.log | awk '{if ($NF > 1.0) print}'
```

查找队列积压：
```bash
grep "Queue size:" backend.log | grep -E "Queue size: [0-9]{2,}"
```

## 测试验证

### 1. 压力测试

使用 Apache Bench 测试：
```bash
# 开发环境测试
ab -n 100 -c 10 -p analyze.json -T application/json \
   http://localhost:8000/api/engine/analyze

# 生产环境测试（小心使用！）
ab -n 50 -c 5 -p analyze.json -T application/json \
   https://api.catachess.com/api/engine/analyze
```

**analyze.json:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "depth": 20,
  "multipv": 3,
  "engine": "sf"
}
```

### 2. 速率限制测试

```bash
# 开发环境：发送 50 个请求，超过限制应返回 429
API_URL="http://localhost:8000"  # 或 https://api.catachess.com

for i in {1..50}; do
  curl -X POST $API_URL/api/engine/analyze \
    -H "Content-Type: application/json" \
    -d '{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "depth": 20, "multipv": 3}'
  echo ""
done
```

### 3. 去重测试

同时发送 10 个相同请求，应该只调用 1 次引擎：
```bash
API_URL="http://localhost:8000"  # 或 https://api.catachess.com

for i in {1..10}; do
  (curl -X POST $API_URL/api/engine/analyze \
    -H "Content-Type: application/json" \
    -d '{"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "depth": 25, "multipv": 5}' &)
done
```

## 故障排查

### 问题：队列长度持续增长

**原因：** Worker 数量不足或引擎响应慢

**解决：**
1. 增加 `ENGINE_QUEUE_MAX_WORKERS`（最多 10）
2. 检查本机 Stockfish 或 AlphaZero worker 状态
3. 检查 MongoDB 缓存命中率

### 问题：大量 429 错误

**原因：** 速率限制过严

**解决：**
1. 增加 `ENGINE_RATE_LIMIT_PER_MINUTE` (例如改为 60)
2. 或优化前端，减少重复请求

### 问题：引擎调用失败

**原因：** 本机 Stockfish 不可用、AlphaZero 配置缺失，或外部兜底不可用

**解决：**
1. 检查 `ENGINE_URL` 配置
2. 查看日志中的错误详情
3. 确认 Lichess Cloud Eval 回退是否正常

## 性能优化建议

### 1. 提高缓存命中率
- 前端预计算更多常见位置
- 增加 MongoDB 索引覆盖率

### 2. 调整 Worker 数量
- 根据 sf.catachess 的并发能力调整
- 监控 `avg_processing_time_ms`，如果增加说明引擎过载

### 3. 优化前端请求
- 避免重复请求
- 使用前端缓存（Memory + IndexedDB）
- 延迟预计算启动（`delayMs: 500`）

## 回滚方案

如果新队列系统出现问题，可以临时禁用队列：

```python
# routers/chess_engine.py

# 注释掉队列代码
# result = await engine_queue.enqueue(...)

# 恢复直接调用
result = engine.analyze(
    fen=request.fen,
    depth=request.depth,
    multipv=request.multipv,
    engine=request.engine or 'auto',
)
```

但仍然保留速率限制以防滥用。

## 总结

**修复内容：**
1. ✅ 添加请求队列（3 个 worker 并发）
2. ✅ 添加请求去重（相同请求共享结果）
3. ✅ 添加速率限制（30 次/分钟/IP）
4. ✅ 添加详细日志（每个请求的等待和处理时间）
5. ✅ 添加监控端点（`/api/engine/queue/stats`）
6. ✅ 可配置参数（通过环境变量）

**防护效果：**
- 单用户无法再发送无限并发请求
- 最多 3 个并发引擎调用（可配置）
- 速率限制防止恶意滥用
- 请求去重减少重复计算

**下一步建议：**
1. 部署到生产环境
2. 监控队列统计 1-2 天
3. 根据实际流量调整参数
4. 考虑添加用户级别的限制（已认证用户可以更高限额）
