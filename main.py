import json
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect

app = FastAPI()

active_connections = {}
players = {}
lobby = {}
games = 1

@app.websocket("/ws")
async def lobby_endpoint(websocket: WebSocket):
    global games
    global lobby
    await websocket.accept()
    if games not in lobby:
        lobby[games] = []
    if websocket not in lobby.values():
        lobby[games].append(websocket)
        json_mess = json.dumps({"type": "game_id", "game_id": games})
        await websocket.send_text(json_mess)
    if len(lobby[games]) == 2:
        games += 1

@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await websocket.accept()
    if game_id not in active_connections:
        active_connections[game_id] = []
        players[game_id] = {}

    color = "white" if "white" not in players[game_id] else "black"
    players[game_id][color] = websocket
    await websocket.send_text(json.dumps({"type": "player_joined", "color": color}))

    active_connections[game_id].append(websocket)

    if len(active_connections[game_id]) == 2:
        connections = active_connections[game_id]
        for connection in connections:
            await connection.send_text(json.dumps({"type": "start_game"}))

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)


            if message["type"] == "end_game":
                for connection in list(active_connections[game_id]):
                    await connection.send_text(json.dumps({"type": "end_game"}))
            if "type" in message:
                for connection in list(active_connections[game_id]):
                    await connection.send_text(json.dumps(message))

    except WebSocketDisconnect:
        active_connections[game_id].remove(websocket)
        if len(active_connections[game_id]) == 1:
            ws: WebSocket = active_connections[game_id].pop(0)
            await ws.send_text(json.dumps({"type": "player_left"}))
            await ws.close()

        if not active_connections[game_id]:
            del active_connections[game_id]
        if color in players[game_id]:
            del players[game_id][color]