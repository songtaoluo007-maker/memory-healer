# Changelog

本项目按 Keep a Changelog 的结构记录重要变化。

## [Unreleased]

### Added

- 严格的五场景内容注册表和跨文档引用校验。
- 包含 schema、game ID 和 revision 的权威 `GameState`。
- 确定性探索、对话效果、关键选择、场景跳转和四结局服务。
- DeepSeek 结构化对白适配器：超时、有限重试、熔断和角色化降级。
- Argon2id 密码、HttpOnly Cookie 会话、令牌摘要存储和撤销。
- 用户隔离的多槽位存档与 `save_revision` CAS 覆盖保护。
- Alembic 初始迁移，以及 SQLite/PostgreSQL 配置边界。
- Edge TTS 有界并发、SHA-256 缓存、原子落盘和容量清理。
- 内容校验命令、同域冒烟脚本和四 job GitHub Actions 流水线。

### Changed

- 后端成为内容和游戏规则唯一权威来源；前端改为提交意图并替换完整状态。
- 热区、碎片图和选择 UI 改为消费后端规范化数据。
- 前端 API 统一使用同域 `/api` 和 Credentialed Cookie。
- Nginx 同域代理 `/api/` 与 `/tts/`；容器启动前执行 Alembic。
- 健康检查不再暴露 AI Key 是否存在、Debug 状态等配置能力信息。
- Python 与前端直接依赖更新并锁定；生产依赖审计无高危发现。

### Fixed

- 修复旧前端质量基线中的 TypeScript、ESLint、Prettier、Vitest 和构建失败。
- 修复窄屏对话层遮挡热区、关闭按钮被覆盖和选择按钮不可见。
- 删除前端不存在的碎片 ID、重复状态规则和废弃路由调用。
- 删除两份未使用且无法通过 Python 编译的旧场景脚本。
- TTS 或 DeepSeek 失败不再让主剧情失去可操作性。

### Security

- 移除前端可读令牌认证和无盐 SHA-256 密码。
- CORS Credential 只允许显式来源，生产 Cookie 默认 Secure。
- 注册冲突和登录失败使用稳定、不泄露账号存在性的错误。
- 存档读取、列出、写入和删除全部限制为当前 Cookie 用户。

### Planned

- P0-B：1972 西安老巷电影级纵向切片。
- 东方皮影电影感、桌面 2.39:1 舞台、移动双构图。
- 常态动画电影写实，记忆高潮超现实化。

## [0.1.0] - Prototype

- 建立 Vue/FastAPI 原型、基础 SVG 场景、AI 对话和本地存档概念。
