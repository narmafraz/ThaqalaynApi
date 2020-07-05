$Env:PYTHONPATH = $PSScriptRoot
$Env:BACKEND_CORS_ORIGINS = "http://localhost, http://localhost:4200, http://localhost:3000, http://localhost:8080, https://localhost, https://localhost:4200, https://localhost:3000, https://localhost:8080, http://dev.thaqalayn.com, https://stag.thaqalayn.com, https://thaqalayn.com, http://local.dockertoolbox.tiangolo.com, http://localhost.tiangolo.com"
$Env:PROJECT_NAME = "Thaqalayn"

python .\data\main_add.py
