# 测试说明（TESTING）

本项目为「企业制度知识复核与阅读追踪系统」补充了一批单元测试，覆盖前后端核心业务链路，
方便在提交前快速验证主流程未被破坏。

## 覆盖范围

### 后端（`backend/tests/`，pytest）
| 测试文件 | 覆盖服务 | 关键验证点 |
| --- | --- | --- |
| `test_auth_service.py` | 认证服务 / 安全工具 | 登录鉴权（用户名、密码、角色匹配）、token 载荷、用户创建去重、密码哈希 |
| `test_knowledge_service.py` | 制度条目服务 | 新增（分类/停用校验、周期回退）、查询、状态与关键字筛选、复核到期状态计算、编辑/删除权限 |
| `test_category_service.py` | 分类服务 | 分类树构建与排序、启用/停用过滤、创建（path/level）、删除约束 |
| `test_reading_service.py` | 阅读确认服务 | 标记已读（幂等）、标记未读、我的阅读记录筛选与分页 |
| `test_review_service.py` | 复核服务 | 待复核列表、通过/驳回、批量复核、复核统计与到期计数 |
| `test_summary_service.py` | 复核汇总服务 | 汇总重建、节点/根聚合、未读数随阅读态变化 |

### 前端（`frontend/src/**/__tests__/`，Vitest + happy-dom）
| 测试文件 | 覆盖对象 | 关键验证点 |
| --- | --- | --- |
| `api/__tests__/api.test.ts` | 接口封装 | 请求方法、URL 拼接、参数组装 |
| `stores/__tests__/user.test.ts` | 用户状态 store | 登录状态更新、token/user 持久化、`hasRole` 权限判断、异常处理 |
| `stores/__tests__/category.test.ts` | 分类 store | 树加载、选中态递归查找、下拉选项组装、CRUD 状态更新 |
| `pages/__tests__/KnowledgeList.test.ts` | 制度列表页 | 筛选参数组装、标记已读/未读、分页/筛选变化、提交制度 |
| `pages/__tests__/ReadingStatus.test.ts` | 阅读确认页 | 参数组装、统计派生、标记状态、详情异常提示 |

## 测试设计原则
- **内存级依赖替代真实环境**：后端使用内存 SQLite（`StaticPool`）+ fixtures，每个用例独立、可重复；
  前端通过 `vi.mock` 拦截 axios 封装、ant-design-vue 的 `message/Modal` 与 pinia store 依赖。
- **小规模 mock 数据**：`conftest.py` 提供三种角色用户、两层分类树与覆盖各复核到期状态的制度条目。
- **聚焦逻辑而非渲染**：页面测试通过 `wrapper.vm` 调用方法、断言响应式状态，组件统一 stub。

## 运行方式

### 一键运行（推荐）
```bash
./run_tests.sh            # 前后端全部
./run_tests.sh backend    # 仅后端
./run_tests.sh frontend   # 仅前端
```

### 后端
```bash
cd backend
python3 -m pytest              # 全部
python3 -m pytest -v           # 详细输出
python3 -m pytest tests/test_auth_service.py   # 单文件
```
> 依赖已在 `backend/requirements.txt` 中（pytest、sqlalchemy 等）。测试无需真实数据库或启动服务。

### 前端
```bash
cd frontend
npm install       # 首次需安装 vitest / @vue/test-utils / happy-dom
npm run test              # 运行一次
npm run test:watch        # 监听模式
npm run test:coverage     # 覆盖率（需安装 @vitest/coverage-v8）
```

## 当前结果
- 后端：**89** 个用例全部通过。
- 前端：**57** 个用例全部通过。

## 备注
- 修复了 `frontend/src/pages/ReadingStatus.vue` 中 `#bodyCell` 首个分支误用 `v-else-if`
  （缺少起始 `v-if`）导致的模板编译错误。
