import colorlog
import datetime
import logging
import os
from pathlib import Path

# Check if file logging is disabled via environment variable
if os.environ.get('DISABLE_FILE_LOGGING') != '1':
    _filename = 'autopilot.log'

    # Rename existing log file to create new one.
    if os.path.exists(_filename):
        try:
            filename_only = Path(_filename).stem
            t = os.path.getmtime(_filename)
            v = datetime.datetime.fromtimestamp(t)
            x = v.strftime('%Y-%m-%d %H-%M-%S')
            os.rename(_filename, f"{filename_only} {x}.log")

            # remove all but the last 2 log files
            files = sorted(Path('.').glob(f'{filename_only}*.log'), key=os.path.getmtime, reverse=True)
            if len(files) > 2:
                for file_to_delete in files[2:]:
                    os.remove(file_to_delete)
        except PermissionError:
            # This can happen if another process has the log file open.
            # In this case, we just log to the existing file.
            pass

    # Define the logging config for file logging.
    logging.basicConfig(filename=_filename, level=logging.ERROR,
                        format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
                        datefmt='%H:%M:%S')

logger = colorlog.getLogger('ed_log')

# Change this to debug if want to see debug lines in log file
logger.setLevel(logging.INFO)    # change to INFO for more... DEBUG for much more

handler = logging.StreamHandler()
handler.setLevel(logging.WARNING)  # change this to what is shown on console
handler.setFormatter(
    colorlog.ColoredFormatter('%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s', 
        log_colors={
            'DEBUG':    'fg_bold_cyan',
            'INFO':     'fg_bold_green',
            'WARNING':  'bg_bold_yellow,fg_bold_blue',
            'ERROR':    'bg_bold_red,fg_bold_white',
            'CRITICAL': 'bg_bold_red,fg_bold_yellow',
	},secondary_log_colors={}

    ))
logger.addHandler(handler)
