这个文档是可以借鉴的前辈lichess.org的计划：

 1. NDJSON 流式加载 — 比 JSON 更快的"渐进式响应"                               
                                                                                
  普通 JSON:  等待全部数据 → 一次渲染                                           
  NDJSON:     每行数据到达 → 立刻更新 UI → 继续等后续行
                                                                                
  服务端按行输出 JSON，前端 readNdJson() 逐行处理，用户看到的不是白屏等待，而是 
  数据"流入"表格。这对数据量大的开局库尤其有价值。

  ---
  2. AbortController + Debounce 的组合 — 永远不展示过时数据

  private fetch = debounce(() => {
    this.abortController?.abort();           // 取消上一个请求
    this.abortController = new AbortController();
    xhr.opening(..., this.abortController.signal);  // 新请求携带取消信号
  }, 250, true);

  用户快速翻棋谱时，每次走棋都触发 debounce，250ms
  内不停动则不发请求；发出去的请求如果局面又变了，立刻
  abort。彻底杜绝"后发先至"的数据竞争问题，这是很多前端项目的常见 bug 源。

  ---
  3. FEN 为 key 的内存缓存 — 回溯瞬间响应

  private cache: Dictionary<ExplorerData> = {};

  setNode = () => {
    const cached = this.cache[node.fen];
    if (cached) {
      this.loading(false);   // 直接渲染，0 延迟
    } else {
      this.fetch();           // 才去网络
    }
  };

  局面唯一对应 FEN，FEN 做 key 缓存响应。用户来回翻棋谱时，已访问过的局面瞬间显
  示，不走网络。设计上极简，效果极好。

  ---
  4. Reactive Prop — 无框架的响应式

  // 核心用法：prop() 读，prop(value) 写
  loading = prop(true);
  enabled = prop(false);

  // 写入后触发 redraw()，UI 自动同步
  this.loading(false);
  this.root.redraw();

  没有 Redux、没有 MobX、没有 RxJS，一个极简的 Prop<T> getter/setter
  模式统管全部状态。整个状态树清晰可见，没有任何魔法。

  ---
  5. TypeScript 类型判别 — 编译期杜绝 UI 渲染错误

  // 运行时 tag
  export function isOpening(m: ExplorerData): m is OpeningData {
    return !!m.isOpening;
  }
  export function isTablebase(m: ExplorerData): m is TablebaseData {
    return !!m.tablebase;
  }

  // 渲染层：TypeScript 静态确保两条分支不会混淆
  if (isOpening(data)) showMoveTable(ctrl, data);      // data 是 OpeningData
  else if (isTablebase(data)) showTablebase(ctrl, data); // data 是
  TablebaseData

  开局数据库和残局 Tablebase
  数据结构完全不同，类型判别函数让编译器在渲染层全程护航。

  ---
  6. 事件委托 via Snabbdom Hooks — 一个监听器管整张表

  // 不是每行一个 listener，而是表格级别的单一 listener
  hook: {
    insert(vnode) {
      vnode.elm.addEventListener('mouseover', e => {
        const uci = $(e.target).parents('tr').attr('data-uci'); // 从 data attr
  路由
        ctrl.explorer.setHovering(fen, uci);
      });
    }
  }

  走法表格可能几十行，但全表只有一个事件监听器。通过 data-uci
  属性做事件路由，内存占用极低，且 VNode 销毁时监听器自动随之消失，无需手动
  removeEventListener。

  ---
  7. StoredProp — localStorage 持久化与响应式的无缝结合

  db: storedProp<ExplorerDb>(
    'explorer.db2.' + variant,   // 按变体分别存储
    this.allDbs[0],               // 默认值
    str => str as ExplorerDb,     // 反序列化
    v => v,                        // 序列化
  ),

  用户选择的数据库、评分段、时间控制，刷新页面后自动恢复。StoredProp 与普通 Prop
   API 完全一致，切换到持久化版本只需换一个构造函数，对调用方透明。

  ---
  总结

  ┌────────────────────────────┬─────────────────────────┐
  │            理念            │       解决的问题        │
  ├────────────────────────────┼─────────────────────────┤
  │ NDJSON 流式渲染            │ 大数据集的白屏等待      │
  ├────────────────────────────┼─────────────────────────┤
  │ AbortController + Debounce │ 数据竞争 / 无效网络请求 │
  ├────────────────────────────┼─────────────────────────┤
  │ FEN 内存缓存               │ 回溯导航的重复请求      │
  ├────────────────────────────┼─────────────────────────┤
  │ Reactive Prop              │ 状态管理的复杂度        │
  ├────────────────────────────┼─────────────────────────┤
  │ TypeScript 类型判别        │ 运行时渲染错误          │
  ├────────────────────────────┼─────────────────────────┤
  │ 事件委托 via Hooks         │ 大列表的内存膨胀        │
  ├────────────────────────────┼─────────────────────────┤
  │ StoredProp                 │ 持久化与响应式的割裂    │
  └────────────────────────────┴─────────────────────────┘

  最值得借鉴的核心思想是：不依赖大型框架，用最小的工具组合解决具体问题——Debounce
   + Abort 解决并发，FEN key 解决缓存，Prop
  解决响应式，每个工具只做一件事，组合起来却极为强大。
