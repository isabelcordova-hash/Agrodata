param([switch]$Rebuild)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath "backend/.env")) { throw "Crea backend/.env a partir de backend/.env.example" }
$postgresBin = "C:/Program Files/PostgreSQL/17/bin"
$pythonExe = Join-Path $projectRoot "backend/.venv/Scripts/python.exe"
$backendRoot = Join-Path $projectRoot "backend"
$frontendRoot = Join-Path $projectRoot "frontend"
$nodeExe = (Get-Command node.exe).Source
$nextEntry = Join-Path $frontendRoot "node_modules/next/dist/bin/next"
function Test-Endpoint([string]$Url) {
    try { return (Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200 }
    catch { return $false }
}
function Wait-Endpoint([string]$Url, [System.Diagnostics.Process]$ServerProcess) {
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        if (Test-Endpoint $Url) { return }
        if ($ServerProcess.HasExited) { throw "El servidor termino. Revisa api-error.log o frontend-error.log." }
        Start-Sleep -Milliseconds 500
    }
    throw "El servidor no respondio en $Url. Revisa los logs."
}
if (Test-Path -LiteralPath ".pgdata/PG_VERSION") {
    & "$postgresBin/pg_ctl.exe" -D .pgdata status | Out-Null
    if ($LASTEXITCODE -ne 0) {
        & "$postgresBin/pg_ctl.exe" -D .pgdata -l postgres.log -o "-p 55432 -h 127.0.0.1" start
        if ($LASTEXITCODE -ne 0) { throw "No se pudo iniciar PostgreSQL" }
    }
}
if (Test-Endpoint "http://127.0.0.1:8000/health") {
    Write-Host "API activa; se reutiliza."
} else {
    $apiListener = Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($apiListener) { throw "El puerto 8000 esta ocupado y la API no responde correctamente." }
    $apiProcess = Start-Process -FilePath $pythonExe -ArgumentList @("-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000") -WorkingDirectory $backendRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot "api.log") -RedirectStandardError (Join-Path $projectRoot "api-error.log") -PassThru
    Wait-Endpoint "http://127.0.0.1:8000/health" $apiProcess
}
$frontendReady = Test-Endpoint "http://127.0.0.1:3000"
if ($frontendReady -and -not $Rebuild) {
    Write-Host "Frontend activo; se reutiliza. Usa -Rebuild para recompilar."
} else {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort 3000 -ErrorAction SilentlyContinue)
    foreach ($listener in $listeners) {
        $ownerProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)"
        $commandLine = $ownerProcess.CommandLine.Replace('/', '\')
        if (-not $commandLine.Contains($frontendRoot) -or $commandLine -notmatch 'next.* start ') {
            throw "El puerto 3000 pertenece a otro proceso. Detenlo en su terminal antes de continuar."
        }
        Stop-Process -Id $listener.OwningProcess
    }
    $buildDirectory = Join-Path $frontendRoot ".next-production"
    if ($Rebuild -or -not (Test-Path (Join-Path $buildDirectory "required-server-files.json")) -or -not (Test-Path (Join-Path $buildDirectory "BUILD_ID"))) {
        Write-Host "Compilando frontend para produccion..."
        Push-Location -LiteralPath $frontendRoot
        try {
            & $nodeExe $nextEntry build
            if ($LASTEXITCODE -ne 0) { throw "Fallo la compilacion; el frontend no se iniciara." }
        } finally { Pop-Location }
    }
    $frontendProcess = Start-Process -FilePath $nodeExe -ArgumentList @(('"' + $nextEntry + '"'),"start","--hostname","127.0.0.1","--port","3000") -WorkingDirectory $frontendRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot "frontend.log") -RedirectStandardError (Join-Path $projectRoot "frontend-error.log") -PassThru
    Wait-Endpoint "http://127.0.0.1:3000" $frontendProcess
}
Write-Host "AgroData verificado: http://localhost:3000 | API: http://localhost:8000/docs"
