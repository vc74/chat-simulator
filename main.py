from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# In-memory storage
messages = {}
message_id = 0
connections = []

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get():
    with open("static/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    global message_id
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get('action')
            
            if action == 'send':
                message_id += 1
                messages[message_id] = data['message']
                await broadcast({"id": message_id, "message": data['message'], "action": "send"})

            elif action == 'update':
                msg_id = data['id']
                if msg_id in messages:
                    messages[msg_id] = data['message']
                    await broadcast({"id": msg_id, "message": data['message'], "action": "update"})

            elif action == 'delete':
                msg_id = data['id']
                if msg_id in messages:
                    del messages[msg_id]
                    await broadcast({"id": msg_id, "action": "delete"})

    except WebSocketDisconnect:
        connections.remove(websocket)

async def broadcast(message: dict):
    for conn in connections:
        await conn.send_json(message)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)