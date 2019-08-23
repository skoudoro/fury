"""
===============
Using a timer
===============

This example shows how to create a simple animation using a timer callback.

We will use a sphere actor that generates many spheres of different colors,
radii and opacity. Then we will animate this actor by rotating and changing
global opacity levels from inside a user defined callback.

The timer will call this user defined callback every 200 milliseconds. The
application will exit after the callback has been called 100 times.
"""

import os
import time
import threading
import numpy as np
from fury import window, actor, ui
import itertools

xyz = 10 * np.random.rand(100, 3)
colors = np.random.rand(100, 4)
radii = np.random.rand(100) + 0.5

scene = window.Scene()

sphere_actor = actor.sphere(centers=xyz,
                            colors=colors,
                            radii=radii)

scene.add(sphere_actor)

showm = window.ShowManager(scene,
                           size=(900, 768), reset_camera=False,
                           order_transparent=True)

showm.initialize()

icon_path = '/Users/koudoro/furyicon/icons/test_animation_icons'
basename = 'noun_process_621773 '
icon_files = [('rotate_{}'.format(n),
               os.path.join(icon_path, basename + '({}).png'.format(n)))
              for n in range(13)]

button = ui.Button2D(icon_fnames=icon_files, position=(200, 200),
                     size=(128, 128))


# use itertools to avoid global variables
counter = itertools.count()
running = False
timer_id = None
timer_id2 = None
thread = None


def thread_execution():
    cnt = next(counter)
    while cnt != 20:
        cnt = next(counter)
        print("Running ", cnt)
        time.sleep(0.2)
        button.next_icon()
        showm.render()


@window.vtk.calldata_type(window.vtk.VTK_INT)
def timer_callback(obj, event, call_data):
    global timer_id, timer_id2, thread, running, counter
    if "TimerEvent" == event:
        # if timer_id == call_data:
        if timer_id2 == call_data:
            if not thread.is_alive():
                print(" DESTROY TIMER --->>>  THREAD FINISHED")
                running = False
                counter = itertools.count()
                showm.destroy_timer(timer_id)
                showm.destroy_timer(timer_id2)


def start_stop(iren, _obj, _event):
    global running, timer_id, timer_id2, thread, counter
    if not running:
        print("start")
        timer_id = showm.add_timer_callback(True, 100, timer_callback)
        timer_id2 = showm.add_timer_callback(repeat=True,
                                             duration=1000,
                                             timer_callback=timer_callback)

        thread = threading.Thread(target=thread_execution)
        thread.start()
        running = True
    else:
        print("stop")
        showm.destroy_timer(timer_id)
        showm.destroy_timer(timer_id2)
        thread._stop()
        counter = itertools.count()
        del thread
        running = False

scene.add(button)

# Run every 200 milliseconds
button.on_left_mouse_button_clicked = start_stop

showm.start()

# window.record(showm.scene, size=(900, 768), out_path="viz_timer.png")
