import asyncio
import websockets
import argparse
from cflib import crtp
from cflib.positioning.position_hl_commander import PositionHlCommander
import formations
import json
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie import Crazyflie
from common import reset_estimator, LeaderFollowerLogger

parser = argparse.ArgumentParser(description='Follower')
parser.add_argument('URI', metavar='URI', type=str, help='URI of the Crazyflie to connect to.')
parser.add_argument("position", type=str, help="Which position transform to use")
parser.add_argument("--test-mode", dest="test_mode", action="store_true", help="Run in test mode.")

args = parser.parse_args()
TEST = args.test_mode

URI = args.URI
LOGGER = LeaderFollowerLogger(URI,1)
if not TEST:
    print("Initializing Drivers...")
    crtp.init_drivers(enable_debug_driver=False)
    LOGGER.log_trying_connection(URI)
    SCF = SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache'))
    SCF.open_link()
LOGGER.log_connected()
if not TEST:
    LOGGER.log_resetting_estimator()
    reset_estimator(SCF.cf)
    LOGGER.log_got_position()
    FOLLOWER = PositionHlCommander(SCF)
SHOULD_EXIT = False
FIRST = True
def handle_message(message: dict):
    global SHOULD_EXIT
    global FIRST
    if FIRST:
        print("Connected to leader. Recieved first message")
        FIRST = False
        return

    if message['type'] == 'shutdown':
        SHOULD_EXIT = True
        return

    if message['type'] == 'land':
        if not TEST:
            FOLLOWER.land()
        LOGGER.log_land()
        return

    if message['type'] == 'takeoff':
        if not TEST:
            FOLLOWER.take_off(height=message['height'])
        LOGGER.log_takeoff(height=message['height'])
        return

    if message['type'] == 'position':
        pos: dict = eval(f"formations.{args.position}({message['position']})")
        if not TEST:
            FOLLOWER.go_to(x=pos['x'],y=pos['y'],z=pos['z'])
        LOGGER.log_position(position=pos)
        return

    print(message)

async def connect():
    uri = f"ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        while not SHOULD_EXIT:
            m = await websocket.recv()
            handle_message(json.loads(m))

try:
    asyncio.get_event_loop().run_until_complete(connect())
finally:
    LOGGER.log_land()
    if not TEST:
        FOLLOWER.land()
        SCF.close_link()
    LOGGER.log_disconnected()



