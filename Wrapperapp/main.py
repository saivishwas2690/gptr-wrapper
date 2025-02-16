import asyncio
import json
import asyncpg
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pathlib import Path
from pydantic import BaseModel
from urllib.parse import unquote
import os

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
INDEX_HTML_PATH = BASE_DIR / "templates" / "index.html"

GPT_RESEARCHER_WS = "ws://127.0.0.1:8000/ws"

class MarkdownRequest(BaseModel):
    file_path: str

@app.get("/")
async def home():
    return FileResponse(INDEX_HTML_PATH)


@app.websocket("/ws/client")
async def websocket_client_endpoint(client_ws: WebSocket):
    """WebSocket connection: Maintains persistent connection between client and GPTResearcher."""
    await client_ws.accept()

    try:
        async with websockets.connect(GPT_RESEARCHER_WS, ping_interval=30) as gpt_ws:  
            print("Connected to GPTResearcher WebSocket")

            while True:
                try:
                    data = await client_ws.receive_text()
                    print(f"Received from client: {data}")

                    structured_data = {
                        "agent": "Auto Agent",
                        "report_source": "web",
                        "report_type": "research_report",
                        "source_urls": [],
                        "task": data,
                        "tone": "Objective"
                    }

                    str_data = "start " + json.dumps(structured_data)
                    await gpt_ws.send(str_data)

                    while True:
                        response = await gpt_ws.recv()
                        print(f"Received from GPTResearcher: {response}")

                        if not response:
                            break  

                        await client_ws.send_text(response)


                except WebSocketDisconnect:
                    print("Client disconnected")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("GPTResearcher WebSocket disconnected. Reconnecting...")
                    break  
                except Exception as e:
                    print(f"Error in WebSocket loop: {e}")
                    break

    except Exception as e:
        print(f"Error connecting to GPTResearcher: {e}")

    finally:
        await db_conn.close()
# start {"agent": "Auto Agent","report_source": "web","report_type": "research_report","source_urls": [],"task": "DeepSeek","tone": "Objective"}
# chat {"message": "What is the capital of France?"}
@app.post("/fetch-markdown")
async def fetch_markdown(request: MarkdownRequest):
    """
    Fetch and serve the markdown file
    """
    try:
        file_path = request.file_path.replace("%20", " ")

        if file_path.startswith(".\\"):
            file_path = file_path[2:]

        file_path = file_path.replace("\\", "/")
        
        print(f"Cleaned file path: {file_path}")

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")

            parent_path = os.path.join("..", file_path)
            print(f"Trying parent directory: {parent_path}")
            if os.path.exists(parent_path):
                file_path = parent_path
            else:
                raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
 
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return PlainTextResponse(content)
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))