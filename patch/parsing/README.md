# Parsing Module

**创建日期**: 2025-02-15

## 📋 目的

这个模块是为了**重构导入逻辑**而创建的，将 PGN 和 FEN 解析功能从旧的 `patch/pgn/` 模块中分离出来。

## 🎯 设计目标

### **1. 模块化**
- ✅ 独立的 FEN 导入逻辑 (`fen_import.ts`)
- 🔜 独立的 PGN 导入逻辑 (`pgn_import.ts`)
- 🔜 共享的类型定义 (`types.ts`)
- 🔜 共享的验证工具 (`validators.ts`)

### **2. 清晰的职责分离**
```
patch/parsing/
├── README.md           # 本文件
├── types.ts            # 共享类型定义
├── validators.ts       # FEN/PGN 验证工具
├── fen_import.ts       # FEN 导入功能
└── pgn_import.ts       # PGN 导入功能（未来）
```

### **3. 向后兼容**
- `patch/pgn/import.ts` 将逐步被废弃
- 新代码应使用 `patch/parsing/` 中的模块
- 迁移过程中保持现有功能正常工作

## 📦 模块说明

### **fen_import.ts**
FEN (Forsyth-Edwards Notation) 导入功能

**功能**：
- ✅ 验证 FEN 字符串格式
- ✅ 创建空 StudyTree（只有 root node）
- ✅ 返回 `starting_fen` 供 Chapter metadata 使用
- ✅ 支持任意棋局位置（残局、中局训练等）

**使用示例**：
```typescript
import { importFromFen } from './parsing/fen_import';

const result = importFromFen('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1');

if (result.success) {
  // 保存到 chapter
  const chapter = await createChapter({
    title: 'Endgame Practice',
    starting_fen: result.startingFen,
    tree: result.tree
  });
}
```

### **pgn_import.ts** (未来)
PGN (Portable Game Notation) 导入功能

**计划功能**：
- 🔜 使用 `@mliebelt/pgn-parser` 解析 PGN
- 🔜 支持 variations（变化分支）
- 🔜 支持 comments（注释）
- 🔜 支持 NAGs（!, ?, !!, ?? 等符号）
- 🔜 构建完整的 StudyTree

**详见**：`/fen_import.md` Phase 2+

## 🔄 迁移计划

### **Phase 1: FEN Import** ✅ 进行中
- [x] 创建 `parsing/` 目录结构
- [x] 实现 `fen_import.ts`
- [x] 实现 `types.ts`
- [ ] 实现 `validators.ts`
- [ ] 集成到 `studyContext.tsx`

### **Phase 2: PGN Import with Variations** 🔜 计划中
- [ ] 研究 `@mliebelt/pgn-parser`
- [ ] 实现 `pgn_import.ts`
- [ ] 支持 variations 解析
- [ ] 支持 comments 解析
- [ ] 支持 NAGs 解析

### **Phase 3: 废弃旧模块** 🔜 未来
- [ ] 迁移所有使用 `patch/pgn/import.ts` 的代码
- [ ] 添加 deprecation 警告
- [ ] 最终删除 `patch/pgn/` 模块

## 📚 参考资料

- **FEN 格式**: https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation
- **PGN 标准**: http://www.saremba.de/chessgml/standards/pgn/pgn-complete.htm
- **Lichess 实现**: `/lichess_pgn_fen.md`
- **实施计划**: `/fen_import.md`

## ⚠️ 注意事项

### **当前限制**
- ❌ 旧的 `patch/pgn/import.ts` 只支持 mainline（不支持 variations）
- ❌ 旧的 `patch/pgn/import.ts` 不解析 comments
- ❌ 旧的 `patch/pgn/import.ts` 不解析 NAGs

### **新模块优势**
- ✅ 清晰的模块边界
- ✅ 更好的类型安全
- ✅ 易于测试
- ✅ 易于扩展

## 📝 开发指南

### **添加新的导入格式**
1. 在 `patch/parsing/` 创建新文件 `{format}_import.ts`
2. 导出统一的接口 `ImportResult`
3. 在 `types.ts` 中添加相关类型
4. 在 `validators.ts` 中添加验证逻辑
5. 更新本 README

### **代码规范**
- ✅ 使用 TypeScript strict mode
- ✅ 导出明确的类型定义
- ✅ 编写单元测试 (`*.test.ts`)
- ✅ 提供清晰的错误消息
- ✅ 遵循函数式编程风格（纯函数，不可变数据）

---

**维护者**: Claude Code
**最后更新**: 2025-02-15
**版本**: 1.0.0
