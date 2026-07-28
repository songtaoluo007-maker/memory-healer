# 拾忆 · Memory Healer

一款关于皮影、记忆与代际传承的 AI 叙事游戏。玩家作为“记忆修复师”，
穿行于陈守义跨越百年的五段人生，通过探索、对话和选择修复逐渐消散的记忆。

当前版本已完成 P0-A 产品稳定底座、五年代电影级美术，以及 1972 第一幕的
固定语音纵向切片。其余年代不会在叙事脚本冻结前批量生成固定语音。

## 当前可玩范围

- 5 个年代场景：1972、1990、2024、2050、2089。
- 7 位场景角色、17 个记忆碎片、17 个可探索热区。
- 10 个权威选择和 4 个确定性结局。
- DeepSeek 结构化角色对白；未配置或不可用时自动使用角色化本地对白。
- 1972 第一幕已提供 Edge 托管云在构建期生成的批准语音资产；运行时 Edge
  语音失败时保持完整文字玩法。
- Cookie 登录、用户隔离存档和并发覆盖保护。

后端是场景内容、规则和 `GameState` 的唯一权威来源。前端只提交玩家意图，
并应用后端返回的完整版本化状态。

## 技术结构

| 层 | 实现 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite、Vitest |
| 后端 | FastAPI、Pydantic 2、SQLAlchemy 2 |
| AI / 语音 | DeepSeek（OpenAI SDK 协议）、Edge 托管云语音、可选远程 HTTPS primary |
| 数据 | 本地 SQLite；生产支持 PostgreSQL |
| 迁移 | Alembic，当前 head 为 `20260726_0001` |
| 部署 | Nginx 同域代理、Docker Compose、GitHub Actions |

主要目录：

```text
backend/
  api/             HTTP 与 Cookie 协议
  application/     确定性游戏与对话用例
  content/         严格内容模型和交叉引用校验
  domain/          版本化权威 GameState
  integrations/    DeepSeek / Edge / 可选远程语音适配器
  persistence/     用户、会话和存档仓储
alembic/           初始数据库迁移
frontend/src/      Vue 页面、组件、组合式状态和 API 客户端
scripts/           内容校验与部署冒烟测试
```

## 本地开发

要求 Python 3.11+、Node.js 24+。从项目根目录执行：

```powershell
Copy-Item .env.example .env
python -m pip install -r requirements.txt
alembic upgrade head
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

另开终端：

```powershell
Set-Location frontend
npm ci
npm run dev
```

打开 `http://127.0.0.1:5173/`。开发服务器会把 `/api` 代理到后端；浏览器代码
不包含固定的后端主机名。API 文档位于 `http://127.0.0.1:8000/docs`。

`DEEPSEEK_API_KEY` 是可选项。留空时游戏仍能完整启动和推进，只是对白使用
本地降级内容。

语音默认不需要额外凭据：批准的 1972 固定资产随游戏发布，动态对白使用 Edge
托管云语音，`VOICE_PRIMARY_ENABLED=false`。可选 primary 只允许连接带 token
的远程 HTTPS 服务；它保持禁用时，后端不会要求该服务或任何本地语音模型。
候选生成、验证、内容寻址原子晋升、缓存清理和降级演练见
[语音生产手册](docs/voice-production.md)。

## 登录与存档

- 浏览器只使用名为 `memory_session` 的 HttpOnly、SameSite=Lax Cookie。
- 密码使用 Argon2id；数据库只保存会话令牌的 SHA-256 摘要。
- 存档以 `(user_id, slot_id)` 隔离。
- 每次写入都携带独立 `save_revision`，陈旧写入返回 HTTP 409，不能静默覆盖。

本地开发默认 SQLite。腾讯云 PostgreSQL 可使用：

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
ENVIRONMENT=production
CORS_ORIGINS=https://your-game.example.com
```

生产环境未显式设置 `COOKIE_SECURE` 时会自动启用 Secure Cookie；不能把
Credentialed CORS 配成通配符。

## Docker Compose

安装并启动 Docker daemon 后：

```powershell
docker compose config --quiet
docker compose up --build -d
powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1
docker compose down
```

访问 `http://127.0.0.1:5173/`。Nginx 同域代理 `/api/`、`/tts/` 与
`/voice/`；批准的固定语音以只读方式挂载，运行时语音缓存使用独立可写卷。
后端不向宿主机开放业务端口。容器启动会先执行 `alembic upgrade head`。

## 质量门

```powershell
python scripts/validate_content.py
python -m compileall -q backend scripts
python -m pytest backend/tests -q

Set-Location frontend
npm ci
npm run typecheck
npm run lint
npm run check
npm test
npm run build
npm audit --omit=dev --audit-level=high
```

CI 还会构建前后端镜像并运行 Compose 冒烟测试。最新本地证据见
[TEST_REPORT.md](TEST_REPORT.md)，产品路线见 [UPGRADE_PLAN.md](UPGRADE_PLAN.md)，
变更进度见 [CHANGELOG.md](CHANGELOG.md)。

## 下一阶段

后续先冻结重写后的其余年代叙事脚本，再按同一档案、候选审核与事务式晋升流程
扩展固定语音。质量门、文字优先玩法与权威状态边界会继续保留。
