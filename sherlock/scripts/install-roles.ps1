param(
    [string]$CodexHomePath = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' })
)

$ErrorActionPreference = "Stop"

$sourcePath = Join-Path $PSScriptRoot '..\roles'
$destinationPath = Join-Path $CodexHomePath 'agents\sherlock'
$backupPath = Join-Path $env:TEMP ("sherlock_roles_backup_" + [System.Guid]::NewGuid().ToString("N"))

if (-not (Test-Path -LiteralPath $sourcePath -PathType Container)) {
    throw "Sherlock rol kaynağı bulunamadı: $sourcePath"
}

# 1. Transactional Backup
$hadExisting = Test-Path -LiteralPath $destinationPath
if ($hadExisting) {
    Copy-Item -LiteralPath $destinationPath -Destination $backupPath -Recurse -Force
}

try {
    New-Item -ItemType Directory -Path $destinationPath -Force | Out-Null
    $installed = 0
    $copiedFiles = @()

    foreach ($sourceFile in Get-ChildItem -LiteralPath $sourcePath -Filter '*.toml' -File) {
        $destinationFile = Join-Path $destinationPath $sourceFile.Name
        Copy-Item -LiteralPath $sourceFile.FullName -Destination $destinationFile -Force
        $copiedFiles += $destinationFile
        $installed++
    }

    # Verify SHA-256 integrity
    foreach ($sourceFile in Get-ChildItem -LiteralPath $sourcePath -Filter '*.toml' -File) {
        $destinationFile = Join-Path $destinationPath $sourceFile.Name
        $srcHash = (Get-FileHash -LiteralPath $sourceFile.FullName -Algorithm SHA256).Hash
        $dstHash = (Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash
        if ($srcHash -ne $dstHash) {
            throw "Hash uyumsuzluğu tespit edildi: $destinationFile"
        }
    }

    if (Test-Path -LiteralPath $backupPath) {
        Remove-Item -LiteralPath $backupPath -Recurse -Force
    }

    Write-Output "Sherlock 6-Ajan Rol Kurulumu Başarılı (ACID Verified). Yüklenen dosya: $installed. Hedef: $destinationPath"
}
catch {
    Write-Warning "Rol kurulumunda hata oluştu! Otomatik geri alma (rollback) başlatılıyor: $_"
    if ($hadExisting -and (Test-Path -LiteralPath $backupPath)) {
        Remove-Item -LiteralPath $destinationPath -Recurse -Force -ErrorAction SilentlyContinue
        Copy-Item -LiteralPath $backupPath -Destination $destinationPath -Recurse -Force
        Remove-Item -LiteralPath $backupPath -Recurse -Force -ErrorAction SilentlyContinue
        Write-Output "Rollback tamamlandı: Eski durum başarıyla restore edildi."
    }
    throw $_
}
