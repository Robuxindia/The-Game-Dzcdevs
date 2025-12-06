# run_ursina.ps1
# Mastırs için: Ursina scriptini çalıştırır
# Kaydet: run_ursina.ps1

# Python scriptinin tam yolu (değiştirmek istersen burayı düzenle)
$scriptPath = "C:\Users\aydin\OneDrive\Desktop\The Game\ursina_main.py"

# Kontrol: script var mı?
if (-not (Test-Path $scriptPath)) {
    Write-Host "HATA: Script bulunamadı:" $scriptPath -ForegroundColor Red
    exit 1
}

# Python çalıştırıcısını bulmaya çalış
$pythonCandidates = @("py","python","python3")
$python = $null
foreach ($p in $pythonCandidates) {
    try {
        & $p -V > $null 2>&1
        $python = $p
        break
    } catch { }
}

# Bulunamadıysa kullanıcıdan tam yolu iste
if (-not $python) {
    Write-Host "Python sistem PATH'inde bulunamadı." -ForegroundColor Yellow
    $inputPath = Read-Host "Python'un tam yolunu gir (ör: C:\Python310\python.exe). İptal için boş bırak."
    if ([string]::IsNullOrWhiteSpace($inputPath)) {
        Write-Host "İşlem iptal edildi." -ForegroundColor Red
        exit 1
    }
    $python = $inputPath
}

# Çalışma dizinini scriptin olduğu klasöre ayarla (kaynak dosya yolları için)
$scriptDir = Split-Path -Path $scriptPath -Parent
if (Test-Path $scriptDir) { Set-Location $scriptDir }

# Scripti çalıştır
Write-Host "Ursina tabanli dzcdevs yapimi the game baslatiliyor..." -ForegroundColor Green
& $python $scriptPath @args

# Çalışma bittikten sonra pencere açık kalsın diye bekle
Write-Host "`Program sona erdi. Kapatmak icin Enter tusuna basabilirsin :D" -ForegroundColor Cyan
Read-Host
