# 拾忆 P0-A / P0-B 验证报告

验证日期：2026-07-27

分支：`codex/stabilize-core`

环境：Windows、Python 3.12.10、Node.js 24.16.0、npm 11.13.0、
Alembic 1.18.5、Microsoft Edge

## 结论

P0-A 稳定产品底座与 P0-B“1972 西安老巷”电影级纵向切片均已通过本地验收。
1972 已达到当前产品的代表性画质与交互标准；1990、2024、2050、2089 仍使用
旧插画回退，不声称已完成最终电影美术。

| 验证项 | 结果 |
| --- | --- |
| 内容注册表 | 5 场景、7 NPC、17 碎片、17 热区、10 选择、4 结局 |
| 后端测试 | 168 passed |
| 前端测试 | 8 files / 37 tests passed |
| TypeScript / ESLint / Prettier | passed |
| Vite 生产构建 | passed，863 modules transformed |
| Python 全量编译 | passed |
| Alembic | `20260726_0001 (head)`；`alembic check` 无漂移 |
| 生产依赖审计 | 高危 0；1 个仅影响 Windows 开发服务器的 low 通告 |
| 同域冒烟 | 首页、健康检查、5 场景、新游戏全部 passed |
| Docker Compose 配置 | `docker compose config --quiet` passed |
| 浏览器视觉验收 | 390×844、768×1024、1440×900、1920×1080 passed |
| 无障碍显示边界 | reduced-motion、200% 文字缩放、语义化按钮与对话 passed |
| 美术加载降级 | 主 PNG 被拦截时自动回退可操作 SVG，页面无异常 |

## 自动化证据

后端：

```text
python scripts/validate_content.py
Content valid: 5 scenes, 7 NPCs, 17 fragments, 17 hotspots,
10 choices, 4 endings.

python -m compileall -q backend scripts
exit 0

python -m pytest backend/tests -q
168 passed, 3 warnings
```

前端：

```text
npm run typecheck     passed
npm run lint          passed
npm run check         passed
npm test              8 files, 37 tests passed
npm run build         Vite build passed; 863 modules transformed
npm audit --omit=dev --audit-level=high
exit 0; no high-severity vulnerability
```

生产构建按页面与能力拆包。PixiJS 电影舞台 chunk 为 202.83 kB
（gzip 59.65 kB）；1972 主场景与人物立绘合计约 4.27 MB，后续 P1 应接入
对象存储/CDN 与现代图片格式，而不是继续扩大首包。

数据库与同域协议：

```text
python -m alembic current
20260726_0001 (head)

python -m alembic check
No new upgrade operations detected.

docker compose config --quiet
exit 0

powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1
Smoke checks passed: frontend, health, 5 scenes, and authoritative new game.
```

## P0-B 浏览器验收

完整检查了首页、序章、教程、登录、存档、1972 游戏场、热点、人物对白、因果选择、
碎片背包、记忆档案、时序/因果/记录浮层与结局。

- 桌面 1440×900 与 1920×1080 使用 2.39:1 电影舞台和字幕安全区。
- 手机 390×844 使用竖向场景焦点、底部工具栏和全宽对白抽屉。
- 平板 768×1024 保持纵向构图，字幕与因果选择互不遮挡。
- 200% 文字缩放下首页标题、主操作和账号入口无裁切。
- `prefers-reduced-motion` 下 Pixi ticker 与 CSS 胶片颗粒停止。
- 页面隐藏时舞台暂停；低效/窄屏设备限制 30 FPS 与较少粒子。
- 主电影 PNG 加载失败时回退到旧 SVG，热点与剧情选择仍可操作。
- 匿名首页、游戏主流程与回退路径未出现未处理的页面异常。

## 覆盖的关键风险

- 内容 ID 重复、跨场景错误引用、不可达结局条件。
- 游戏状态未知字段、失配碎片状态和陈旧 revision。
- 五场景探索、选择、场景跳转与四结局计算。
- DeepSeek 超时、有限重试、熔断、结构化输出失败和本地角色对白。
- Argon2id 密码、Cookie 会话、过期/撤销、用户名冲突和统一登录错误。
- 用户存档隔离、严格 `GameState`、CAS 冲突和陈旧写保护。
- TTS 输入边界、并发合并、原子缓存、失败残留和容量清理。
- Pixi 生命周期、断图回退、移动遮挡、浮层冲突和 reduced-motion。
- 前端只应用权威状态，不再维护第二套热区/碎片/选择规则。

## 已知说明

- npm 审计仍报告 esbuild 的 1 个 low 通告，仅涉及 Windows 本地开发服务器任意
  文件读取；`npm audit fix` 在当前兼容依赖范围内无可用变更。生产依赖高危为 0，
  P1 跟随 Vite/esbuild 兼容版本升级处理。
- 后端测试显示 Starlette TestClient、Pydantic V1 validator 和
  pytest-asyncio 默认 loop scope 的上游弃用提示；不影响 168 项测试结果，P1
  依赖升级时迁移。
- 本机仍没有可用 Docker daemon，因此不声称镜像构建或容器启动已通过；Compose
  配置已通过，GitHub Actions 的 docker/smoke job 会在具备 daemon 的 runner 上执行。
