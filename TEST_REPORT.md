# 拾忆 P0-A 验证报告

验证日期：2026-07-26

分支：`codex/stabilize-core`

环境：Windows、Python 3.12.10、Node.js 24.16.0、npm 11.13.0、
Alembic 1.18.5

## 结论

P0-A 的内容、权威状态、完整流程、AI/TTS 降级、认证、存档、迁移、前端质量
和同域运行已通过本地验收。电影级 UI/最终美术不属于 P0-A，仍在 P0-B 待办。

| 验证项 | 结果 |
| --- | --- |
| 内容注册表 | 5 场景、7 NPC、17 碎片、17 热区、10 选择、4 结局 |
| 后端测试 | 168 passed |
| 前端测试 | 5 files / 30 tests passed |
| TypeScript / ESLint / Prettier | passed |
| Vite 生产构建 | passed，148 modules transformed |
| Python 全量编译 | passed |
| Alembic | `20260726_0001 (head)`；`alembic check` 无漂移 |
| 生产依赖审计 | `npm audit --omit=dev --audit-level=high`：0 vulnerabilities |
| CI 语法 | actionlint 1.7.12 passed |
| 同域冒烟 | 首页、健康检查、5 场景、新游戏全部 passed |
| Docker Compose 配置 | `docker compose config --quiet` passed |
| 容器镜像/启动 | 未在本机执行：Docker daemon 不存在，详见下方 |

## 执行证据

后端：

```text
python scripts/validate_content.py
Content valid: 5 scenes, 7 NPCs, 17 fragments, 17 hotspots,
10 choices, 4 endings.

python -m compileall -q backend scripts
exit 0

python -m pytest backend/tests -q
168 passed
```

前端：

```text
npm run typecheck     passed
npm run lint          passed
npm run check         passed
npm test              5 files, 30 tests passed
npm run build         Vite build passed; 148 modules transformed
npm audit --omit=dev --audit-level=high
found 0 vulnerabilities
```

数据库迁移在全新临时 SQLite 文件上执行：

```text
alembic upgrade head
alembic current
20260726_0001 (head)

alembic check
No new upgrade operations detected.
```

临时迁移库在确认绝对路径位于项目 `data` 目录后删除，不包含用户数据。

部署协议：

```text
docker compose config --quiet
exit 0

powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1
Smoke checks passed: frontend, health, 5 scenes, and authoritative new game.
```

冒烟脚本本次运行在本地 Vite/FastAPI 同域代理栈。执行 `docker compose build`
时，Docker CLI 报告无法连接
`npipe:////./pipe/dockerDesktopLinuxEngine`；系统中没有可启动的 Docker
Desktop/daemon 服务。因此本报告不声称镜像构建或容器启动已在此机器通过。
GitHub Actions 的 `docker` 与 `smoke` job 会在具备 daemon 的 runner 上强制执行。

## 覆盖的关键风险

- 内容 ID 重复、跨场景错误引用、不可达结局条件。
- 游戏状态未知字段、失配碎片状态和陈旧 revision。
- 五场景探索、选择、场景跳转与四结局计算。
- DeepSeek 超时、有限重试、熔断、结构化输出失败和本地角色对白。
- Argon2id 密码、Cookie 会话、过期/撤销、用户名冲突和统一登录错误。
- 用户存档隔离、严格 `GameState`、CAS 冲突和陈旧写保护。
- TTS 输入边界、并发合并、原子缓存、失败残留和容量清理。
- 前端只应用权威状态，不再维护第二套热区/碎片/选择规则。

## 已知验证说明

- 当前测试运行会显示 Starlette 对 `TestClient` 传输层的上游弃用提示；不影响
  168 项测试结果，后续依赖升级时跟进。
- P0-B 开始前仍需保留本报告中的全部自动化门。
