import uvicorn
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio
import threading
import queue
import json
from time import sleep
from EDAP_EDMesg_Interface import *

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class EDMesgWebClient:
    def __init__(self, instance_name, websocket_queue):
        self.client = None
        self.instance_name = instance_name
        self.websocket_queue = websocket_queue
        self.actions_port = 0
        self.events_port = 0

    def start(self, host, actions_port, events_port):
        self.actions_port = actions_port
        self.events_port = events_port
        self.client = create_edap_client(self.actions_port, self.events_port)
        self._client_loop_thread = threading.Thread(target=self._client_loop, daemon=True)
        self._client_loop_thread.start()

    def _client_loop(self):
        while True:
            if not self.client.pending_events.empty():
                event = self.client.pending_events.get()
                self.websocket_queue.put(f"[{self.instance_name}] {event}")
            sleep(0.1)

    def send_action(self, action_name, params=None):
        if not self.client:
            return

        action_class = globals().get(action_name)
        if action_class and issubclass(action_class, EDMesgAction):
            if params:
                action = action_class(**params)
            else:
                action = action_class()
            self.client.publish(action)
            self.websocket_queue.put(f"[{self.instance_name}] Sent action: {action_name}")
        else:
            self.websocket_queue.put(f"[{self.instance_name}] Unknown action: {action_name}")

websocket_queue = queue.Queue()
edmesg_clients = {}

@app.on_event("startup")
async def startup_event():
    with open("web_gui_config.json", "r") as f:
        config = json.load(f)

    for instance_config in config["instances"]:
        instance_name = instance_config["name"]
        client = EDMesgWebClient(instance_name, websocket_queue)
        client.start(instance_config["host"], instance_config["actions_port"], instance_config["events_port"])
        edmesg_clients[instance_name] = client

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    with open("web_gui_config.json", "r") as f:
        config = json.load(f)
    return templates.TemplateResponse("index.html", {"request": request, "instances": config["instances"]})

@app.post("/action/{instance_name}/{action_name}")
async def send_action(instance_name: str, action_name: str, request: Request):
    params = await request.json()
    if instance_name in edmesg_clients:
        edmesg_clients[instance_name].send_action(action_name, params)
        return {"status": "ok"}
    else:
        return {"status": "error", "message": "Unknown instance"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        if not websocket_queue.empty():
            message = websocket_queue.get()
            await websocket.send_text(message)
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
