from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware
import os

app = FastAPI()

origins = ["*"]
TRADE_LOG_FILE = "trade_log.txt"
RUN_LOG_FILE = "run_log.txt"
ERROR_LOG_FILE = "error_log.txt"


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])


def get_list_html(contents):
    respond = "<ul>"
    respond += "".join(["<li>" + s + "</li>\n" for s in contents])
    respond += "</ul>"
    return respond


@app.get("/trade", response_class=HTMLResponse)
async def trade():
    res = "<script>setTimeout(function(){ window.location.reload(1); }, 5000)</script>"
    res += "<h1>RUN LOG</h1>"
    if os.path.exists(RUN_LOG_FILE):
        with open(RUN_LOG_FILE, 'r') as f:
            run_content = f.readlines()
        res += get_list_html(run_content[-10:][::-1])
    res += "<h1>ERROR LOG</h1>"
    if os.path.exists(ERROR_LOG_FILE):
        with open(ERROR_LOG_FILE, 'r') as f:
            error_content = f.readlines()
        res += get_list_html(error_content[-10:][::-1])
    res += "<h1>TRADE LOG</h1>"
    if os.path.exists(TRADE_LOG_FILE):
        with open(TRADE_LOG_FILE, 'r') as f:
            trade_content = f.readlines()
        res += get_list_html(trade_content[::-1])
    res += "<style> * {font-family: courier;}</style>"
    return res

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app='main:app', host="0.0.0.0",
                    port=8889, reload=False, debug=False)
