import sys
import toml
import cv2
import numpy as np
from functools import lru_cache

default_position = lambda: (0, 0)
default_size = lambda: (100, 100)
default_color = lambda: '#ffffff'
SCREEN_HEIGHT = 1000
SCREEN_WIDTH = 1920
default_screen = lambda x=SCREEN_WIDTH, y=SCREEN_HEIGHT: np.full((y, x, 3), 0xFF, np.uint8)


def navegate(old_position):
    position = old_position
    key = cv2.waitKey(25) & 0xFF
    if key == ord('d'):
        position = position + 1
    elif key == ord('a'):
        position = position - 1
    elif key == ord('q'):
        exit()

    if position > presentation_size:
        position = 0
    elif position < 0:
         position = presentation_size
    return position, position != old_position


@lru_cache
def img_read(img_file_path):
    path = sys.argv[1].split('/')
    path[-1] = img_file_path
    return cv2.imread('/'.join(path))


@lru_cache
def capture(camera_id):
    return cv2.VideoCapture(camera_id)


@lru_cache
def absolute(relative):
    (x, y) = relative
    if x < 0:
        x = 100 + x
    if y < 0:
        y = 100 + y
    if x > 100:
        x = 0
    if y > 100:
        y = 0
    return (
        int(SCREEN_HEIGHT/100 * y),
        int(SCREEN_WIDTH/100 * x),
    )


def to_frame(slide):
    frame = default_screen()
    frames = slide.get('frames', [])
    for frame_def in frames:
        size = frame_def.get('size', default_size())
        abs_h, abs_w = absolute(tuple(size))
        position = frame_def.get('position', default_position())
        abs_y, abs_x = absolute(tuple(position))
        color = frame_def.get('color', None)
        textColor = frame_def.get('textColor', None)
        text = frame_def.get('text', None)
        img_file_path = frame_def.get('file', None)
        camera_id = frame_def.get('camera', None)

        if color:
            pass
        elif text:
            frame = cv2.putText(
                    frame,
                    text,
                    (abs_x, abs_y), #position
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1, #fontScale
                    (0, 0, 0), #color
                    2, #thickness
                    cv2.LINE_AA,
                    False)
        elif img_file_path:
            img = img_read(img_file_path)
            actual_h, actual_w, _ = frame[abs_y:abs_y + abs_h, abs_x:abs_x + abs_w].shape
            frame[abs_y:abs_y + abs_h, abs_x:abs_x + abs_w] = cv2.resize(img, (actual_w, actual_h))
        elif camera_id is not None:
            ret, camera = capture(camera_id).read()
            actual_h, actual_w, _ = frame[abs_y:abs_y + abs_h, abs_x:abs_x + abs_w].shape
            frame[abs_y:abs_y + abs_h, abs_x:abs_x + abs_w] = cv2.resize(camera, (actual_w, actual_h))
    return frame


if __name__ == "__main__":
    presentation_def = toml.load(sys.argv[1])
    position = 0
    presentation_size = len(presentation_def['slides']) -1
    change = True
    frame = default_screen()
    cv2.imshow('Frame', frame)
    while True:
        slide = presentation_def['slides'][position]
        frame = to_frame(slide)
        cv2.imshow('Frame', frame)
        position, change = navegate(position)


