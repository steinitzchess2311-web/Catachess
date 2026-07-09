# CatPet - Desktop Pet System
Created at: 2026-07-08 22:36 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:36 EDT
Last Modified by: Codex

像素风格的桌面宠物猫，可以在屏幕上自由拖动和互动。

## 功能特性

### ✅ 第一阶段（已完成）
- [x] 基础 Sprite 渲染系统
- [x] 待机动画（idle）
- [x] 鼠标拖拽移动
- [x] 左右方向镜像
- [x] 像素完美渲染

### ✅ 第二阶段（已完成）
- [x] AI 行为状态机
- [x] 随机移动系统
- [x] 行走动画（自动切换）
- [x] 点击交互（唤醒/玩耍）
- [x] 边界检测（不会走出屏幕）
- [x] 多状态切换（idle, walk, sit, sleep, play）
- [x] 平滑移动和方向转换

### 🎯 第三阶段（未来）
- [ ] 音效系统
- [ ] 对话气泡
- [ ] 状态持久化
- [ ] 迷你游戏

## 使用方法

### 基础用法

```tsx
import { CatPet } from '@patch/modules/cats';

function App() {
  return (
    <div>
      <CatPet />
    </div>
  );
}
```

### 自定义配置

```tsx
<CatPet
  initialPosition={{ x: 200, y: 150 }}
  scale={3}
  enableDrag={true}
  onInteraction={(type) => {
    console.log('Interaction:', type);
  }}
/>
```

## Props

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `initialPosition` | `{ x: number, y: number }` | `{ x: 100, y: 100 }` | 初始位置 |
| `scale` | `number` | `3` | 缩放比例（1-4） |
| `enableDrag` | `boolean` | `true` | 是否允许拖拽 |
| `enableAI` | `boolean` | `true` | 是否启用自主行为 |
| `onInteraction` | `(type: string) => void` | - | 交互回调 |

## 文件结构

```
patch/modules/cats/
├── index.ts                # 导出入口
├── CatPet.tsx             # 主组件
├── CatPet.css             # 样式
├── README.md              # 本文档
├── types.ts               # TypeScript 类型
├── assets/
│   └── cat-sprite.png     # 精灵图
├── components/
│   └── Cat.tsx            # 猫咪渲染组件
└── engine/
    ├── SpriteConfig.ts    # Sprite 配置
    ├── BehaviorEngine.ts  # AI 行为引擎
    └── MovementEngine.ts  # 移动引擎
```

## Sprite Sheet 说明

精灵图尺寸：**128x192px** (4列 x 6行)
每帧尺寸：**32x32px**

### 动画映射

| 行 | 动画名 | 帧数 | 说明 |
|----|--------|------|------|
| 0 | idle | 4 | 待机呼吸动画 |
| 1 | walk | 4 | 行走动画 |
| 2 | sleep | 3 | 睡觉动画 |
| 3 | sit | 2 | 坐下动画 |
| 4 | (未用) | 2 | 预留 |
| 5 | play | 2 | 玩耍动画 |

## 技术细节

### 渲染方式
- 使用 CSS background-position 实现 sprite animation
- requestAnimationFrame 控制动画帧率
- CSS transform 实现左右镜像
- 宠物位置通过容器 `translate3d(...)` 直接写入 DOM，避免移动期间每一帧触发 React 重渲染。
- 行为状态机 `start()` 会先清理旧 timeout，避免多次启动叠加自主行为计时器。

### 性能优化
- `image-rendering: pixelated` 保持像素锐利
- `will-change: background-position` 优化动画性能
- React.memo 避免不必要的重渲染
- 长时间移动、下落、拖拽过程避免帧级 `setPosition`。
- 方向和旋转状态有变更 guard，避免相同值在动画帧中重复触发 state setter。

## 开发日志

### 2026-02-07
- ✅ 完成第一阶段开发
- ✅ 实现基础拖拽功能
- ✅ 实现 idle 动画循环
- ✅ 配置 sprite sheet 解析
- ✅ 像素完美渲染

## 作者

CataChess Team - 2026
