import csv
import math
import random
import os
import json

from manim import *


def read_steps():
    data = []
    with open(sys.argv[-1]) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            data.append([eval(v) for v in row])
    return data


def get_transitions(prev, curr):
    new_idxs = {}
    for idx, (p, c) in enumerate(zip(prev, curr)):
        if p != c:
            new_idxs.setdefault(c, []).append(idx)

    transitions = []
    for idx, (p, c) in enumerate(zip(prev, curr)):
        if p != c:
            idxs = []
            for idx2 in new_idxs[p]:
                delta = abs(idx - idx2)
                idxs.append((delta, idx2))
            new_idx = sorted(idxs, key=lambda i: i[0])[0][1]
            new_idxs[p].remove(new_idx)
            transitions.append((idx, new_idx))
    return transitions


def to_right(obj, radius, arc_center_x):
    return Arc(
        start_angle=math.radians(180),
        angle=-math.radians(180),
        radius=radius,
        arc_center=[arc_center_x, obj.get_center()[1], 0]
    )


def to_left(obj, radius, arc_center_x):
    return Arc(
        start_angle=math.radians(0),
        angle=math.radians(180),
        radius=radius,
        arc_center=[arc_center_x, obj.get_center()[1], 0]
    )


def anim_transitions(src, dst, radius, arc_center_x):
    if src.get_center()[0] < dst.get_center()[0]:
        return [
            MoveAlongPath(src, to_right(src, radius, arc_center_x)),
            MoveAlongPath(dst, to_left(dst, radius, arc_center_x))
        ]
    else:
        return [
            MoveAlongPath(dst, to_right(dst, radius, arc_center_x)),
            MoveAlongPath(src, to_left(src, radius, arc_center_x))
        ]


def test_data(width):
    arr = [(random.choice(['S', 'B']), v) for v in range(1, width + 1)]
    random.shuffle(arr)
    n = len(arr)
    steps = [arr.copy()]
    for i in range(n-1):
        for j in range(0, n-i-1):
            if arr[j][1] > arr[j+1][1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
                steps.append(arr.copy())
    return steps


def align(row2):
    g_row = Group(*row2)
    g_row.arrange(RIGHT, buff=0)

    max_width = config.frame_width - 0.2
    if g_row.width > max_width:
        g_row.scale(max_width / g_row.width)

    for robot in row2:
        x, y, _ = robot.get_center()
        robot.move_to([x, 0, 0], aligned_edge=DOWN)
    return g_row


def draw_lines(self, row2, lines):
    prev_color = str(row2[0].path)
    slice = [row2[0]]
    slices = []
    for robot in row2[1:]:
        curr_color = str(robot.path)
        if prev_color != curr_color:
            slices.append(slice)
            slice = [robot]
        else:
            slice.append(robot)
        prev_color = curr_color
    slices.append(slice)

    for line in lines:
        self.remove(line)

    lines = []
    for slice in slices:
        if 'green' not in str(slice[0].path):
            continue

        if len(slice) < 3:
            continue

        x_left, y, _ = slice[0].get_corner(DL)
        x_right, _, _ = slice[-1].get_corner(DR)
        y -= 0.05
        line = Line(
            [x_left, y, 0],
            [x_right, y, 0],
            color=YELLOW,
            stroke_width=2
        )
        self.add(line)
        lines.append(line)
    return lines


current_directory = os.path.dirname(os.path.abspath(__file__))


def load_config():
    try:
        with open(os.path.join(current_directory, 'config.json'), 'r') as f:
            return json.loads(f.read())
    except:
        return {}


class Sorting(MovingCameraScene):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera.background_color = WHITE

    def construct(self):
        steps = read_steps()
        #steps = test_data(10)[:5]
        config = load_config()
        # plane = NumberPlane()
        # self.add(plane)


        row = []
        nums_only = [num for letter, num in steps[0]]
        min_x, max_x = min(nums_only), max(nums_only)
        min_y, max_y = 1, 3

        for letter, x in steps[0]:
            robot = ImageMobject('robot_grey.png' if letter == 'S' else 'robot_green.png')
            y = min_y + (((x - min_x) * (max_y - min_y)) / (max_x - min_x))
            robot.scale(y)
            row.append(robot)

        row = align(row)
        self.add(row)
        prev = steps[0]
        row2 = [v for v in row]

        lines = draw_lines(self, row2, [])
        total = len(steps[1:])
        current_directory = os.path.dirname(os.path.abspath(__file__))
        for idx2, curr in enumerate(steps[1:]):
            transitions = get_transitions(prev, curr)
            anims = []
            for src_idx, dst_idx in transitions:
                src = row2[src_idx]
                dst = row2[dst_idx]
                s = src.get_center()[0]
                d = dst.get_center()[0]
                radius = (max([s, d]) - min([s, d])) / 2
                arc_center_x = min([s, d]) + radius
                anims += anim_transitions(src, dst, radius, arc_center_x)

            for idx in range(len(transitions)):
                if idx % 2 == 0:
                    src_idx, dst_idx = transitions[idx]
                    tmp = row2[dst_idx]
                    row2[dst_idx] = row2[src_idx]
                    row2[src_idx] = tmp

            self.play(*anims, run_time=config.get('run_time', 0.5))
            align(row2)
            progress = str((idx2 / total) * 100)
            with open(os.path.join(current_directory, 'progress'), 'w') as file:
                file.write(progress)

            lines = draw_lines(self, row2, lines)
            prev = curr
        self.wait(2)
