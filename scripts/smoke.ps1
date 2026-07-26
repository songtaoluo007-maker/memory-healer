param(
    [string]$BaseUrl = "http://127.0.0.1:5173",
    [int]$Attempts = 30
)

$ErrorActionPreference = "Stop"
$base = $BaseUrl.TrimEnd("/")

function Invoke-WithRetry {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Uri
    )

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            return Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 5
        }
        catch {
            if ($attempt -eq $Attempts) {
                throw
            }
            Start-Sleep -Seconds 1
        }
    }
}

$root = Invoke-WithRetry -Uri "$base/"
if ($root.StatusCode -ne 200 -or $root.Content -notmatch "<title>") {
    throw "Frontend root smoke check failed"
}

$healthResponse = Invoke-WithRetry -Uri "$base/api/health"
$health = $healthResponse.Content | ConvertFrom-Json
if ($healthResponse.StatusCode -ne 200 -or $health.status -ne "ok" -or $health.database -ne "ok") {
    throw "Backend health smoke check failed"
}

$sceneResponse = Invoke-WithRetry -Uri "$base/api/scene/list"
$scenePayload = $sceneResponse.Content | ConvertFrom-Json
if ($sceneResponse.StatusCode -ne 200 -or $scenePayload.scenes.Count -ne 5) {
    throw "Expected exactly five scenes"
}

$gameResponse = Invoke-WithRetry -Uri "$base/api/game/new"
$game = $gameResponse.Content | ConvertFrom-Json
if (
    $gameResponse.StatusCode -ne 200 -or
    $game.state.current_scene -ne "scene_1972" -or
    $game.state.schema_version -ne 1
) {
    throw "New-game smoke check failed"
}

Write-Output "Smoke checks passed: frontend, health, 5 scenes, and authoritative new game."
