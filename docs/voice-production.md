# 电影语音生产与运行手册

本项目的默认语音路径是：

1. 用锁定的 `edge-tts==7.2.8` 直接调用 Edge 托管云语音，生成 1972 第一幕候选；
2. 候选留在 `.codex-run/voice-renders`，人工审核后由脚本校验并原子晋升；
3. 游戏优先播放随包发布的批准固定资产，动态对白使用 Edge；
4. 可选 HTTPS 远程 primary 默认关闭，任何语音失败都降级为可继续的文字玩法。

禁止把真人录音用作提示、seed、训练或微调数据。默认 Edge 流程没有 seed 文件。
如果未来外部远程供应商确实要求 seed，只能由该供应商使用纯合成来源，并在其
外部生产记录中保存不可变的 provenance JSON；不得把真人样本或任何 seed
artifact 带入本仓库、镜像或运行卷。

## 生产前检查

从仓库根目录运行：

```powershell
python -m pip install -r requirements.txt
python -c "import importlib.metadata; assert importlib.metadata.version('edge-tts') == '7.2.8'"
ffmpeg -version
ffprobe -version
python scripts/validate_content.py
```

`ffmpeg` 和 `ffprobe` 必须在 `PATH`。这些命令不会安装或启动任何本地语音
推理服务。

## Edge dry-run 与第一幕候选

先做无网络 dry-run；输出必须是七条 1972 固定台词：

```powershell
python scripts/voice/generate_fixed_assets.py --scene scene_1972 --dry-run
```

确认脚本计划后调用 Edge 托管云生成候选。此步骤需要出站网络：

```powershell
python scripts/voice/generate_fixed_assets.py --scene scene_1972 --candidate-mode
```

候选音频写入 `.codex-run/voice-renders/fixed`，候选 manifest 写入
`.codex-run/voice-renders/voice_assets.candidate.json`，不会进入运行时资产目录。

在试听前执行结构预检：

```powershell
$renderRoot = Join-Path (Get-Location) ".codex-run/voice-renders"
$manifestPath = Join-Path $renderRoot "voice_assets.candidate.json"
$candidates = @(Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json)
if ($candidates.Count -ne 7) { throw "Expected exactly seven 1972 candidates." }
if (@($candidates | Where-Object { $_.approved -ne $false }).Count -ne 0) {
    throw "Candidates must remain unapproved before promotion."
}
foreach ($candidate in $candidates) {
    $audioPath = Join-Path $renderRoot $candidate.filename
    if (-not (Test-Path -LiteralPath $audioPath -PathType Leaf)) {
        throw "Missing candidate audio: $audioPath"
    }
}
```

人工审核语气、角色一致性、可懂度、爆音、截断、响度和 cue。不要直接编辑
`backend/data/voice_assets.json`，也不要把未批准候选复制进
`backend/data/voice_public/fixed`。

## 校验与原子晋升

晋升命令先在 staging 中把候选标为批准并执行完整媒体/manifest 校验，再写入
内容寻址的不可变目录 `voice_public/releases/<bundle-sha256>/`。release 完整写入
并在同一文件系统原子改名后，脚本才原子替换 manifest；因此并发读者只会看到
完整旧包或完整新包。切换不删除旧 `fixed/` 或 release，manifest 替换失败时旧包
仍保持活动：

```powershell
python scripts/voice/generate_fixed_assets.py --scene scene_1972 --promote
python scripts/voice/validate_voice_assets.py
python scripts/validate_content.py
git diff --check
```

成功后应看到七条批准资产且活动 release 没有 stale file。现有 legacy manifest
可继续引用 `fixed/*.opus`；下一次晋升会把新 manifest 切换为
`releases/<bundle-sha256>/*.opus`。提交前只纳入经审核的活动 release 与
`backend/data/voice_assets.json`；`.codex-run` 中的 raw、cache 和候选不是发布
资产。

旧 release 只能在应用已离线且确认没有读者时显式清理：

```powershell
python scripts/voice/generate_fixed_assets.py --scene scene_1972 --prune-releases --confirm-offline
```

不要在在线晋升路径中删除旧 release。

## 缓存清理

批准固定资产与缓存严格分离。下列命令只删除三个明确目录中的文件，不会触碰
`backend/data/voice_public/fixed`：

