import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

rooms = {}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    client_id = str(uuid.uuid4())[:8]

    if room_id not in rooms:
        rooms[room_id] = {}

    for c_id, ws in rooms[room_id].items():
        await ws.send_json({"type": "user-joined", "clientId": client_id})

    rooms[room_id][client_id] = websocket

    try:
        while True:
            data = await websocket.receive_json()
            target_id = data.get("target")

            if target_id and target_id in rooms[room_id]:
                data["sender"] = client_id
                await rooms[room_id][target_id].send_json(data)
            else:
                for c_id, ws in rooms[room_id].items():
                    if c_id != client_id:
                        data["sender"] = client_id
                        await ws.send_json(data)

    except WebSocketDisconnect:
        del rooms[room_id][client_id]
        if not rooms[room_id]:
            del rooms[room_id]
        else:
            for ws in rooms[room_id].values():
                await ws.send_json({"type": "user-left", "clientId": client_id})