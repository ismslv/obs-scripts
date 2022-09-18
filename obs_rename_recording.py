import obspython as obs
from pathlib import Path
import re
import unicodedata
import easygui
from datetime import datetime
import pyautogui
from threading import Timer


class Data:
    _template_ = None
    _name_ = None
    _askname_ = None
    _askseries_ = None
    _series_ = None
    _times_ = None
    _settings_ = None
    _titledelay_ = None


question_name = "What [name] do you prefer?"
question_series = "Will this be series?"

source_name = ""


def script_properties():
    props = obs.obs_properties_create()
    p_template = obs.obs_properties_add_text(props, "_template", "Template", obs.OBS_TEXT_DEFAULT)
    obs.obs_property_set_long_description(p_template, "[date] is current month-day\n"
                                                      "[time] is current hour-min\n"
                                                      "[src] is the source name\n"
                                                      "[name] is title\n"
                                                      "[num] is recording number (if it is series)\n"
                                                      "if empty, default is [name]_[date]_[time]"
                                                      "if series, '_[num]' is added automatically")
    p_askname = obs.obs_properties_add_bool(props, "_askname", "Ask for a title")
    obs.obs_property_set_long_description(p_askname,
                                          "Will ask for a new title after recording if template contains [name]")
    p_askseries = obs.obs_properties_add_bool(props, "_askseries", "Ask for series")
    obs.obs_property_set_long_description(p_askseries, "Will ask whether to start series if title has changed")
    p_series = obs.obs_properties_add_bool(props, "_series", "Series")
    obs.obs_property_set_long_description(p_series, "Will increment num for each recording")
    obs.obs_properties_add_text(props, "_name", "Title", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int(props, "_times", "№", 1, 1000, 1)
    p_titledelay = obs.obs_properties_add_int(props, "_titledelay", "Title capture delay", 1, 100, 1)
    obs.obs_property_set_long_description(p_titledelay, "Time in seconds to wait before capturing active window title")

    return props


def script_defaults(settings):
    obs.obs_data_set_default_string(settings, "_template", "[name]_[date]_[time]")
    obs.obs_data_set_default_bool(settings, "_askname", True)
    obs.obs_data_set_default_bool(settings, "_askseries", True)
    obs.obs_data_set_default_bool(settings, "_series", False)
    obs.obs_data_set_default_string(settings, "_name", "Untitled_recording")
    obs.obs_data_set_default_int(settings, "_times", 0)
    obs.obs_data_set_default_int(settings, "_titledelay", 5)


def script_update(settings):
    Data._template_ = obs.obs_data_get_string(settings, "_template")
    Data._askname_ = obs.obs_data_get_bool(settings, "_askname")
    Data._askseries_ = obs.obs_data_get_bool(settings, "_askseries")
    Data._series_ = obs.obs_data_get_bool(settings, "_series")
    Data._name_ = obs.obs_data_get_string(settings, "_name")
    Data._times_ = obs.obs_data_get_int(settings, "_times")
    Data._titledelay_ = obs.obs_data_get_int(settings, "_titledelay")
    Data._settings_ = settings


def script_load(settings):
    obs.obs_frontend_add_event_callback(on_event)


def on_event(event):
    global source_name
    if event == obs.OBS_FRONTEND_EVENT_RECORDING_STARTED:
        if "[src]" in Data._template_:
            Timer(Data._titledelay_, get_window_title).start()

    elif event == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        file = get_recorded_file()

        if Data._askname_ and "[name]" in Data._template_:
            input_name = ask_name(Data._name_)
            if input_name:
                if (input_name != Data._name_):
                    Data._name_ = input_name
                    obs.obs_data_set_string(Data._settings_, "_name", Data._name_)

                    if Data._askseries_:
                        toseries = ask_series()
                        if toseries:
                            Data._series_ = True
                            obs.obs_data_set_bool(Data._settings_, "_series", True)

        if Data._series_:
            if Data._times_ == 0:
                Data._times_ = 1
            else:
                Data._times_ += 1
            obs.obs_data_set_int(Data._settings_, "_times", Data._times_)

        new_name = fill_template(Data._template_, source_name, Data._name_, Data._times_)

        file_rename(file, new_name)


def get_source_name():
    current_scene = obs.obs_frontend_get_current_scene()
    scene = obs.obs_scene_from_source(current_scene)
    items = obs.obs_scene_enum_items(scene)
    source = obs.obs_sceneitem_get_source(items[0])
    source_settings = obs.obs_source_get_settings(source)
    print(obs.obs_data_get_json(source_settings))
    obs.obs_data_release(source_settings)
    return obs.obs_source_get_name(source)


def get_recorded_file():
    output = obs.obs_frontend_get_recording_output()
    output_settings = obs.obs_output_get_settings(output)
    path = obs.obs_data_get_string(output_settings, 'path')
    file_path = Path(path)
    obs.obs_data_release(output_settings)
    obs.obs_output_release(output)
    return file_path


def fill_template(t, src="", name="", num=0):
    if t == "":
        t = "[name]_[date]_[time]"
    if src == "":
        src = "source-title"
    if name == "":
        name = "title"
    if (not "[num]" in t and Data._series_):
        t += "_[num]"
    t = t.replace("[date]", datetime.now().strftime("%m-%d"))
    t = t.replace("[time]", datetime.now().strftime("%H-%M"))
    t = t.replace("[src]", src)
    t = t.replace("[name]", name)
    t = t.replace("[num]", str(num))
    return t


def file_rename(file, name_new):
    file.rename(Path(file.parent, name_new + file.suffix))


def ask_name(text):
    return easygui.enterbox(question_name, "OBS", text)


def ask_series():
    return easygui.ynbox(question_series, "OBS")


def get_window_title():
    global source_name
    name = pyautogui.getActiveWindowTitle()
    source_name = slugify(name)


def slugify(value, allow_unicode=True):
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def snake(s):
    return '_'.join(
        sub('([A-Z][a-z]+)', r' \1',
            sub('([A-Z]+)', r' \1',
                s.replace('-', ' '))).split()).lower()
