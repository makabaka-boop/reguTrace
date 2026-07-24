# 单元测试说明

本仓库为「企业制度知识复核与阅读追踪系统」补充了前后端单元测试，覆盖核心业务链路，
方便后续迭代提交前快速回归。

## 目录结构

```
reguTrace/
├── pytest.ini                     # 后端 pytest 配置（pythonpath/testpaths）
├── run-tests.sh                   # 一键运行前后端全部测试
├── backend/
│   ├── requirements-test.txt      # 后端测试依赖
│   └── tests/
│       ├── conftest.py            # 内存级 SQLite + 工厂 fixture
│       ├── test_auth_service.py
│       ├── test_knowledge_service.py
│       ├── test_category_service.py
│       ├── test_reading_service.py
│       ├── test_review_service.py
│       └── test_summary_service.py
└── frontend/
    ├── vitest.config.ts
    ├── package.json               # 已新增 test / test:watch / test:coverage 脚本
    └── src/
        ├── test/setup.ts          # 全局 mock：axios、antd message/Modal、router
        ├── api/*.spec.ts          # 接口封装参数组装与 URL 校验
        ├── stores/*.spec.ts       # pinia store 状态/权限/持久化
        └── pages/*.spec.ts        # 制度列表、阅读确认页面关键方法
```

## 后端测试

技术栈：pytest + SQLAlchemy 内存 SQLite（每个用例独立建表/销毁，互不污染），
触发器（`app/triggers/summary_triggers.sql`）在测试库中自动加载，保证汇总数据与
生产一致。

首次运行安装依赖：

```bash
pip install -r backend/requirements.txt
pip install -r backend/requirements-test.txt
```

运行全部后端测试（在仓库根目录执行）：

```bash
python3 -m pytest backend/tests
# 或仅运行某一文件
python3 -m pytest backend/tests/test_knowledge_service.py -v
```

覆盖点：

- **认证服务**：登录成功/密码错误/用户不存在/角色不匹配、JWT 载荷、用户创建与重复校验。
- **制度条目服务**：新增/查询/详情/更新/删除、分类子树过滤、关键字、复核状态与到期状态
  筛选（`overdue / upcoming / normal`）、分页、阅读标记回填、越权编辑/删除拦截。
- **分类服务**：树结构构建、按排序号排序、启用/停用过滤、CRUD、有子分类/有条目时禁止删除、
  停用、移动（禁止移入自身后代）、合并、重建路径等。
- **阅读确认服务**：标记已读（幂等更新）、标记未读（删除记录）、按到期状态过滤、分页。
- **复核统计服务**：单条通过/驳回、批量通过/驳回、下次复核日期按周期计算、统计计数
  （pending/approved/rejected/upcoming/overdue）。
- **汇总服务**：节点 total/pending/unread 计数、全节点汇总、重建汇总。

## 前端测试

技术栈：Vitest + @vue/test-utils + happy-dom，通过 `src/test/setup.ts` 统一 mock
掉网络层（axios 实例）、ant-design-vue 的 `message`/`Modal`、以及 vue-router。

安装依赖（首次）：

```bash
cd frontend
npm install
```

运行：

```bash
npm test            # 单次运行
npm run test:watch  # 监听模式（TDD）
npm run test:coverage  # 生成覆盖率报告
```

覆盖点：

- **接口封装**（`src/api/*.spec.ts`）：每个 API 的 URL、HTTP 方法、请求参数/请求体组装，
  以及可选参数默认值。
- **用户 store**：token/user 持久化到 localStorage、登录成功/失败、登出清理并跳转、
  `fetchCurrentUser` 异常清理、`hasRole` 单角色与数组角色权限判断。
- **分类 store**：`fetchTree` 加载与 loading 态、`selectedCategory` 计算属性、
  `categoryOptions` 缩进标签与禁用停用节点、`create/update/remove/move/merge/copy/deactivate`
  成功/失败行为与选中项联动。
- **制度列表页**：挂载时加载分类树与列表、筛选参数组装（分类/分页/关键字/状态/到期）、
  按角色控制「提交制度」「导出Excel」按钮显示、标记已读成功后刷新列表、非 2xx 响应兜底。
- **阅读确认页**：挂载加载参数、stats 统计计算、到期筛选触发重载、标记已读/未读调用对应接口、
  查看详情失败提示、分页切换更新页码。

## 提交前建议

```bash
# 一键回归
./run-tests.sh
```

或分别执行 `python3 -m pytest backend/tests` 与 `(cd frontend && npm test)`。
用例均使用小规模 mock 数据与内存依赖，执行速度快，适合在 pre-push / CI 中运行。
