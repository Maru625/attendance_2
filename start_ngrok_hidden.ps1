$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logPath = Join-Path $projectDir "ngrok.log"
Start-Process -WindowStyle Hidden -FilePath "ngrok" -ArgumentList "http 8000 --log=stdout" -WorkingDirectory $projectDir -RedirectStandardOutput $logPath
