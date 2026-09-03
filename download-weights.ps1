# Downloads model weights over an unstable connection.
# ponytail: the link here drops constantly. Traps found the hard way:
#   1. hf_hub's retry starts a NEW temp file each attempt -> a 5GB file never finishes.
#   2. curl --retry resumes from the offset it computed at STARTUP, so a mid-transfer
#      drop throws away everything gained in that attempt.
#   3. A HEAD request (to learn the file size) can ALSO hit the outage; treating that
#      as "file doesn't exist" silently skips the file forever. Retry the HEAD too.
#   4. An uncaught network exception (e.g. from Invoke-RestMethod) kills the whole script,
#      not just one file. Every network call in here is retried in a loop, nothing throws out.
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
        # --speed-limit/--speed-time: abort and retry if throughput drops to ~0 for 30s straight,
        # instead of hanging forever on a half-dead connection that DNS/new-TCP checks won't catch.
        $curlArgs = @("-L", "--fail", "--connect-timeout", "20", "--speed-limit", "2048", "--speed-time", "30", "-C", "-", "-o", $dest, $url, "--silent", "--show-error")
        if ($token) { $curlArgs = @("-H", "Authorization: Bearer $token") + $curlArgs }
        & curl.exe @curlArgs
        Start-Sleep -Seconds 3
    }
    Write-Host "GAVE UP: $dest"
}

function Get-JsonRetry($url) {
    for ($j = 1; $j -le 60; $j++) {
        try { return Invoke-RestMethod $url -TimeoutSec 20 } catch { Start-Sleep -Seconds 5 }
    }
    return $null
}

$barkDir = "D:\AIModels\SoundGen\_xdg_cache\suno\bark_v0"
foreach ($f in @("text_2.pt", "coarse_2.pt", "fine_2.pt")) {
    Get-File "https://huggingface.co/suno/bark/resolve/main/$f" "$barkDir\$f"
}

$aceDir = "D:\AIModels\SoundGen\ace-step-cache\checkpoints\ACE-Step-v1-3.5B"
$tree = Get-JsonRetry "https://huggingface.co/api/models/ACE-Step/ACE-Step-v1-3.5B/tree/main?recursive=1"
if ($null -eq $tree) {
    Write-Host "GAVE UP: could not list ACE-Step repo tree"
} else {
    foreach ($item in $tree | Where-Object { $_.type -eq "file" }) {
        Get-File "https://huggingface.co/ACE-Step/ACE-Step-v1-3.5B/resolve/main/$($item.path)" "$aceDir\$($item.path -replace '/', '\')"
    }
}

Write-Host "ALL DOWNLOADS FINISHED"
