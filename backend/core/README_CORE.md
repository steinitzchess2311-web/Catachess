# Core Chess Engine Documentation

## 总体架构 Architecture Overview

Core 是 CataChess 的核心引擎，负责国际象棋规则验证和 PGN 记录。

Core is the chess engine for CataChess, responsible for rule validation and PGN recording.

### 核心原则 Core Principles

1. **纯规则引擎** - Core 仅运行在终端环境，不包含任何样式、UI、前端逻辑
2. **唯一规则裁判** - Core 是唯一规则裁判，任何不合法走法禁止写入
3. **PGN 记录分离** - PGN 仅负责记录，不参与合法性判断
4. **灵活调度** - vari / no_vari 通过调度层随时切换
5. **门面模式** - 前端、网络、用户系统只能调用 Core 暴露的接口

**Core Principles:**
1. **Pure Rule Engine** - Runs in terminal only, no UI/frontend logic
2. **Single Source of Truth** - Core is the only rule arbiter, illegal moves are blocked
3. **Separated PGN Recording** - PGN only records, doesn't validate
4. **Flexible Orchestration** - Switch between vari/no_vari modes via orchestration layer
5. **Facade Pattern** - External systems must use the facade interface

---

## 模块结构 Module Structure

```
backend/core/
├── chess_basic/              # 基础国际象棋引擎
│   ├── constants.py          # 常量定义
│   ├── errors.py             # 异常类型
│   ├── types.py              # 基础类型
│   │
│   ├── utils/                # 工具函数
│   │   ├── square.py         # 格子操作
│   │   ├── fen.py            # FEN 解析
│   │   ├── uci.py            # UCI 解析
│   │   └── san.py            # SAN 生成
│   │
│   ├── rule/                 # 规则引擎
│   │   ├── api.py            # 对外接口
│   │   ├── movegen.py        # 走法生成
│   │   ├── legality.py       # 合法性验证
│   │   ├── apply.py          # 走法应用
│   │   ├── special_moves.py  # 特殊走法
│   │   ├── check.py          # 将军判断
│   │   └── perft.py          # 性能测试
│   │
│   └── pgn/                  # PGN 记录
│       ├── common/           # 通用组件
│       ├── no_vari/          # 主线 PGN
│       └── vari/             # 分支 PGN
│
└── orchestration/            # 调度层
    ├── core_facade.py        # 对外门面
    ├── core_session.py       # 会话控制
    └── policies.py           # 模式策略
```

---

## 使用指南 Usage Guide

### 基本使用 Basic Usage

```python
from backend.core.orchestration import CoreFacade, SessionMode

# 创建 facade Create facade
facade = CoreFacade()

# 创建标准对局会话 Create standard game session
session_id = facade.create_session("game1", mode=SessionMode.STANDARD_GAME)

# 提交走法 Submit moves
facade.submit_move_uci("game1", "e2e4")
facade.submit_move_uci("game1", "e7e5")

# 获取合法走法 Get legal moves
legal_moves = facade.get_legal_moves("game1")

# 获取 PGN Get PGN
pgn = facade.get_pgn("game1")
print(pgn)
```

### 分析模式 Analysis Mode

```python
# 创建分析会话（支持分支和悔棋）
# Create analysis session (with variations and takebacks)
session_id = facade.create_session("analysis1", mode=SessionMode.ANALYSIS)

facade.submit_move_uci("analysis1", "e2e4")
facade.submit_move_uci("analysis1", "c7c5")

# 悔棋 Takeback
facade.takeback("analysis1")

# 尝试其他走法 Try alternative move
facade.submit_move_uci("analysis1", "e7e5")
```

### 自定义起始位置 Custom Starting Position

```python
# 从 FEN 开始 Start from FEN
custom_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
session_id = facade.create_session("custom1", starting_fen=custom_fen)
```

---

## 红线规定 Red Lines (Do Not Cross)

### ✅ Rule 层允许做什么 What Rule Layer Can Do

- 判断走法是否合法
- 应用合法走法并生成新局面
- 生成所有合法走法
- 检测将军、将死、逼和

### ❌ Rule 层禁止做什么 What Rule Layer Cannot Do

- ❌ **不写 PGN** - 不负责 PGN 记录
- ❌ **不保存文件** - 不进行任何 I/O 操作
- ❌ **不关心用户** - 不涉及用户系统
- ❌ **不关心网络** - 不涉及网络通信
- ❌ **不关心时间** - 不处理计时
- ❌ **不关心 UI** - 不涉及任何界面逻辑

### ✅ PGN 层允许做什么 What PGN Layer Can Do

- 记录已通过规则的走法
- 支持主线或分支记录
- 管理 PGN 标签
- 序列化为 PGN 字符串

### ❌ PGN 层禁止做什么 What PGN Layer Cannot Do

- ❌ **不判断合法性** - 不验证走法是否合法
- ❌ **不自行推演棋盘** - 不维护棋盘状态
- ❌ **不绕过 Rule** - 必须由 orchestration 调用

