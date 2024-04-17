from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger
import time
from datetime import datetime as dt
from rich import print as pprint

def wait_for_position_estimator(scf):
    print('Waiting for estimator to find position...')

    log_config = LogConfig(name='Kalman Variance', period_in_ms=500)
    log_config.add_variable('kalman.varPX', 'float')
    log_config.add_variable('kalman.varPY', 'float')
    log_config.add_variable('kalman.varPZ', 'float')

    var_y_history = [1000] * 10
    var_x_history = [1000] * 10
    var_z_history = [1000] * 10

    threshold = 0.001

    with SyncLogger(scf, log_config) as logger:
        for log_entry in logger:
            data = log_entry[1]

            var_x_history.append(data['kalman.varPX'])
            var_x_history.pop(0)
            var_y_history.append(data['kalman.varPY'])
            var_y_history.pop(0)
            var_z_history.append(data['kalman.varPZ'])
            var_z_history.pop(0)

            min_x = min(var_x_history)
            max_x = max(var_x_history)
            min_y = min(var_y_history)
            max_y = max(var_y_history)
            min_z = min(var_z_history)
            max_z = max(var_z_history)

            # print("{} {} {}".
            #       format(max_x - min_x, max_y - min_y, max_z - min_z))

            if (max_x - min_x) < threshold and (
                    max_y - min_y) < threshold and (
                    max_z - min_z) < threshold:
                break

def reset_estimator(scf):
    scf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    scf.param.set_value('kalman.resetEstimation', '0')
    wait_for_position_estimator(scf)

class LeaderFollowerLogger():
    # 0 - Leader , 1 - Follower
    def __init__(self,URI: str,type: int):
        self.URI = URI
        self.type = type
        self.str_con = ("[yellow bold]"if type == 0 else "[magenta]")+f"{self.URI.replace('radio://', '')}"+("[/yellow bold]"if type == 0 else "[/magenta]")

    def log_position(self,position: dict):
        pprint(f"<[red]{dt.now().strftime('%H:%M:%S')}[/red]> <{self.str_con}>*️⃣MOVING TO x: [cyan]{position.get('x','UNKNOWN')}[/cyan], y: [cyan]{position.get('y','UNKNOWN')}[/cyan], z: [cyan]{position.get('z','UNKNOWN')}[/cyan],")

    def log_takeoff(self,height: float):
        pprint(f"<[red]{dt.now().strftime('%H:%M:%S')}[/red]> <{self.str_con}> ⏫ TAKING OFF height: [cyan]{height}[/cyan]m")

    def log_land(self):
        pprint(f"<[red]{dt.now().strftime('%H:%M:%S')}[/red]> <{self.str_con}> ⏬ LANDING")

    def log_resetting_estimator(self):
        pprint(f"<[red]{dt.now().strftime('%H:%M:%S')}[/red]> <{self.str_con}> 🔄RESETTING ESTIMATOR")

    def log_waiting_for_estimator(self):
        pprint(f"<[red]{dt.now().strftime('%H:%M:%S')}[/red]> <{self.str_con}> ⏳WAITING FOR ESTIMATOR")

    def log_got_position(self):
        pprint(f"<[red]{dt.now().strftime('%H:%M:%S')}[/red]> <{self.str_con}> ✅GOT POSITION")

    def log_trying_connection(self,uri: str):
        pprint(f"<[red]{dt.now().strftime('%H:%M:%S')}[/red]> <{self.str_con}> 🟡TRYING TO CONNECT TO {uri}")

    def log_connected(self):
        pprint(f"<[red]{dt.now().strftime('%H:%M:%S')}[/red]> <{self.str_con}> 🟢CONNECTED")

    def log_disconnected(self):
        pprint(f"<[red]{dt.now().strftime('%H:%M:%S')}[/red]> <{self.str_con}> 🔴DISCONNECTED")


    def log_connected_to_leader(self):
        pprint(f"<[red]{dt.now().strftime('%H:%M:%S')}[/red]> <{self.str_con}> 🟢CONNECTED TO LEADER")