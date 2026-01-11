Claude,你是极其专业的编程者.请按照如下要求撰写工程级代码(要有详细的评注)



一、总体目标

Core 仅运行在终端环境，不包含任何样式、UI、前端逻辑

Core 是唯一规则裁判，任何不合法走法禁止写入

PGN 仅负责记录，不参与合法性判断

vari / no_vari 通过调度层随时切换

前端、网络、用户系统只能调用 Core 暴露的接口

二、核心文件夹架构（精细到文件）
core/
├── __init__.py                         # core 模块入口
├── README_CORE.md                      # core 使用规范与红线说明

├── chess_basic/
│   ├── __init__.py                    # chess_basic 模块声明
│   ├── constants.py                   # 棋盘尺寸、棋子编码、颜色等常量
│   ├── errors.py                      # 非法走法、解析失败等核心异常
│   ├── types.py                       # BoardState、Move、Color 等基础类型定义
│   │
│   ├── utils/
│   │   ├── __init__.py                # 工具子模块入口
│   │   ├── square.py                  # 格子坐标与索引转换工具
│   │   ├── fen.py                     # FEN 解析与序列化
│   │   ├── uci.py                     # UCI 走法解析与生成
│   │   └── san.py                     # SAN 表示法生成（不做合法性判断）
│   │
│   ├── rule/
│   │   ├── __init__.py                # 规则模块入口
│   │   ├── api.py                     # 规则层对外唯一接口
│   │   ├── board_state.py             # 棋盘状态数据结构与初始化
│   │   ├── movegen.py                 # 基础走法生成（不含将军判断）
│   │   ├── legality.py                # 合法性总判断（含王是否被将）
│   │   ├── apply.py                   # 合法走法应用并生成新棋盘状态
│   │   ├── special_moves.py           # 王车易位、升变、吃过路兵规则
│   │   ├── check.py                   # 将军、将死、逼和判断
│   │   └── perft.py                   # 规则正确性与性能验证工具
│   │
│   └── pgn/
│       ├── __init__.py                # PGN 模块入口
│       │
│       ├── common/
│       │   ├── __init__.py            # PGN 通用组件入口
│       │   ├── pgn_types.py           # PGN 相关数据结构定义
│       │   ├── tags.py                # Event、Site 等 PGN 标签管理
│       │   ├── writer_base.py         # PGN Writer 抽象基类
│       │   ├── serialize.py           # PGN 文本序列化逻辑
│       │   └── io.py                  # PGN 字符串/文件输出工具
│       │
│       ├── no_vari/
│       │   ├── __init__.py            # 主线 PGN writer 模块入口
│       │   ├── writer.py              # 不支持分支的 PGN 写入实现
│       │   └── tests_writer_no_vari.py# 主线 PGN 写入测试
│       │
│       └── vari/
│           ├── __init__.py            # 分支 PGN writer 模块入口
│           ├── writer.py              # 支持变化分支的 PGN 写入实现
│           ├── variation_stack.py     # PGN 分支栈与括号管理
│           └── tests_writer_vari.py   # 分支 PGN 写入测试
│
├── orchestration/
│   ├── __init__.py                    # 调度层模块入口
│   ├── core_session.py                # 单局对弈/研究会话控制器
│   ├── core_facade.py                 # core 对外唯一调用门面
│   └── policies.py                   # 比赛/研究等模式策略定义
│



 tests/ tests文件请放在catachess/tests/chess_basic
    ├── __init__.py                    # 测试模块入口
    ├── test_rule_legal_basic.py       # 基础规则合法性测试
    ├── test_rule_special_moves.py     # 特殊走法测试
    ├── test_rule_checkmate_stalemate.py# 将死与逼和测试
    ├── test_pgn_no_vari_end_to_end.py # 主线 PGN 全流程测试
    ├── test_pgn_vari_end_to_end.py    # 分支 PGN 全流程测试
    └── test_fen_roundtrip.py          # FEN 解析与还原测试

三、允许做 / 禁止做（红线）
Rule 层（chess_basic/rule）

✅ 判断走法是否合法

✅ 应用合法走法并生成新局面

❌ 不写 PGN

❌ 不保存文件

❌ 不关心用户、网络、时间、UI

PGN 层（chess_basic/pgn）

✅ 记录已通过规则的走法

✅ 支持主线或分支

❌ 不判断合法性

❌ 不自行推演棋盘

Orchestration 层

✅ 决定是否启用 PGN 及其类型

✅ 保证调用顺序：rule → pgn

❌ 不绕过 rule 写入

❌ 不混入前端逻辑

四、潜在风险（必须提前防）

PGN 模块偷偷维护棋盘状态

上层绕过 core_session.submit_move

vari / no_vari 语义混乱

core 引入用户、计时、网络状态

规则缺乏最小 end-to-end 测试

五、推进 Checklist (完成后明确标注已完成)

✅ 架构完整创建（不写逻辑）- 已完成 2026-01-10
   - chess_basic 完整目录结构已创建
   - 所有模块的 __init__.py 已创建
   - 所有源文件已创建并包含完整的工程级代码和详细评注

✅ Rule 最小可用（能走完棋）- 已完成 2026-01-10
   - 走法生成 (movegen.py) 已实现
   - 合法性判断 (legality.py) 已实现
   - 走法应用 (apply.py) 已实现
   - 将军/将死/逼和判断 (check.py) 已实现
   - 特殊走法 (special_moves.py) 已实现
   - Perft 验证工具 (perft.py) 已实现

✅ CoreSession 固化调用顺序 - 已完成 2026-01-10
   - CoreSession 已实现，确保调用顺序：rule → pgn
   - 红线保障：非法走法永远不会到达 PGN writer

✅ PGN no_vari 可输出完整对局 - 已完成 2026-01-10
   - PGNWriterNoVari 已实现
   - 支持标签管理、走法记录、评注、NAG
   - 可输出完整 PGN 字符串和保存到文件

✅ PGN vari 支持分支结构 - 已完成 2026-01-10
   - PGNWriterVari 已实现
   - VariationStack 已实现分支栈管理
   - 支持多层嵌套分支
   - 可输出带分支的 PGN 字符串

✅ 前端只调用 core_facade - 已完成 2026-01-10
   - CoreFacade 已实现为唯一对外接口
   - 提供完整的会话管理和走法提交功能
   - 支持多种会话模式（标准对局、分析、谜题、研究）

✅ 额外完成项 Additional Completions:
   - 完整的工具模块 (utils/: square, fen, uci, san)
   - 游戏策略系统 (policies.py)
   - 完整的测试套件 (7 个测试文件)
   - 完整的 README_CORE.md 文档
