import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import threading
from cflib import crtp
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie import Crazyflie
from common import reset_estimator, LeaderFollowerLogger
import uvicorn
import argparse
import asyncio

SCF = None
LEADER = None
LOGGER = None
TEST = False

app = FastAPI()


class FollowerManager:
    def __init__(self):
        self.followers = []
        self.count = 0
        self.current_position = {}
        self.lock = threading.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        print("New Follower Connected")
        # with self.lock:
        self.followers.append(websocket)
        self.count += 1
        if self.current_position:
            await websocket.send_json(self.current_position)
        else:
            await websocket.send_json({"type": "land"})

    def disconnect(self, websocket: WebSocket):
        print("Follower Disconnected")
        # with self.lock:
        self.followers.remove(websocket)
        self.count -= 1

    async def broadcast_message(self, message: dict):
        # with self.lock:
        for follower in self.followers:
            await follower.send_json(message)
                # await follower


follower_manager = FollowerManager()


@app.post("/setpos")
async def set_position(position: dict):
    await follower_manager.broadcast_message({
        "type": "position",
        "position": position
    })
    LOGGER.log_position(position)
    if not TEST:
        await asyncio.get_event_loop().run_in_executor(None, lambda: LEADER.go_to(LEADER.go_to(position["x"], position["y"], position["z"])))
    return {"message": "Position sent to all followers."}


@app.post("/takeoff")
async def takeoff(height: float = 1.0):
    await follower_manager.broadcast_message({
        "type": "takeoff",
        "height": height
    })
    LOGGER.log_takeoff(height)
    if not TEST:
        await asyncio.get_event_loop().run_in_executor(None, lambda: LEADER.take_off(height=height))
    else:
        print("Simulating Action")
        await asyncio.get_event_loop().run_in_executor(None, lambda: time.sleep(5))
    return {"message": "Takeoff command sent to all followers."}


@app.post("/shutdown")
async def shutdown():
    await follower_manager.broadcast_message({
        "type": "shutdown"
    })
    LOGGER.log_land()
    if not TEST:
        await asyncio.get_event_loop().run_in_executor(None, lambda: LEADER.land())
        SCF.close_link()
    LOGGER.log_disconnected()

    return {"message": "shutdown command sent to all followers."}


@app.post("/land")
async def land():
    await follower_manager.broadcast_message({
        "type": "land"
    })
    LOGGER.log_land()
    if not TEST:
        await asyncio.get_event_loop().run_in_executor(None, lambda: LEADER.land())
    return {"message": "Landing command sent to all followers."}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await follower_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        follower_manager.disconnect(websocket)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Leader server for drone swarm')
    parser.add_argument("URI", type=str, help="URI for leader drone")
    parser.add_argument("--test-mode", dest="test_mode", action="store_true", help="Run in test mode.")
    args = parser.parse_args()
    TEST = args.test_mode
    LOGGER = LeaderFollowerLogger(args.URI, 0)
    try:
        if not TEST:
            print("Initializing drivers...")
            crtp.init_drivers(enable_debug_driver=False)
            LOGGER.log_trying_connection(args.URI)
            SCF = Crazyflie(rw_cache='./cache')
            SCF.open_link(args.URI)
            LEADER = PositionHlCommander(SCF)
        LOGGER.log_connected()
        if not TEST:
            LOGGER.log_resetting_estimator()
            reset_estimator(SCF)
            LOGGER.log_got_position()
    except Exception as e:
        print(e)
        exit(1)
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        if not TEST:
            LOGGER.log_land()
            LEADER.land()
            SCF.close_link()
            LOGGER.log_disconnected()
