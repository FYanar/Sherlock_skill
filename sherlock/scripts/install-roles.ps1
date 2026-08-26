#Requires -Version 5.1
<#
.SYNOPSIS
    Sherlock 6-Ajan Rol Kurulum Script'i — Evrensel Platform Desteği
.DESCRIPTION
    TOML rol dosyalarını Codex ve diğer AI araçlarının arama yollarına kopyalar.
    Codex FLAT layout: ~/.codex/agents/sherlock-*.toml  (alt dizin DEĞİL)
    Özellikler: Tam ACID rollback (fresh install + update-over-existing), SHA-256 doğrulama.
.PARAMETER CodexHomePath
    Codex ana dizini. Varsayılan: CODEX_HOME env veya ~/.codex
#>
param(
    [string]$CodexHomePath = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' })
)

$ErrorActionPreference = 'Stop'

$sourcePath = Join-Path $PSScriptRoot '..\roles'
# Codex flat layout: agents/*.toml — NOT agents/sherlock/*.toml
$agentsPath = Join-Path $CodexHomePath 'agents'
$backupPath = Join-Path $env:TEMP ("sherlock_roles_backup_" + [System.Guid]::NewGuid().ToString('N'))

if (-not (Test-Path -LiteralPath $sourcePath -PathType Container)) {
    throw "Sherlock rol kaynağı bulunamadı: $sourcePath"
}

# Ensure agents directory exists
New-Item -ItemType Directory -Path $agentsPath -Force | Out-Null

# Backup: collect existing sherlock-*.toml files (flat, no subdir)
$existingTomls = @()
try {
    $existingTomls = @(Get-ChildItem -LiteralPath $agentsPath -Filter 'sherlock-*.toml' -File -ErrorAction SilentlyContinue)
} catch { }

$hadExisting = $existingTomls.Count -gt 0
if ($hadExisting) {
    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    foreach ($f in $existingTomls) {
        Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $backupPath $f.Name) -Force
    }
    Write-Host "[INFO] Mevcut $($existingTomls.Count) TOML yedeklendi: $backupPath"
}

# Track freshly-created files for atomic rollback on fresh installs
$freshFiles = @()

try {
    $installed = 0
    foreach ($sourceFile in Get-ChildItem -LiteralPath $sourcePath -Filter '*.toml' -File) {
        # FLAT layout: ~/.codex/agents/sherlock-structural.toml
        $destFile = Join-Path $agentsPath $sourceFile.Name
        $isNew    = -not (Test-Path -LiteralPath $destFile)
        Copy-Item -LiteralPath $sourceFile.FullName -Destination $destFile -Force
        if ($isNew) { $freshFiles += $destFile }
        $installed++
    }

    # SHA-256 integrity verification
    foreach ($sourceFile in Get-ChildItem -LiteralPath $sourcePath -Filter '*.toml' -File) {
        $destFile = Join-Path $agentsPath $sourceFile.Name
        $srcHash  = (Get-FileHash -LiteralPath $sourceFile.FullName -Algorithm SHA256).Hash
        $dstHash  = (Get-FileHash -LiteralPath $destFile            -Algorithm SHA256).Hash
        if ($srcHash -ne $dstHash) { throw "Hash uyumsuzluğu: $destFile" }
    }

    # Cleanup backup on success
    if ($hadExisting -and (Test-Path -LiteralPath $backupPath)) {
        Remove-Item -LiteralPath $backupPath -Recurse -Force
    }

    Write-Host "[OK] Sherlock 6-Ajan Rol Kurulumu Tamamlandı (ACID Verified)."
    Write-Host "     Yüklenen: $installed TOML  |  Hedef: $agentsPath  (flat layout)"
    Write-Host "     Codex bu dosyaları 'sherlock-*' prefix ile otomatik keşfeder."
}
catch {
    Write-Warning "Rol kurulumunda hata! Rollback başlatılıyor: $_"

    # Fresh install rollback: remove every file we just created
    foreach ($f in $freshFiles) {
        if (Test-Path -LiteralPath $f) {
            Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue
            Write-Host "[ROLLBACK] Silindi (fresh): $f"
        }
    }

    # Update-over-existing rollback: restore from backup
    if ($hadExisting -and (Test-Path -LiteralPath $backupPath)) {
        foreach ($bf in Get-ChildItem -LiteralPath $backupPath -File) {
            Copy-Item -LiteralPath $bf.FullName -Destination (Join-Path $agentsPath $bf.Name) -Force
        }
        Remove-Item -LiteralPath $backupPath -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "[ROLLBACK] Eski durum restore edildi."
    }
    throw $_
}

