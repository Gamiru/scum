import os
import os.path
from datetime import datetime
import mss

TEMP_SCREENSHOTS_DIRECTORY = "temp_screenshots"

def take_screenshot(monitor_number):
    with mss.mss() as sct:
        file_name_and_type = "screenshot" + "_" + datetime.now().strftime("%Y_%m_%d-%H_%M_%S_%f") + ".png"

        if not os.path.isdir(TEMP_SCREENSHOTS_DIRECTORY):
            os.mkdir(TEMP_SCREENSHOTS_DIRECTORY)

        complete_file_name = os.path.join(TEMP_SCREENSHOTS_DIRECTORY, file_name_and_type)

        # monitor_number = 0 is all monitor at once. 1 is monitor 1, 2 is monitor 2, ...
        filename = sct.shot(mon=monitor_number, output=complete_file_name)

        return filename
        # Delete screenshot


def delete_screenshot(file_path):
    # Delete screenshot file.
    # try:
    #     if os.path.isfile(file_path):
    #         os.remove(file_path)
    # except OSError as e:
    #     print ("Error deleting file: %s - %s." % (file_path, e.strerror))

    # Check if other screenshot files exists in the folder if ever. Then, delete them.
    for filename in os.listdir(TEMP_SCREENSHOTS_DIRECTORY):
        file_path = os.path.join(TEMP_SCREENSHOTS_DIRECTORY, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except OSError as e:
            print ("Error deleting file: %s - %s." % (file_path, e.strerror))


def get_monitors_count():
    with mss.mss() as sct:
        monitors = sct.monitors
        monitors_count = len(monitors) - 1 # Do not include monitor 0 (All monitors together)
    
    return monitors_count