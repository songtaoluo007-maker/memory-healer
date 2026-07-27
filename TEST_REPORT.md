# 拾忆 P0 / P1 核心电影美术验证报告

验证日期：2026-07-27

分支：`codex/stabilize-core`

环境：Windows、Python 3.12.10、Node.js 24.16.0、npm 11.13.0、
Alembic 1.18.5、Microsoft Edge

## 结论

P0-A 稳定产品底座、P0-B“1972 西安老巷”纵向切片与 P1 的 1990—2089
核心电影美术实现均已通过自动化质量门。后四幕现已具备独立主场景、NPC 立绘、
代表碎片插镜与年代调色；共新增 14 张 WebP，不再以旧插画作为正常路径。

应用内浏览器的自动控制策略拒绝接管本机 URL，因此本轮未执行 1990—2089 的
四视口人工截图巡检，不将其记录为已通过。前后端本地服务与全部新增资源均可访问，
用户可直接刷新 `http://127.0.0.1:5173/` 进行最终视觉签收。

| 验证项 | 结果 |
| --- | --- |
| 内容注册表 | 5 场景、7 NPC、17 碎片、17 热区、10 选择、4 结局 |
| 后端测试 | 168 passed |
| 前端测试 | 11 files / 52 tests passed |
| TypeScript / ESLint / Prettier | passed |
| Vite 生产构建 | passed，880 modules transformed |
| Python 全量编译 | passed |
| Alembic | `20260726_0001 (head)`；`alembic check` 无漂移 |
| 生产依赖审计 | 高危 0；1 个仅影响 Windows 开发服务器的 low 通告 |
| 同域冒烟 | 首页、健康检查、5 场景、新游戏全部 passed |
| Docker Compose 配置 | `docker compose config --quiet` passed |
| P0-B 浏览器视觉验收 | 390×844、768×1024、1440×900、1920×1080 passed |
| P1 四视口视觉验收 | 待人工签收；自动接管本机 URL 被浏览器策略拒绝 |
| P1 资源可达性 | 14/14 WebP 返回 200 与 `image/webp` |
| 无障碍显示边界 | reduced-motion、200% 文字缩放、语义化按钮与对话 passed |
| 美术加载降级 | 场景回退旧插画、碎片自隐藏均有组件测试 |

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
npm test              11 files, 52 tests passed
npm run build         Vite build passed; 880 modules transformed
npm audit --omit=dev --audit-level=high
exit 0; no high-severity vulnerability
```

生产构建按页面与能力拆包。PixiJS 电影舞台 chunk 为 204.70 kB
（gzip 60.66 kB）。1990—2089 的 14 张新增 WebP 合计 2,373,882 bytes
（2.26 MiB），每张 66,548—280,540 bytes；1972 两张 PNG 仍合计约 4.27 MB，
后续应优先转换并接入对象存储/CDN。

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

## P1 1990—2089 电影美术验收

本轮交付四张主场景、六张 NPC 立绘和四张代表碎片插镜。陈守义覆盖 43 岁与
77 岁，小雨覆盖 48 岁与大学时期记忆投影；同场景 NPC 使用独立 canonical ID
选择立绘。五幕调色顺序由测试锁定为 `amber`、`rail`、`rain`、`ceremony`、
`memory`。

| 资产 | bytes |
| --- | ---: |
| `chen-shouyi-1990.webp` | 117,770 |
| `chen-shouyi-2024.webp` | 107,020 |
| `fragment-1990-train-ticket.webp` | 216,390 |
| `fragment-2024-xiaoyu-letter.webp` | 151,150 |
| `fragment-2050-award-trophy.webp` | 195,070 |
| `fragment-2089-last-puppet.webp` | 180,270 |
| `journalist-2050.webp` | 66,548 |
| `scene-1990-shenzhen-station.webp` | 280,540 |
| `scene-2024-urban-village-room.webp` | 235,212 |
| `scene-2050-award-ceremony.webp` | 194,066 |
| `scene-2089-memory-lab.webp` | 233,518 |
| `stranger-1990.webp` | 126,700 |
| `xiaoyu-2050.webp` | 104,984 |
| `xiaoyu-2089-projection.webp` | 164,644 |
| **合计** | **2,373,882** |

自动化验证包括：

- 14 个开发服务器资产请求均返回 200、`image/webp` 与预期字节数。
- 五个场景注册、六个后续 NPC 映射、四个代表碎片注册与各年代移动焦点通过单测。
- 场景图片加载拒绝后渲染 legacy 插画；未知场景也进入同一可操作回退路径。
- 碎片图片触发 `error` 后自隐藏，弹窗标题、说明与继续按钮由父层保留。
- 插镜使用 16:9、桌面 `34vh` / 窄屏 `26vh` 上限；reduced-motion 关闭图片过渡。

未自动完成：

- 390×844、768×1024、1440×900、1920×1080 的 P1 页面截图巡检。
- 各幕人物、字幕、热点与选择叠层的最终人工视觉确认。

原因是应用内浏览器拒绝自动控制本机 URL；没有改用其他浏览器控制方式绕过策略。
这两项保持为人工签收，不影响自动化功能、构建、内容和故障降级结论。

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
- 本轮 P1 四视口视觉巡检受应用内浏览器本机 URL 接管策略限制，未冒充为通过；
  本机服务当前可访问，可由用户刷新页面完成最终目测签收。