### ✅ Orchestration 层允许做什么 What Orchestration Can Do

- 决定是否启用 PGN 及其类型
- 保证调用顺序：rule → pgn
- 管理会话和策略
- 提供对外接口

### ❌ Orchestration 层禁止做什么 What Orchestration Cannot Do

- ❌ **不绕过 rule 写入** - 必须先验证合法性
- ❌ **不混入前端逻辑** - 保持与 UI 解耦

---

## API 参考 API Reference

### CoreFacade

核心门面，外部系统的唯一入口。

**重要：** 前端、网络、用户系统必须通过此接口访问 Core。

#### 方法 Methods

- `create_session(session_id, mode, starting_fen=None, custom_policy=None)` - 创建会话
- `submit_move_uci(session_id, uci)` - 提交 UCI 格式走法
- `submit_move(session_id, move)` - 提交 Move 对象
- `get_legal_moves(session_id)` - 获取所有合法走法（UCI 格式）
- `get_board_state(session_id)` - 获取棋盘状态
- `get_fen(session_id)` - 获取 FEN 字符串
- `get_pgn(session_id)` - 获取 PGN 字符串
- `is_game_over(session_id)` - 检查对局是否结束
- `get_result(session_id)` - 获取对局结果
- `takeback(session_id)` - 悔棋
- `reset_session(session_id, starting_fen=None)` - 重置会话

### SessionMode

会话模式枚举：

- `STANDARD_GAME` - 标准对局（无分支，无悔棋）
- `ANALYSIS` - 分析模式（支持分支和悔棋）
- `PUZZLE` - 谜题模式（支持悔棋，不记录 PGN）
- `STUDY` - 研究模式（支持分支和悔棋）

---

## 测试 Testing

### 运行所有测试 Run All Tests

```bash
pytest tests/chess_basic/ -v
```

### 运行特定测试 Run Specific Tests

```bash
# 基础规则测试 Basic rule tests
pytest tests/chess_basic/test_rule_legal_basic.py -v

# 特殊走法测试 Special moves tests
pytest tests/chess_basic/test_rule_special_moves.py -v

# 将死和逼和测试 Checkmate and stalemate tests
pytest tests/chess_basic/test_rule_checkmate_stalemate.py -v

# FEN 往返测试 FEN roundtrip tests
pytest tests/chess_basic/test_fen_roundtrip.py -v

# PGN 测试 PGN tests
pytest tests/chess_basic/test_pgn_no_vari_end_to_end.py -v
pytest tests/chess_basic/test_pgn_vari_end_to_end.py -v
```

### Perft 验证 Perft Verification

```python
from backend.core.chess_basic.rule.perft import run_perft_tests

# 运行标准 perft 测试 Run standard perft tests
success = run_perft_tests(verbose=True)
```

---

## 潜在风险与防范 Potential Risks and Prevention

### ⚠️ 风险 1：PGN 模块偷偷维护棋盘状态

**防范措施：** PGN Writer 基类明确规定不能维护 BoardState。所有棋盘状态由 CoreSession 管理。

### ⚠️ 风险 2：上层绕过 core_session.submit_move

**防范措施：** CoreFacade 是唯一对外接口，不暴露 Rule 或 PGN 的直接访问。

### ⚠️ 风险 3：vari / no_vari 语义混乱

**防范措施：** 通过 GamePolicy 明确定义每种模式的行为，由 Orchestration 管理切换。

### ⚠️ 风险 4：core 引入用户、计时、网络状态

**防范措施：** Core 严格遵守单一职责原则，只处理规则和记录。时间、用户、网络由外层系统管理。

### ⚠️ 风险 5：规则缺乏最小 end-to-end 测试

**防范措施：** 提供完整的测试套件，包括基础规则、特殊走法、将死逼和、FEN 往返、PGN 生成测试。

---

## 开发注意事项 Development Notes

### 添加新功能时 When Adding New Features

1. **先写测试** - 确保行为符合预期
2. **遵守红线** - 不要越界访问不该访问的模块
3. **更新文档** - 保持文档与代码同步
4. **运行 Perft** - 验证规则正确性

### 调试技巧 Debugging Tips

1. 使用 `board_to_fen()` 检查棋盘状态
2. 使用 `generate_legal_moves()` 查看所有合法走法
3. 使用 `perft_divide()` 调试走法生成问题
4. 使用 `get_pgn()` 验证 PGN 记录

### 性能考虑 Performance Considerations

- Move generation 使用位运算优化（可选）
- BoardState 使用浅拷贝减少开销
- PGN Writer 延迟序列化

---

## 进一步阅读 Further Reading

- [PGN 规范](http://www.saremba.de/chessgml/standards/pgn/pgn-complete.htm)
- [UCI 协议](https://www.chessprogramming.org/UCI)
- [Perft 测试](https://www.chessprogramming.org/Perft)
- [Chess Programming Wiki](https://www.chessprogramming.org/)

---

## 许可证 License

本项目遵循 MIT 许可证。

This project is licensed under the MIT License.