```powershell
$cacheRoots = @(
    ".codex-run/voice-renders/edge-cache",
    "backend/data/voice_public/cache",
    "data/tts_cache"
)
foreach ($cacheRoot in $cacheRoots) {
    if (Test-Path -LiteralPath $cacheRoot -PathType Container) {
        Get-ChildItem -LiteralPath $cacheRoot -File | Remove-Item -Force
    }
}
```

Compose 中整个 `backend/data/voice_public` 只读挂载到容器，`voice-cache`
以更具体的嵌套挂载保持可写，`tts-cache` 也是独立可写卷。不要把 seed、模型或
权重目录加入 Compose。

## 可选远程 primary 与降级演练

默认保持：

```dotenv
VOICE_PRIMARY_ENABLED=false
VOICE_PRIMARY_BASE_URL=
VOICE_PRIMARY_TOKEN=
```

仅当已有受控的外部 HTTPS JSON 服务时才设置
`VOICE_PRIMARY_ENABLED=true`。远程适配器只发送文本、声音档案标识、情绪、
强度和缓存键，并使用 Bearer token；配置会拒绝空 token、HTTP、localhost
和 loopback URL。

先运行无网络依赖的 primary→Edge 失败演练：

```powershell
python -m pytest backend/tests/application/test_voice_service.py::test_voice_service_falls_back_to_edge_without_blocking_text -q
python -m pytest backend/tests/application/test_voice_service.py::test_voice_fallback_emits_structured_metrics_without_player_text -q
```

需要联调真实 Edge fallback 时，在测试终端设置一个不可达的保留域名来模拟可选
远程 primary 失败，再启动后端：

```powershell
$env:VOICE_PRIMARY_ENABLED = "true"
$env:VOICE_PRIMARY_BASE_URL = "https://voice-primary.invalid"
$env:VOICE_PRIMARY_TOKEN = "failure-drill-only"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

另开终端发起请求：

```powershell
$body = @{
    text = "文字必须继续，语音允许降级。"
    npc_id = "chen_shouyi_young"
    emotion = "neutral"
    intensity = 0.2
} | ConvertTo-Json
$result = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/api/voice/speak" `
    -ContentType "application/json" `
    -Body $body
if ($result.provider -notin @("edge", "silent")) {
    throw "Expected Edge fallback or complete silent degradation."
}
```

有 Edge 网络时预期 `provider=edge`；Edge 也不可用时预期 `provider=silent`、
`url=null`，但 HTTP 请求和文字内容仍成功。结束后移除演练变量：

```powershell
Remove-Item Env:VOICE_PRIMARY_ENABLED -ErrorAction SilentlyContinue
Remove-Item Env:VOICE_PRIMARY_BASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:VOICE_PRIMARY_TOKEN -ErrorAction SilentlyContinue
```

完整静默降级的确定性验收命令是：

```powershell
python -m pytest backend/tests/application/test_voice_service.py::test_all_provider_failures_return_stable_silent_result -q
python -m pytest backend/tests/application/test_voice_service.py::test_complete_voice_failure_emits_silent_degradation_metric -q
```

## 可观测性与隐私

每次语音请求只投递一个 JSON `voice_synthesis` 事件，例如：

```json
{"asset_hit":false,"cache_hit":false,"event":"voice_synthesis","fallback":true,"latency_ms":25.0,"provider":"edge","silent_degradation":false}
```

聚合以下字段：

- `provider`：`fixed`、`remote`、`edge` 或 `silent`；
- `cache_hit`：动态远程/Edge 运行时缓存是否命中；固定资产始终为 `false`；
- `asset_hit`：是否命中批准固定资产；
- `latency_ms`：从编排入口到最终结果的毫秒数；
- `fallback`：已配置的远程 primary 未产出最终结果，转入 Edge/静默路径；
- `silent_degradation`：最终无音频但文字玩法继续。

事件不得记录完整玩家文本、远程 token、seed 内容、音频正文或个人联系方式。
请求线程只向有界队列执行非阻塞投递；队列满时丢弃指标，后台 worker 隔离日志
收集器异常。应用关闭时会停止并回收 worker，任何指标问题都不能阻断语音结果
或文字玩法。
