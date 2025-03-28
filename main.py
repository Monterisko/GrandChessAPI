import json
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect

app = FastAPI()

active_connections = {}
players = {}

@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await websocket.accept()
    if game_id not in active_connections:
        active_connections[game_id] = []
        players[game_id] = {}

    color = "white" if "white" not in players[game_id] else "black"
    players[game_id][color] = websocket

    active_connections[game_id].append(websocket)

    join_message = json.dumps({"type": "player_joined", "color": color})
    for connection in list(active_connections[game_id]):
        await connection.send_text(join_message)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            print("Odebrana wiadomość:", message)

            if "type" in message:
                for connection in list(active_connections[game_id]):
                    await connection.send_text(json.dumps(message))

    except WebSocketDisconnect:
        active_connections[game_id].remove(websocket)
        if not active_connections[game_id]:
            del active_connections[game_id]
        if color in players[game_id]:
            del players[game_id][color]