from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import os

app = FastAPI()

origins = ["*"]
TRADE_LOG_FILE = "trade_log.txt"
RUN_LOG_FILE = "run_log.txt"


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])


@app.get("/trade")
async def trade():
    if os.path.exists(TRADE_LOG_FILE):
        with open(TRADE_LOG_FILE, 'r') as f:
            content = f.read()
        return content
    else:
        return None

@app.get("/run")
async def run():
    if os.path.exists(RUN_LOG_FILE):
        with open(RUN_LOG_FILE, 'r') as f:
            content = f.readlines()
        return ''.join(content[-10:])
    else:
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app='main:app', host="0.0.0.0",
                    port=8889, reload=True, debug=False)
