# Classroom Workspace Folder 联动

## 目的

老师在 workspace 里自动获得一个统一的学生管理目录，无需手动整理。
每个学生对应一个子文件夹，老师可以在里面放针对该学生的材料，也可以查看学生 share 过来的内容。

---

## 目录结构

```
My Classroom/               ← 老师 workspace 根目录下，所有班级共享这一个入口
  {student_username}/       ← 每个学生一个文件夹，跨班级去重（同一学生只建一次）
  {student_username}/
  ...
```

**不按班级划分**，直接按学生。原因：
- 一个学生可能同时在老师的多个班级，重复建目录没有意义。
- 老师管理学生内容时，关心的是"这个学生"，不是"这个班的这个学生"。

---

## 数据存储

| 字段 | 位置 | 含义 |
|------|------|------|
| `workspace_folder_id` | `classrooms` 表 | 老师的 `My Classroom/` 根目录 node_id（同一老师所有班级共享同一个值） |
| `workspace_folder_id` | `classroom_members` 表 | 该学生的子文件夹 node_id |

### 根目录复用逻辑

老师创建第二个班时，先查该老师已有班级是否存在 `workspace_folder_id`，有则直接复用，不重复创建 `My Classroom/`。

### 学生文件夹去重逻辑

同一老师的多个班级里出现同一个学生时，先查该老师名下是否已有该学生的 `workspace_folder_id`（跨 classroom 查 members 表），有则复用，不重复创建。

---

## Sharing 语义

- **classroom-scoped share**：学生在 classroom 内选择"share with teacher"，内容进入 `My Classroom/{student_username}/`。
- **normal workspace share**：学生直接 share 节点给老师账号，走正常 workspace share 流程，**不进这个目录**。

两套系统完全独立，互不干扰。

---

## 老师重命名学生文件夹

老师可以把 `{student_username}` 文件夹改成学生真名（如 `Alice Chen`）。

- 端点：`PATCH /classrooms/{id}/members/{username}/folder`
- Body：`{ "title": "新名字" }`
- 后端调 workspace `PUT /api/v1/workspace/nodes/{node_id}`（已有接口）
- **只改 workspace 文件夹标题，classroom_members 表的 username 不变**

---

## 触发时机

| 事件 | 操作 |
|------|------|
| 老师创建第一个班级 | 创建 `My Classroom/` 根目录，存 `classroom.workspace_folder_id` |
| 老师创建后续班级 | 查已有班级复用根目录 ID，直接存到新 classroom |
| 学生通过邀请码加入 / 被老师手动添加 | 查是否已有该学生文件夹；没有则在 `My Classroom/` 下创建，存 `member.workspace_folder_id` |
| 老师重命名学生文件夹 | 调 workspace PATCH，只改标题，不动 DB |

---

## 实现文件

| 文件 | 改动 |
|------|------|
| `services/workspace_sync.py` | 改 `sync_create_classroom_folder` → 查复用逻辑；加 `sync_rename_student_folder` |
| `api/endpoints/classrooms.py` | 创建班级时传入 teacher_uuid，复用根目录 |
| `api/endpoints/members.py` | 加入/添加学生时跨班查重；新增 `PATCH .../folder` 端点 |

---

## 不做的事（V1 append-only 原则）

- 不自动删除文件夹（学生被移除时文件夹保留，防止数据丢失）
- 不自动跟随班级改名（workspace 文件夹名由老师手动控制）
- 不处理老师转移班级所有权后的文件夹归属问题
