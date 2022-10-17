import PySimpleGUI as sg
from pynput import keyboard
from psgtray import SystemTray
import constants
import minecraft_chest_sorter
import screenshot_handler
from just_playback import Playback
import random

APP_NAME = "SCUM"

DEFAULT_FONT = "Any"

ICON_64x64_PNG_FILENAME = "icon/minecraft_chest_sorter_icon_64x64-01.png"
ICON_32x32_ICO_FILENAME = "icon/minecraft_chest_sorter_icon_32x32-01.ico"

MONITORS_COUNT = screenshot_handler.get_monitors_count()
MONITOR_NUMBER_OPTIONS = list(range(1, MONITORS_COUNT + 1)) if (MONITORS_COUNT != None and MONITORS_COUNT > 0) else 1 
MONITOR_NUMBER_DEFAULT_OPTION = 1
MONITOR_NUMBER_COMBO_KEY = "-MONITOR_NUMBER_COMBO-"

SORT_TYPE_OPTIONS = list(constants.SORT_TYPES.values())
SORT_TYPE_DEFAULT_OPTION = SORT_TYPE_OPTIONS[0]
SORT_TYPE_COMBO_KEY = "-SORT_TYPE_COMBO-"

HOTKEY = "F9"
SORT_KEY = "-START_SORT-"
OUTPUT_MSG_MULTILINE_KEY = "-OUTPUT_MSG_MULTILINE-"

# Global variables. Initialized to default.
window = None
tray = None

sg.theme("DarkTeal10")

playback1 = Playback()
playback1.load_file("audio/1.mp3")

playback2 = Playback()
playback2.load_file("audio/2.mp3")

top_banner = [
    [
        sg.Image(ICON_64x64_PNG_FILENAME, size=(64, 64)),
        sg.Column([
            [sg.Text(APP_NAME, font=(DEFAULT_FONT, 26, "bold"), pad=(0, 0))],
            [sg.Text("Sorter of Chests Using Mouse", font=(DEFAULT_FONT, 9), pad=(0, 0))]
        ], pad=(10, 0))
    ]
]

block_1 = [
    [
        sg.Text("Monitor number:"),
        sg.Column([
            [sg.Combo(MONITOR_NUMBER_OPTIONS, default_value=MONITOR_NUMBER_DEFAULT_OPTION, readonly=True, key=MONITOR_NUMBER_COMBO_KEY)]
        ], expand_x=True, element_justification="right", pad=(0, 0))
    ],
    [
        sg.Text("Sort by:"),
        sg.Column([
            [sg.Combo(SORT_TYPE_OPTIONS, default_value=SORT_TYPE_DEFAULT_OPTION, readonly=True, key=SORT_TYPE_COMBO_KEY)]
        ], expand_x=True, element_justification="right", pad=(0, 0))
    ],
    [
        sg.Text("Sort Hotkey:"),
        sg.Column([
            [sg.Text(HOTKEY)]
        ], expand_x=True, element_justification="right", pad=(0, 0))
    ]
]

block_2 = [
    [sg.Text("Instruction:")],
    [
        sg.Column([
            [sg.Text("1.")],
            [sg.Text("")] 
        ], pad=(0, 0)),
        sg.Column([
            [sg.Text("Make sure Minecraft is not on fullscreen mode.")],
            [sg.Text("(Maximized windowed mode is fine)")]
        ], pad=(0, 0))
    ],
    [
        sg.Text("2."), 
        sg.Column([
            [sg.Text("Open the chest that you want to sort.")]
        ], pad=(0, 0))
    ],
    [
        sg.Column([
            [sg.Text("3.")],
            [sg.Text("")],
            [sg.Text("")]
        ], pad=(0, 0)),
        sg.Column([
            [sg.Text("Press F9 key or click the Sort button.")],
            [sg.Text("(The Hotkey works even if this app is minimized)")],
            [sg.Text("Don't move the mouse while it is sorting.")]
        ], pad=(0, 0))
    ]
]

block_3 = [
    [
        sg.Column([
            [sg.Button("Sort", key=SORT_KEY, expand_x=True), sg.Exit(button_color=("#FFFFFF", "#872f2f"))]
        ], expand_x=True, element_justification="right", pad=(0, 0))
    ]
]

block_4 = [
    [sg.Text("Output message:")],
    [sg.Multiline(disabled=True, size=(35, 5), expand_x=True, key=OUTPUT_MSG_MULTILINE_KEY)],
]

layout = [
    [sg.Column(top_banner, pad=((0, 0), (0, 0)))],
    [
        sg.Column([
            [sg.Column(block_1, expand_x=True, pad=(0, 0))],
            [sg.Column(block_2, expand_x=True, pad=((0, 0), (20, 0)))]
        ], expand_x=True, pad=((0, 0), (20, 0)))
    ],
    [sg.Column(block_3, expand_x=True, pad=((0, 0), (20, 0)))],
    [sg.Column(block_4, expand_x=True, pad=((0, 0), (20, 0)))]
]


def hotkey_on_press(key):
    if key == keyboard.Key.f9:
        event = SORT_KEY
        window.write_event_value(event, "")


def start_btn_event(event, values):
    monitor_number = values[MONITOR_NUMBER_COMBO_KEY]
    sort_type = values[SORT_TYPE_COMBO_KEY]
    sort_return_val = minecraft_chest_sorter.sort(monitor_number, sort_type)

    # Update Multiline element.
    if sort_return_val == constants.SORT_RETURN_SUCCESS:
        multiline_msg = "Success!"
    else:
        multiline_msg = sort_return_val
    window[OUTPUT_MSG_MULTILINE_KEY].update(multiline_msg)

    global tray
    tray.show_message(APP_NAME, multiline_msg)

    # Play sound.
    if random.randint(0, 100) < 50:
        playback1.play()
    else:
        playback2.play()


def main(args=None):
    global window
    window = sg.Window(
        title=APP_NAME, 
        icon=ICON_32x32_ICO_FILENAME,
        layout=layout, 
        resizable=False, 
        margins=(15, 10), 
        finalize=True, 
        enable_close_attempted_event=True)

    # Start global hotkey listener.
    hotkey_listener =  keyboard.Listener(on_press=hotkey_on_press, on_release=None)
    hotkey_listener.start()

    # System Tray
    menu = ["", ["Show", "---", "Exit"]]
    tooltip = APP_NAME
    global tray
    tray = SystemTray(menu, single_click_events=False, window=window, tooltip=tooltip, icon=ICON_32x32_ICO_FILENAME)
    tray.show_message(APP_NAME, "System Tray icon started.")

    while True:
        event, values = window.read()
        # print(event, values)

        # IMPORTANT step. It's not required, but convenient.
        # If it's a tray event, change the event variable to be whatever the tray sent.
        if event == tray.key:
            event = values[event]   # Use the System Tray's event as if was from the window

        if event in (sg.WIN_CLOSED, "Exit"):
            break

        if event == SORT_KEY:
            start_btn_event(event, values)
        elif event in ("Show", sg.EVENT_SYSTEM_TRAY_ICON_DOUBLE_CLICKED):
            window.un_hide()
            window.bring_to_front()
        elif event in (sg.WIN_CLOSE_ATTEMPTED_EVENT):
            window.hide()
            tray.show_icon()    # If hiding window, better make sure the icon is visible.
            tray.show_message(title=APP_NAME, message="Minimized to System Tray.")

    tray.close()    # Optional but without a close, the icon may "linger" until moused over.
    window.close()

if __name__ == "__main__":
    main()