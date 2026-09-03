# Stable Audio Open only — runs alongside download-weights.ps1 (Bark/ACE-Step) without
# touching the same files, so both can download in parallel over the shared connection.
$ErrorActionPreference = "Continue"

function Get-RemoteSize($url, $token) {
    for ($j = 1; $j -le 60; $j++) {
        $args = @("-sI", "-L", "--connect-timeout", "15", $url)
        if ($token) { $args = @("-H", "Authorization: Bearer $token") + $args }
        $h = & curl.exe @args 2>$null | Select-String -Pattern "^content-length:" | Select-Object -Last 1
        if ($h) { return [int64](($h -replace '[^\d]', '')) }
        Start-Sleep -Seconds 5
    }
    return 0
}

function Get-File($url, $dest, $token = $null) {
    $dir = Split-Path $dest -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $want = Get-RemoteSize $url $token
    if ($want -eq 0) { Write-Host "GAVE UP (no size after retries): $dest"; return }

    for ($i = 1; $i -le 300; $i++) {
        $have = if (Test-Path $dest) { (Get-Item $dest).Length } else { 0 }
        if ($have -ge $want) {
            Write-Host ("OK {0}  ({1:N0} MB)" -f (Split-Path $dest -Leaf), ($want / 1MB))
            return
        }
        Write-Host ("  {0} attempt {1}: {2:N0}/{3:N0} MB" -f (Split-Path $dest -Leaf), $i, ($have / 1MB), ($want / 1MB))
        $curlArgs = @("-L", "--fail", "--connect-timeout", "20", "--speed-limit", "2048", "--speed-time", "30", "-C", "-", "-o", $dest, $url, "--silent", "--show-error")
        if ($token) { $curlArgs = @("-H", "Authorization: Bearer $token") + $curlArgs }
        & curl.exe @curlArgs
        Start-Sleep -Seconds 3
    }
    Write-Host "GAVE UP: $dest"
}

# Все пути к весам берутся из MUSITION_MODELS_DIR (переменная среды или .env рядом со скриптом).
$modelsDir = $env:MUSITION_MODELS_DIR
if (-not $modelsDir -and (Test-Path "$PSScriptRoot\.env")) {
    $modelsDir = ((Get-Content "$PSScriptRoot\.env" | Where-Object { $_ -match '^\s*MUSITION_MODELS_DIR\s*=' }) -split '=', 2)[1]
}
if (-not $modelsDir) { throw "MUSITION_MODELS_DIR не задан (см. README)" }
$modelsDir = $modelsDir.Trim().Trim('"').Trim("'")

$saoTok = ((Get-Content "$PSScriptRoot\.env" | Where-Object { $_ -match '^\s*HF_TOKEN\s*=' }) -split '=', 2)[1].Trim().Trim('"').Trim("'")
$saoDir = "$modelsDir\stable-audio-open-1.0"
$saoFiles = @(
    "model_index.json", "model_config.json", "LICENSE.md",
    "scheduler/scheduler_config.json",
    "transformer/config.json", "transformer/diffusion_pytorch_model.safetensors",
    "vae/config.json", "vae/diffusion_pytorch_model.safetensors",
    "text_encoder/config.json", "text_encoder/model.safetensors",
    "tokenizer/tokenizer.json", "tokenizer/tokenizer_config.json", "tokenizer/spiece.model", "tokenizer/special_tokens_map.json",
    "projection_model/config.json", "projection_model/diffusion_pytorch_model.safetensors"
)
foreach ($p in $saoFiles) {
    Get-File "https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/main/$p" "$saoDir\$p" $saoTok
}

Write-Host "SAO DOWNLOAD FINISHED"
