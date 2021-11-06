# -*- coding: utf-8 -*-
#  piTFT touchscreen handling using evdev

# Heavily altered version of script provided by git@github.com:pigamedrv/pitft_touchscreen.git

# I'm not interested in a queue of events - just that an event happens

import os
import evdev
import threading

# Class for handling events from piTFT
class pitft_touchscreen(threading.Thread):
    def __init__(self, device_path=os.getenv("PIGAME_TS") or "/dev/input/touchscreen", grab=False):
        super(pitft_touchscreen, self).__init__()
        self.device_path = device_path
        self.grab = grab
        self.have_event = False
        self.shutdown = threading.Event()

    def run(self):
        thread_process = threading.Thread(target=self.process_device)
        # run thread as a daemon so it gets cleaned up on exit.
        thread_process.daemon = True
        thread_process.start()
        self.shutdown.wait()

    # thread function
    def process_device(self):
        device = None
        # if the path to device is not found, InputDevice raises an OSError
        # exception.  This will handle it and close thread.
        try:
            device = evdev.InputDevice(self.device_path)
            if self.grab:
                device.grab()
        except Exception as ex:
            message = "Unable to load device {0} due to a {1} exception with" \
                      " message: {2}.".format(self.device_path,
                                              type(ex).__name__, str(ex))
            raise Exception(message)
        finally:
            if device is None:
                self.shutdown.set()
        # Loop for getting evdev events
        event = {'time': None, 'id': None, 'x': None, 'y': None, 'touch': None}
        dropping = False
        while not self.shutdown.is_set():
            for input_event in device.read_loop():
                if input_event.type == evdev.ecodes.EV_ABS:
                    pass
                elif input_event.type == evdev.ecodes.EV_KEY:
                    pass
                elif input_event.type == evdev.ecodes.SYN_REPORT:
                    if not dropping:
                        self.have_event = True
                elif input_event.type == evdev.ecodes.SYN_DROPPED:
                    dropping = True
        if self.grab:
            device.ungrab()

    def has_event(self):
        return self.have_event

    def clear_event(self):
        self.have_event = False

    def stop(self):
        self.shutdown.set()

    def __del__(self):
        self.shutdown.set()
