# TemizIST — RaspberryPi_Controller klasörünü Pi'ye kopyalar (PowerShell)
$PiUser = "temizist"
$PiHost = "192.168.1.194"
$RemoteDir = "/home/temizist/TemizIST"
$LocalDir = $PSScriptRoot

Write-Host "=== TemizIST Pi deploy ===" -ForegroundColor Cyan
Write-Host "Hedef: ${PiUser}@${PiHost}:${RemoteDir}"

Write-Host "`n[1/3] Port 22 kontrol..." -ForegroundColor Yellow
$test = Test-NetConnection -ComputerName $PiHost -Port 22 -WarningAction SilentlyContinue
if (-not $test.TcpTestSucceeded) {
    Write-Host "HATA: Pi'ye ulasilamiyor (SSH port 22). IP ve agyi kontrol edin." -ForegroundColor Red
    exit 1
}

Write-Host "[2/3] Uzak klasor olusturuluyor..." -ForegroundColor Yellow
ssh "${PiUser}@${PiHost}" "mkdir -p ${RemoteDir}"
if ($LASTEXITCODE -ne 0) {
    Write-Host "HATA: SSH basarisiz." -ForegroundColor Red
    exit 1
}

Write-Host "[3/3] Dosyalar kopyalaniyor (scp)..." -ForegroundColor Yellow
scp -r "$LocalDir" "${PiUser}@${PiHost}:${RemoteDir}/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "HATA: scp basarisiz." -ForegroundColor Red
    exit 1
}

Write-Host "`nTamam. Sonraki adimlar:" -ForegroundColor Green
Write-Host "  ssh ${PiUser}@${PiHost}"
Write-Host "  cd ${RemoteDir}/RaspberryPi_Controller"
Write-Host "  chmod +x install_pi.sh && ./install_pi.sh"
Write-Host "  source venv/bin/activate && python3 main.py"
