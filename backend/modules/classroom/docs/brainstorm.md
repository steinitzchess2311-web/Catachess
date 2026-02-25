V1（最小上线）- 不眠不休2 -3 天
1 、建立班级、解散班级。
 2 、班级改名、拉人、踢人、增加管理员。
 3 、班级消息：和 catachat  - 代码：desktop/catachat 联动
 4 、建立班级，老师workspace/shared自动出现班级文件夹，自动整理学生 share 给老师的 study 。
 5 、老师布置train mode作业，学生做。老师端返回学生情况。
6 、日历系统。
7 、老师端消息提示

 V2：-这周前（可同步其他事情）
1 、开局回放 trainer
 2 、开局考试
3 、打谱 trainer - 开局回放和 trainer 的集合
4 、 上传系统。

 V3 - 下周五前（可同步其他事情）
1 、 lichess 战术


--------------

功能说明：

老师端： 
板块 1： 代办（学生 xxx，提交了 xxxx）
板块 2：上传材料
板块 3： 上传 assignment
板块 4：上传考试
板块 5：学生管理。
板块 6：作业入口 - 每一个上传的作业卡片按照 due date 整合。点入后有正确率统计等，然后每道题可以显示哪个学生做对哪个学生做错。
板块 7：broadcast 功能：和 catachat 联动。 catachat 出现班级列表。

功能 8 - 一旦该用户创建了一个有人的班级，workspace/shared中，自动出现一个置顶的文件夹：My Classroom/{class name}/{student username}这个文件夹，如果学生在classroom 中选择 share with teacher，都会出现在这里。

材料： 学生看了就可以
assignment：有可以量化的 task 。
考试：带正确率评分

材料/assignment/考试下面的分类：

材料分类：
1 、workspace 直接导入
2 、老师自己上传照片/pdf

assignment 分类：
1 、战术 - 采用 lichess 开源战术集。
2 、 开局 - 之后需要重新写 opening trainer
3 、局面 trainer - 现在的 trainer
4 、老师自己上传照片/pdf 。

考试分类：
1 、战术考试
2 、开局考试

其他功能：
1 、老师选择时间或者不限时
2 、老师选择 deadline
3 、老师选择一共能做多少次。


学生端：
板块 1：代办 - 逾期/临期
板块 2：announcement去 - 展示老师发的最近消息 - 点击某个入口直接进入 catachat里面
板块 3：作业入口 - due date 和作业卡片。
板块 4：联系老师 -  允许 share folder with teacher

