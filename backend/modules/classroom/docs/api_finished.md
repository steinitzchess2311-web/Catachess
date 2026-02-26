# Classroom API — Finished Endpoints

## Classrooms
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/classroom/classrooms` | 创建班级（自动建 catachat 群组和 workspace 文件夹） |
| GET | `/api/classroom/classrooms` | 列出当前用户所有班级（含角色和人数） |
| GET | `/api/classroom/classrooms/{id}` | 获取单个班级详情 |
| PATCH | `/api/classroom/classrooms/{id}` | 修改班级名称（owner/teacher） |
| DELETE | `/api/classroom/classrooms/{id}` | 软删除班级（owner only） |
| POST | `/api/classroom/classrooms/{id}/archive` | 归档班级（owner only） |
| POST | `/api/classroom/classrooms/{id}/unarchive` | 取消归档（owner only） |
| GET | `/api/classroom/classrooms/{id}/invite` | 获取邀请码和开关状态 |
| POST | `/api/classroom/classrooms/{id}/invite/reset` | 重置邀请码（owner/teacher） |
| PATCH | `/api/classroom/classrooms/{id}/invite` | 开关邀请码（owner/teacher） |
| POST | `/api/classroom/classrooms/join` | 通过邀请码加入班级 |
| GET | `/api/classroom/classrooms/{id}/chat` | 获取该班的 catachat 群组 ID |
| POST | `/api/classroom/classrooms/{id}/broadcast` | 向班级 catachat 群发送广播消息（标记 is_broadcast） |
| GET | `/api/classroom/classrooms/{id}/broadcasts` | 列出该班所有广播消息，按时间倒序（任意成员） |
| DELETE | `/api/classroom/classrooms/{id}/broadcasts/{mid}` | 删除指定广播消息（teacher+） |

## Members
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/classroom/classrooms/{id}/members` | 列出班级所有成员（含 owner 合并显示） |
| POST | `/api/classroom/classrooms/{id}/members` | 直接添加成员并指定角色（teacher+） |
| DELETE | `/api/classroom/classrooms/{id}/members/{username}` | 移除成员（teacher+ 可移除 student，owner 可移除 teacher） |
| PATCH | `/api/classroom/classrooms/{id}/members/{username}/role` | 修改成员角色（owner only） |
| POST | `/api/classroom/classrooms/{id}/members/leave` | 当前用户离开班级 |

## Assignments
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/classroom/classrooms/{id}/assignments` | 创建作业/材料/考试（teacher+） |
| GET | `/api/classroom/classrooms/{id}/assignments` | 列出班级所有作业 |
| GET | `/api/classroom/classrooms/{id}/assignments/{aid}` | 获取单个作业详情 |
| PATCH | `/api/classroom/classrooms/{id}/assignments/{aid}` | 修改作业（teacher+） |
| DELETE | `/api/classroom/classrooms/{id}/assignments/{aid}` | 软删除作业（teacher+） |
| GET | `/api/classroom/classrooms/{id}/assignments/{aid}/stats` | 获取作业提交统计（teacher+） |

## Submissions
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/classroom/classrooms/{id}/assignments/{aid}/submissions` | 创建或更新提交（学生） |
| GET | `/api/classroom/classrooms/{id}/assignments/{aid}/submissions` | 列出该作业所有提交（teacher+） |
| GET | `/api/classroom/classrooms/{id}/assignments/{aid}/submissions/me` | 获取自己的提交 |
| GET | `/api/classroom/classrooms/{id}/assignments/{aid}/submissions/{username}` | 获取指定学生的提交（teacher+） |
| GET | `/api/classroom/classrooms/my/todo` | 获取当前学生跨班级待完成作业（含紧急度） |

## Activity
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/classroom/classrooms/{id}/activity` | 获取班级最新提交动态流，按时间倒序（teacher+） |
