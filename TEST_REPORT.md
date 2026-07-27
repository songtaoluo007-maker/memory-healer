# 拾忆实体人物与全交互物美术验证报告

验证日期：2026-07-27

分支：`codex/solid-characters-fragments`

环境：Windows、Python 3.12.10、Node.js 24.16.0、npm 11.13.0、
Alembic 1.18.5、应用内浏览器

## 结论

七名可对话人物已全部替换为带真实透明通道的实体角色层；普通人物主体
`opacity: 1`，仅脚部渐隐，2089 小雨只保留克制的青紫投影边缘。全部 17 个
canonical fragment ID 已拥有独立 4:3 电影特写，五幕背景中的对应热点物件也已逐项
复核并局部补画。

真实页面已走通五个年代、七名人物和十七个热点，并在 390×844、768×1024、
1440×900、1920×1080 四种视口完成验收。验收中修正了桌面人物被电影画幅裁头、
手机全高对话抽屉遮挡人物两个问题。

| 验证项 | 结果 |
| --- | --- |
| 内容注册表 | 5 场景、7 NPC、17 碎片、17 热点、10 选择、4 结局 |
| 后端测试 | 172 passed，3 条上游弃用告警 |
| 前端测试 | 11 files / 61 tests passed |
| TypeScript / ESLint / Prettier | passed |
| Vite 生产构建 | passed，893 modules transformed |
| 电影资源校验 | 7/7 人物 alpha passed；17/17 碎片比例与体积 passed |
| Alembic | `20260726_0001 (head)`；`alembic check` 无漂移 |
| 生产依赖审计 | 高危 0；1 个仅影响 Windows 开发服务器的 low 通告 |
| 同域冒烟 | 首页、健康检查、5 场景、新游戏全部 passed |
| Docker Compose 配置 | `docker compose config --quiet` passed |
| 新增运行资源可达性 | 20/20 返回 HTTP 200 |
| 五幕浏览器验收 | 7 人物、17 热点、17 弹窗图片 passed |
| 四视口验收 | 390×844、768×1024、1440×900、1920×1080 passed |
| 图片失败降级 | 背景回退、人物即时隐藏、碎片自隐藏及下张复位 passed |

## 自动化证据

后端与内容：

```text
python scripts/validate_content.py
Content valid: 5 scenes, 7 NPCs, 17 fragments, 17 hotspots,
10 choices, 4 endings.

python -m compileall -q backend scripts
exit 0

python -m pytest backend/tests -q
172 passed, 3 warnings

python -m alembic current
20260726_0001 (head)

python -m alembic check
No new upgrade operations detected.

docker compose config --quiet
exit 0

powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1
Smoke checks passed: frontend, health, 5 scenes, and authoritative new game.
```

前端：

```text
npm run typecheck     passed
npm run lint          passed
npm run check         passed
npm test              11 files, 61 tests passed
npm run build         893 modules transformed
npm audit --omit=dev --audit-level=high
exit 0; no high-severity vulnerability
```

构建中的 `Game` JavaScript chunk 为 20.64 kB（gzip 8.52 kB），
`CinematicStage` JavaScript chunk 为 205.00 kB（gzip 60.77 kB）。

资源校验：

```text
python scripts/validate_cinematic_assets.py [7 portrait flags] [17 fragment flags]
Validated 7 portraits and 17 fragments.
```

## 人物资源

七张人物图均为纵向 alpha WebP，包含透明像素和不透明主体，单张低于 800 KB。

| 文件 | bytes |
| --- | ---: |
| `chen-shouyi-1972-solid.webp` | 66,014 |
| `chen-shouyi-1990-solid.webp` | 68,134 |
| `chen-shouyi-2024-solid.webp` | 59,920 |
| `journalist-2050-solid.webp` | 40,996 |
| `stranger-1990-solid.webp` | 60,326 |
| `xiaoyu-2050-solid.webp` | 56,918 |
| `xiaoyu-2089-projection-solid.webp` | 69,794 |
| **合计** | **422,102** |

## 交互物资源

十七张碎片图均为独立 4:3 WebP，单张低于 600 KB。

| 文件 | bytes |
| --- | ---: |
| `fragment-1972-carving-knife.webp` | 172,206 |
| `fragment-1972-shadow-stage.webp` | 192,854 |
| `fragment-1972-three-kings.webp` | 259,282 |
| `fragment-1990-farewell-letter.webp` | 114,208 |
| `fragment-1990-puppet-trunk.webp` | 148,814 |
| `fragment-1990-station-clock.webp` | 129,892 |
| `fragment-1990-train-ticket.webp` | 216,390 |
| `fragment-2024-last-show-poster.webp` | 268,658 |
| `fragment-2024-old-photos.webp` | 184,204 |
| `fragment-2024-xiaoyu-letter.webp` | 151,150 |
| `fragment-2050-audience-tears.webp` | 72,882 |
| `fragment-2050-award-trophy.webp` | 195,070 |
| `fragment-2050-hologram-stage.webp` | 130,150 |
| `fragment-2050-photo-wall.webp` | 169,192 |
| `fragment-2089-family-photo.webp` | 178,174 |
| `fragment-2089-heritage-certificate.webp` | 133,738 |
| `fragment-2089-last-puppet.webp` | 180,270 |
| **合计** | **2,897,134** |

## 背景局部补画

五张主背景保留原镜头与整体风格，只补充或强化热点物件。逐项证据见
`docs/qa/2026-07-27-hotspot-art-audit.md`。

| 文件 | bytes |
| --- | ---: |
| `scene-1972-xian-alley.png` | 1,044,802 |
| `scene-1990-shenzhen-station.webp` | 259,526 |
| `scene-2024-urban-village-room.webp` | 237,620 |
| `scene-2050-award-ceremony.webp` | 179,494 |
| `scene-2089-memory-lab.webp` | 205,766 |

1972 主背景由 2,191,151 字节降至 1,044,802 字节；五张背景均低于 1.5 MB。

## 浏览器验收

- 五幕主背景、标题、字幕、因果选择和热点层均正常。
- 七名人物脸部身份、实体不透明度、尺度、落脚和光向通过目测；2089 小雨为唯一
  `projection` 处理，主体仍清晰实体。
- 十七个热点均能打开正确的碎片图片；图片完整解码，标题、说明和“继续探索”按钮
  均可读可用。
- 390×844 的碎片弹窗完整容纳图片、文案和按钮，无横向溢出。
- 768×1024 的人物上半身保持在对话底板上方，输入区可操作。
- 1440×900 与 1920×1080 的人物不再被电影画幅顶部裁切。
- 页面运行日志没有未处理异常；20 个新增运行资源均返回 200。

## 已知说明

- npm 审计仍报告 esbuild 的 1 个 low 通告，仅涉及 Windows 本地开发服务器任意
  文件读取；生产依赖高危为 0，后续随 Vite/esbuild 兼容版本升级处理。
- 后端测试显示 Starlette TestClient、Pydantic V1 validator 和 pytest-asyncio
  默认 loop scope 的上游弃用提示；不影响 172 项测试结果。
- 本轮验证了 Compose 配置，但没有把“配置可解析”等同于完整容器镜像构建与生产
  部署验证；上线阶段仍需在有 Docker daemon 的 CI/预发布环境执行。
