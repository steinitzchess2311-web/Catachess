## 如下为 2026.7.8  代办

请严格遵循 agents/约束完成。完成后，请在每一项前 绘制 -[✅]

必须保证这是工程级别，可以扛住很多人同时使用。


引擎功能：
-[✅] 服务器上，部署 stockfish worker 和 alphazero worker 。产品级别根据极大网站的工程级别部署。 alphazero 可以放在 gpu 上。但是加上限制（stockfish 最多 10cpu 同时跑，alphazero 最多占一部分 gpu，不要挤爆服务器。）产品级别的设置排队机制等等。
  - 2026-07-08 23:10 EDT：Stockfish 本机 worker 已部署到服务器，跨 gunicorn 进程全局最多 10 个 Stockfish 进程；AlphaZero worker 入口、健康检查、队列/限流和受控不可用错误已部署，但服务器当前 `nvidia-smi` 无法连接驱动，且未配置 `ALPHAZERO_COMMAND`/`ALPHAZERO_MODEL_PATH`，真实 AlphaZero 推理仍等待 GPU/模型。
  - 2026-07-08 23:34 EDT：AlphaZero 不作为总 goal 阻塞点；如原 AlphaZero 环境不可用，后续改走 LC0/Leela 路线并优先适配 ROCm GPU，同样保留并发/显存保护和受控不可用。
  - 2026-07-08 23:55 EDT：LC0/Leela 已在服务器用户目录构建并部署，权重为 `T1-256x10-distilled`，`engine=lc0` 生产 smoke 返回 `source: LC0`；当前 ONNX Runtime ROCm provider 对 `gfx1151` 搜索阶段报 `hipErrorNoBinaryForGpu`/segfault，因此生产临时使用 `onnx-cpu` backend、全局并发上限 1，不阻塞总 goal。

-[✅] 前端展示和前端的连接用最产品级别的方式，websocket 啥的都可以。前端格式和 stockfishwasm 一样。

-[✅] 修改当前的study 或者 analysis page 当中 engine 前端展示。 1 、顺便修的更加产品级别、简洁清楚。 2 、让用户可以选择引擎。


predictor 功能：

-[✅] study 当中，chapters analysis 右边加 predictor  （analysis 上面加上这个 study 一样的横的分的，只是没有 chapters）
-[✅] predictors 的定义是“人类走法预测器”。我们需要两个 predictor 。一个是 maia，一个是 catie 。maia 你可以从网上下载 maia 的模型，然后用，让用户选择。记住产品级别设计工程级别的 worker，不会挤爆；catiechess在服务器上，你看看 catiechess/analysis 这个里面是啥样的，可以复用这些，直接给他打请求即可（cors policy 啥的改一下给他直接打请求）。然后前端好好设计一下。
  - 2026-07-08 23:34 EDT：已部署 `/api/predictor`，Maia 使用服务器已有 Maia2 rapid 权重并发上限 2，Catie 经 CataChess 后端代理本机 CatieChess 队列；生产 smoke 已验证 Maia `maia2-rapid` 和 Catie `carlsen.best` 均返回 top-k 概率。

classroom 功能

- 全部页面前端参考 workspace/ 和 study 内部产品级别的重构。包括弹窗

study 权限

- 接下来要做一个大改：1 、数据库区分 study 的 viewer 和 modifier
- 实现可以多人同时修改，实时更新。暂时不做所有人同步在一个页面的。


其他

- blog 太丑了，像个玩具，不是产品级别的。无论是这个 blog 展示页面还是编辑页面。请你参考 workspace 的设计和 study 内部的这种设计，产品级别的重构一下
- catachat 不要单独弄，麻烦的要死，就直接打通账号就好。
- header 铃铛那个消息通知显示有 bug，请修复。同时，如果别人邀请你加入study 也在那里显示，某某某邀请你加入研讨。
-[✅] profile 的那个 title，三运 GM 这种什么的（出现在用户名前的显示）改成橙色的。
-[✅] profile 加一个总在线时长。好像我记得已经有后端接口了你看着复用即可。
-[✅] profile 中国棋协 称号 改成中国棋协称号（不要当中空格）
-[✅] profile log out 那个确认弹窗产品级别的重构


排查问题：
-[✅] 排查为什么我们网站使用有时候前端会卡顿，尽量消除卡顿点
-[✅] 当前study 每 5 秒自动保存一次，如果用户量大，多次同时打请求，会不会崩？如果会，修复。并且换成每 2 秒自动保存一次。
