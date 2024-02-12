import os
import traceback
import time
import sys
import threading
import subprocess
import json

from functools import partial

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from animation import load_config

import tkinter as tk

root = Tk()
selected_csv = StringVar()
progressbar = ttk.Progressbar(length=400)
root.title("Sorting animation generator")
frm = ttk.Frame(root, padding=10)
frm.grid(column=0, row=0)
current_directory = os.path.dirname(os.path.abspath(__file__))

threads = {}
layout = {
    'run_button': {
        'column': 0,
        'row': 8
    },
    'notify_message': {
        'column': 0,
        'row': 10
    },
    'button_under_notify_message': {
        'column': 0,
        'row': 11
    },
    'progressbar': {
        'column': 0,
        'row': 7
    },
    'label_over_select_button': {
        'column': 0,
        'row': 0
    },
    'select_button': {
        'column': 0,
        'row': 1,
        'pady': 10
    },
    'done_message': {
        'column': 0,
        'row': 10
    },
    'runtime_label': {
        'column': 0,
        'row': 5,
        'sticky': "w"
    },
    'runtime': {
        'column': 1,
        'row': 5,
        'sticky': "e"
    },
}

ttk.Label(frm, text="Csv file isn't selected").grid(**layout['label_over_select_button'])


def enable_run_button_remove_progress():
    progressbar.stop()
    progressbar.grid_remove()
    run_button.config(state=tk.NORMAL)


def threads_watcher():
    for id in list(threads.keys()):
        thread = threads[id]
        if not thread.is_alive():
            enable_run_button_remove_progress()
            del threads[id]

    root.after(500, threads_watcher)


def clear(slug):
    for slave in frm.grid_slaves(row=layout[slug]['row'], column=layout[slug]['column']):
        slave.destroy()


def copy_message(text_to_copy):
    root.clipboard_clear()
    root.clipboard_append(text_to_copy)
    root.update()


def notify(message):
    clear('notify_message')
    ttk.Label(frm, text=message).grid(**layout['notify_message'])
    clear('button_under_notify_message')
    ttk.Button(frm, text='Copy message above', command=partial(copy_message, message)).grid(
        **layout['button_under_notify_message']
    )


def run2(path, progressbar):
    try:
        animation_py = os.path.join(current_directory, 'animation.py')
        tmp, ext = os.path.splitext(path)
        folder = os.path.dirname(tmp)
        filename = os.path.basename(tmp)
        out_file = os.path.join(folder, filename)

        manim = subprocess.run(['which', 'manim'], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
        process = subprocess.Popen(f'{sys.executable} {manim} {animation_py} Sorting -o {out_file} {path}', shell=True)
        progress_file = os.path.join(current_directory, 'progress')
        progressbar['value'] = 0
        try:
            os.remove(progress_file)
        except FileNotFoundError:
            pass
        while True:
            if process.poll() is None:
                if os.path.exists(progress_file):
                    try:
                        with open(progress_file, 'r') as f:
                            progressbar['value'] = float(f.read())
                    except:
                        pass
            else:
                break
            time.sleep(1)
        return_code = process.wait()
        if return_code != 0:
            raise Exception(f"The folowing command returned non zero code: {process.args}")
        progressbar['value'] = 100
        clear('done_message')
        ttk.Label(frm, text=f'Done. Result is in file {out_file}.mp4').grid(**layout['done_message'])
    except Exception as e:
        notify(str(e) + '\n' + traceback.format_exc())


def run():
    file = selected_csv.get()
    if not file:
        messagebox.showinfo(
            "Error",
            "Select .csv file first"
        )
        return

    clear('done_message')
    clear('button_under_notify_message')

    progressbar.grid(**layout['progressbar'])
    run_button.config(state=tk.DISABLED)

    t = threading.Thread(
        target=run2,
        args=(file, progressbar),
        daemon=True
    )
    t.start()
    threads[t.ident] = t


def select_csv():
    file_path = filedialog.askopenfilename(title='Select csv file')
    if file_path:
        selected_csv.set(file_path)
        ttk.Label(frm, text=f"Selected file: {file_path}").grid(**layout['label_over_select_button'])


def write_config(config):
    with open(os.path.join(current_directory, 'config.json'), 'w') as f:
        f.write(json.dumps(config, indent=2))


def on_runtime_change(*args):
    config = load_config()
    if not runtime_var.get():
        return
    config['run_time'] = float(runtime_var.get())
    write_config(config)


runtime_var = tk.StringVar()
runtime_var.trace("w", on_runtime_change)
runtime = Entry(frm, width=5, textvariable=runtime_var)
runtime.grid(**layout['runtime'])
runtime.insert(0, str(load_config().get('run_time', 0.5)))

ttk.Label(frm, text="On step run time (sec)").grid(
    **layout['runtime_label']
)

ttk.Button(frm, text='Select csv file', command=select_csv).grid(**layout['select_button'])
run_button = ttk.Button(frm, text='Run', command=run)
run_button.grid(**layout['run_button'])
threads_watcher()
root.mainloop()