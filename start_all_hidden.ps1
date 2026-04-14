$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $projectDir "start_server_hidden.ps1")
Start-Sleep -Seconds 2
& (Join-Path $projectDir "start_ngrok_hidden.ps1")
