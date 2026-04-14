$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Start-Process -WindowStyle Hidden -FilePath "uv" -ArgumentList "run uvicorn app.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory $projectDir
