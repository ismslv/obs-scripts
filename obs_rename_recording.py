import obsstudio_sdk as obs
import easygui
from datetime import datetime
from pathlib import Path
from threading import Timer

start_delay = 5.0
default_filename = datetime.now().strftime("recording_%m-%d_%H-%M")
question_name = "How to call a file?"
question_series = "Use this as a series?"
obs_server = {
    "host": 'localhost',
    "port": 4455,
    "password": ''  # Add your password
}
file_configs = Path.home() / ".script_obs_rename"


class Observer:
    isAlive = True

    def __init__(self, cl):
        self.cl = cl
        self.cl.callback.register(
            [
                self.on_record_state_changed,
                self.on_exit_started,
            ]
        )

    def on_record_state_changed(self, data):
        if data.output_state == 'OBS_WEBSOCKET_OUTPUT_STOPPED':
            # Recording has stopped
            file = Path(data.output_path)
            name_def = default_filename
            name, q = get_saved()
            if name != '':
                q += 1
                name_def = name + "_" + str(q)
            name_new = easygui.enterbox(question_name, "OBS", name_def)
            if name_new:
                if name_new != name_def:
                    as_series = easygui.ynbox(question_series, "OBS")
                    if as_series:
                        q = 1
                        write_saved(name_new, 1)
                        name_new += "_" + str(q)
                    else:
                        write_saved('', 0)
                else:
                    write_saved(name, q)
                file.rename(Path(file.parent, name_new + file.suffix))

    def on_exit_started(self, data):
        # OBS has begun the shutdown process
        self.cl.unsubscribe()
        self.isAlive = False


def connect_obs():
    try:
        client_event = obs.EventClient(host=obs_server['host'], port=obs_server['port'], password=obs_server['password'])
    except:
        print("OBS is not started or socket is not ready!")
    else:
        observer = Observer(client_event)

        while True:
            if not observer.isAlive:
                exit()


def get_saved():
    if not file_configs.exists():
        return '', 0

    t = file_configs.read_text()
    if t:
        t_split = t.split(',')
        return t_split[0], int(t_split[1])
    else:
        return '', 0


def write_saved(name, q):
    file_configs.write_text(name + ',' + str(q))


# Uncomment if not started from OBS to start recording
# client_request = obs.ReqClient(host=obs_server['host'], port=obs_server['port'], password=obs_server['password'])
# client_request.start_record()

# Timer to let obs-socket time to initialize
# Call directly if not started from OBS
Timer(start_delay, connect_obs).start()
