## 준비 사항

[Azure Functions 핵심 도구 설치](https://learn.microsoft.com/ko-kr/azure/azure-functions/functions-run-local?tabs=windows%2Cisolated-process%2Cnode-v4%2Cpython-v2%2Chttp-trigger%2Ccontainer-apps&pivots=programming-language-python)


아래 환경변수를 작성하고 Powershell 또는 vscode 의 terminal 에서 실행
```powershell
$env:MicrosoftAppId = "<azure bot 의 appId>"
$env:MicrosoftAppPassword = "<Entra ID 의 앱등록에서 설정한 azure bot 의 secret>"
$env:AZURE_OPENAI_KEY = "<AZURE_OPENAI_KEY>"
$env:AZURE_OPENAI_ENDPOINT = "https://<OpenAI이름>.openai.azure.com/"
$env:AZURE_OPENAI_VERSION = "2024-02-15-preview"
$env:APPLICATIONINSIGHTS_CONNECTION_STRING = "<APPLICATIONINSIGHTS_CONNECTION_STRING>"

```