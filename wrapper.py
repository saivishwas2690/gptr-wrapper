import asyncio
import websockets
import json

async def send_and_receive():
    uri = "ws://127.0.0.1:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        try:
            data = {
                "agent": "Auto Agent",
                "report_source": "web",
                "report_type": "research_report",
                "source_urls": [],
                "task": "Open AI vs Deepseek",
                "tone": "Objective"
            }

            action = "chat "

            json_string = action + json.dumps(data) 
            await websocket.send(json_string)  
            print("JSON string sent!")

            while True: 
                response = await websocket.recv()
                try:
                    response_json = json.loads(response) 
                    formatted_response = json.dumps(response_json, indent=4)  
                    print("Received Response:\n", formatted_response)
                except json.JSONDecodeError:
                    print("Received (non-JSON response):", response)

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed, exiting...")

asyncio.run(send_and_receive())


