$ErrorActionPreference = "Stop"

$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$CosyVoiceDirectory = Join-Path $RepositoryRoot ".local\cosyvoice"
$CosyVoiceCommit = "074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc"
$CosyVoiceRepository = "https://github.com/QwenAudio/CosyVoice.git"
$ModelId = "FunAudioLLM/Fun-CosyVoice3-0.5B-2512"
$ModelDirectory = Join-Path $CosyVoiceDirectory "pretrained_models\Fun-CosyVoice3-0.5B"
$VirtualEnvironment = Join-Path $CosyVoiceDirectory ".venv"
$PythonExecutable = Join-Path $VirtualEnvironment "Scripts\python.exe"
$ModelScopeExecutable = Join-Path $VirtualEnvironment "Scripts\modelscope.exe"

uv python install 3.10

if (-not (Test-Path -LiteralPath (Join-Path $CosyVoiceDirectory ".git"))) {
    New-Item -ItemType Directory -Force -Path (Split-Path $CosyVoiceDirectory) | Out-Null
    git clone $CosyVoiceRepository $CosyVoiceDirectory
}

git -C $CosyVoiceDirectory fetch origin $CosyVoiceCommit
git -C $CosyVoiceDirectory checkout --detach $CosyVoiceCommit
git -C $CosyVoiceDirectory submodule update --init --recursive third_party/Matcha-TTS

uv venv --python 3.10 $VirtualEnvironment
uv pip install --python $PythonExecutable -r (Join-Path $CosyVoiceDirectory "requirements.txt")
& $ModelScopeExecutable download `
    --model $ModelId `
    --local_dir $ModelDirectory

$BridgeApp = Join-Path $RepositoryRoot "tools\cosyvoice_bridge\app.py"
Write-Host ""
Write-Host "Pinned CosyVoice source and model are ready."
Write-Host "Start the authenticated local bridge with:"
Write-Host "`$env:COSYVOICE_REPO_DIR='$CosyVoiceDirectory'; `$env:COSYVOICE_MODEL_DIR='$ModelDirectory'; `$env:COSYVOICE_BRIDGE_TOKEN='<set-a-random-secret>'; & '$PythonExecutable' -m uvicorn tools.cosyvoice_bridge.app:app --app-dir '$RepositoryRoot' --host 127.0.0.1 --port 50000"
Write-Host "Bridge source: $BridgeApp"
