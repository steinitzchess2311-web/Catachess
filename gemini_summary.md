# Catachess 后端功能与前端接口汇总

本文档汇总了 `backend/modules/workspace` 目前已启用的核心功能及可供前端调用的接口 (Hooks)。

## 1. 后端已启用功能 (Backend Functions)

### 核心 PGN 处理引擎 (PGN Engine)
*   **大型 PGN 解析:** 已从递归改为**迭代 (Iterative)** 实现，支持解析超长对局 (如 150+ 回合) 和深度嵌套变例。
*   **智能裁切 (Smart Clipping):** 支持从棋谱的任意节点 (Move Path) "裁切" 生成新的 PGN。
*   **导出模式:** `Clip`, `No Comment`, `Raw`, `Clean`。
*   **R2 存储集成:** 棋谱文件存储在 R2 对象存储中。

### 学习空间 (Study System)
*   **节点系统 (Node System):** 统一管理 Workspace, Folder, Study。
    *   **Workspace:** 顶层容器。
    *   **Folder:** 支持无限嵌套。
    *   **Study:** 棋谱容器。
    *   *注: 均通过 `/nodes` 接口管理。*
*   **Study & Chapter:** 支持 PGN 导入、自动拆分 (>64 章节)。
*   **变例树编辑:** 支持增删改查、注释 (NAG/Text)、变例提拔。

### 讨论系统 (Discussion System)
*   **上下文相关:** 绑定对象 (Study/Chapter) 或棋步。
*   **嵌套回复:** 支持多级回复。
*   **权限:** Viewer/Commenter/Editor 分级。

### 基础设施
*   **事件总线:** 解耦系统组件。
*   **通知系统:** 事件触发通知。

---

## 2. 代码审查与状态 (Code Review & Status)

### ✅ 已挂载路由 (Active Routers)
以下路由已在 `api/router.py` 中注册，前端可正常调用：
*   `/nodes`: 节点管理 (Workspace/Folder/Study CRUD)。
*   `/studies`: 学习与棋谱操作。
*   `/discussions`: 讨论与评论。
*   `/search`: 全局搜索。
*   `/share`: 权限与分享。
*   `/notifications`: 通知管理。

### ⚠️ 未挂载路由 (Inactive/Missing Routers)
以下功能代码已存在于 `api/endpoints/` 但尚未在 `api/router.py` 中挂载，**前端调用会返回 404**：
*   **版本控制 (Versions):** `api/endpoints/versions.py` (Prefix: `/studies`)
    *   涉及接口: `GET /studies/{id}/versions`, `POST /studies/{id}/rollback` 等。
*   **在线状态 (Presence):** `api/endpoints/presence.py` (Prefix: `/presence`)
    *   涉及接口: `POST /presence/heartbeat`, `GET /presence/{id}`。

---

## 3. 前端可用接口 (Hooks for Frontend)

以下是前端集成的建议写法。

### 📂 节点管理 (Nodes: Workspace/Folder/Study)
**注意:** 后端没有 `/workspaces` 或 `/folders` 路由，所有节点操作统一使用 `/nodes`。

| 功能 | HTTP 方法 | 路径 (Endpoint) | Payload 示例 |
| :--- | :--- | :--- | :--- |
| **创建节点** | `POST` | `/nodes` | `{ "node_type": "workspace"\|"folder", "title": "..." }` |
| **获取节点** | `GET` | `/nodes/{id}` | - |
| **移动节点** | `POST` | `/nodes/{id}/move` | `{ "new_parent_id": "...", "version": 1 }` |
| **软删除** | `DELETE` | `/nodes/{id}` | - |
| **获取子节点** | `GET` | `/nodes/{id}/children` | - |

**Frontend Hook Example:**
```typescript
class WorkspaceApi {
  // ... client setup ...

  createWorkspace(title: string) {
    return this.client.request("POST", "/nodes", { 
      node_type: "workspace", 
      title 
    });
  }

  createFolder(parentId: string, title: string) {
    return this.client.request("POST", "/nodes", { 
      node_type: "folder", 
      parent_id: parentId, 
      title 
    });
  }

  getWorkspace(id: string) {
    return this.client.request("GET", `/nodes/${id}`);
  }
}
```

### ♟️ 棋谱与学习 (Studies)

| 功能 | HTTP 方法 | 路径 (Endpoint) | 描述 |
| :--- | :--- | :--- | :--- |
| **导入 PGN** | `POST` | `/studies/import-pgn` | 导入并创建 Study/Chapters。 |
| **获取详情** | `GET` | `/studies/{id}` | 获取 Study 及章节列表。 |
| **添加着法** | `POST` | `/studies/{sid}/chapters/{cid}/moves` | 添加着法/变例。 |
| **删除着法** | `DELETE` | `/studies/{sid}/chapters/{cid}/moves/{mid}` | 删除着法。 |
| **添加注释** | `POST` | `/studies/{sid}/chapters/{cid}/moves/{mid}/annotations` | 添加 NAG/文本。 |
| **提拔变例** | `PUT` | `/studies/{sid}/chapters/{cid}/variations/{vid}/promote` | 变例转主变。 |
| **裁切/导出** | `POST` | `/studies/{id}/pgn/clip` | 裁切或导出 PGN。 |

### 💬 讨论 (Discussions) & 👥 分享 (Shares)

| 功能 | HTTP 方法 | 路径 (Endpoint) | 描述 |
| :--- | :--- | :--- | :--- |
| **列表** | `GET` | `/discussions` | `?target={id}` |
| **创建** | `POST` | `/discussions` | `{ target_id, title, content }` |
| **分享给用户** | `POST` | `/share/{id}/users` | `{ user_id, permission: "viewer"\|"editor" }` |
| **创建分享链** | `POST` | `/share/{id}/links` | 创建公开分享链接。 |

---

## 4. 修复建议 (Action Items)

1.  **后端:** 修改 `backend/modules/workspace/api/router.py`，挂载 `versions` 和 `presence` 路由。
2.  **前端:** 修改 `WorkspaceApi`，将 `/workspaces` 和 `/folders` 请求重定向到 `/nodes` (带上 `node_type`)。