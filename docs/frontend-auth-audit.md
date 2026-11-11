# 前端接口鉴权信息排查

排查日期：2026-11-11。基于提交 `01f90c95683c581dd75085c514dc96295a8db3c3` 及当前工作区。

## 范围与结论

静态遍历 `frontend/src` 下 225 个 JS/TS 源文件，追踪修复后 212 处公共请求工具调用、全部 6 处底层网络入口，以及原生链接、页面跳转、图片和文件预览。对照网关 `AuthFilter`、`OmsAuthFilter` 和部署代理路由，检查浏览器请求是否携带 JWT 或 SSO Cookie。

普通 REST、分片上传、清洗日志流和日志下载已使用认证拦截器。新增发现 6 类业务下载和 DeerFlow 配置探测缺少 JWT 请求头，已修复。示例算子下载一并复用修正后的公共下载函数。文件和归集日志预览同时补齐显式 `credentials: include` 和登录失效处理。

仍发现 DeerFlow 原生页面导航与 JWT 登录不兼容，见下方待处理项。这里的排查结论针对本仓库前端请求；独立 DeerFlow 镜像内的前端源码未包含在仓库中，不能据此断言其内部所有 API 已通过验证。未进行线上账号与部署环境联调，也不以本次检查代替后端权限或资源隔离审计。

## 已修复的入口

所有下载通过 `Request.get()` 发出请求，携带 `Authorization: Bearer <token>` 和 `credentials: include`；验证响应成功后才生成 Blob 下载链接，不再把 JWT 放在 URL 查询参数中。

| 接口 | 原因与处理 |
| --- | --- |
| `/api/data-management/datasets/{id}/files/download` | 公共下载仅将 token 放入 URL；改用认证请求。 |
| `/api/data-management/datasets/{id}/files/directories/download` | 同上，保留中文目录 prefix 查询参数。 |
| `/api/data-management/datasets/{id}/files/{fileId}/download` | 同上，保留 prefix 和指定文件名。 |
| `/api/v1/evaluation/reports/{reportId}/export` | 同上，保留 format 和文件名。 |
| `/api/annotation/auto/{taskId}/download` | 同上。 |
| `/api/cleaning/tasks/{taskId}/result/download` | API 封装使用原生链接，文件表格另用无认证 fetch；两条路径统一使用认证下载。 |
| `/deer-flow-backend/config` | 首页直接 fetch，缺少 JWT；改用认证请求，同时在失败时清理超时计时器。 |
| `/api/operators/examples/download` | 保留上一次修复的行为，统一复用公共下载，避免重复实现。 |

文件预览和 `/api/data-collection/executions/{id}/log` 预览此前经过请求拦截器，但绕过响应拦截器，且未显式指定跨域 Cookie 策略。现在复用完整请求链；HTTP 401 和 HTTP 200 中的认证失败业务码均触发统一登录处理，不会保存为文件。

## 全量调用覆盖

下面的数字是静态调用位置数量，包含多种方法、分支和公开登录接口，不是唯一后端路由数量。

| 文件（相对 frontend） | 公共请求工具调用数 |
| --- | ---: |
| `src/components/AuthGuard.tsx` | 2 |
| `src/pages/DataAnnotation/annotation.api.ts` | 24 |
| `src/pages/DataCleansing/cleansing.api.ts` | 17 |
| `src/pages/DataCollection/collection.apis.ts` | 9 |
| `src/pages/DataEvaluation/evaluation.api.ts` | 60 |
| `src/pages/DataManagement/dataset.api.ts` | 39 |
| `src/pages/Home/Home.tsx` | 1 |
| `src/pages/KnowledgeBase/knowledge-base.api.ts` | 11 |
| `src/pages/Layout/Header.tsx` | 3 |
| `src/pages/OperatorMarket/operator.api.ts` | 18 |
| `src/pages/RatioTask/Detail/RatioTaskDetail.tsx` | 2 |
| `src/pages/RatioTask/ratio.api.ts` | 4 |
| `src/pages/SettingsPage/settings.apis.ts` | 8 |
| `src/pages/SynthesisTask/synthesis-api.ts` | 12 |
| `src/utils/systemParam.ts` | 2 |
| 合计 | 212 |

剩余底层网络入口逐项检查如下：

| 入口 | 结论 |
| --- | --- |
| `main.tsx` 首页配置 fetch | 手工携带 JWT 和 `credentials: include`，已有启动测试覆盖。 |
| `main.tsx` `/api/user/me` fetch | 同上；网关允许该接口自行判断登录状态。 |
| `request.ts` fetch | 请求配置先经过认证拦截器。 |
| `request.ts` XMLHttpRequest | 使用拦截后的 headers，`withCredentials` 对应 include，已验证分片上传。 |
| `errorConfigStore.ts` fetch | 请求公开静态 `/config/error-code.json`，不需要业务认证头。 |
| `authSlice.ts` `/api/auth/login` fetch | 未发现 `loginUser` 的调用方；这是遗留登录入口，当前 UI 使用 AuthGuard 的 `/api/user/login`。遗留路径与网关白名单不一致，并将 token 存入不同缓存键，若恢复使用需先统一；本次未改动该未使用流程。 |

文件图片预览使用已认证获取的 Blob URL；PDF、清洗日志、归集日志和批量导出按钮使用本地 Blob。文档中的外部链接、模板示意图和头像不自动附加 DataMate JWT。Label Studio 跳转属于外部应用会话，不能用 DataMate Authorization 头替代其登录；现有标注任务登录 API 本身走公共请求工具。

## 待处理：DeerFlow 页面会话

条件：`datamate.jwt.enable=true`，未通过 SSO Cookie 认证，DeerFlow 已部署。

首页 `Home.tsx` 使用 `window.location.href = "/chat"` 打开独立应用。浏览器原生导航及其 `/_next/**` 静态资源请求不会从 localStorage 自动生成 Authorization 头。`ApiGatewayApplication` 将这些路径转到 DeerFlow，而 `AuthFilter` 对它们同样要求 Bearer JWT。因此配置探测修复后，页面导航仍可能返回 401；直接访问或刷新 `/chat` 也有相同问题。

这一项尚未修复。需要 DataMate 网关和 DeerFlow 建立可供页面导航使用的会话（例如受保护的服务端 Cookie 或短期会话交换），并验证 Cookie 范围、过期和退出行为；仅给配置探测加请求头无法完成这项集成。

## 验证

- `npm test`：覆盖现有基础功能、启动认证、清洗日志及新增请求鉴权测试。
- `node tests/request-auth.test.cjs`：25 项通过，覆盖 7 个下载封装的 JWT/SSO 配置、二进制字节与文件名、预览、401/业务认证错误、REST 方法、multipart、XHR 分片上传、失败/取消、DeerFlow 探测。
- `node.exe node_modules/vite/bin/vite.js build`：生产构建通过。当前依赖安装包含 Windows Rollup 原生模块；Linux Node 下直接构建缺少 `@rollup/rollup-linux-x64-gnu`。
- `git diff --check`：无空白错误。

下载现在通过 Blob 完整接收文件后触发浏览器保存，大文件会增加浏览器端资源占用；此次未验证大文件压力场景。需要超大文件直接流式落盘时，应单独设计带认证的流式或短期下载凭据方案。
