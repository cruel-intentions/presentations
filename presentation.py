import sys
import cv2
import numpy as np
from functools import lru_cache
from strictyaml import load, Map, Str, Int, Seq, YAMLError, Optional 


frame_schema = Map({
    Optional('color', None): Str(),
    Optional('file', None): Str(),
    Optional('text', None): Str(),
    Optional('textColor', None): Str(),
    Optional('camera', None): Int(),
    Optional('position', None): Seq(Int()),
    Optional('size', None): Seq(Int()),
})
slide_schema = Map({'frames': Seq(frame_schema)})
presentation_schema = Map({'slides': Seq(slide_schema)})


default_position = lambda: (0, 0)
default_size = lambda: (100, 100)
default_color = lambda: '#ffffff'
SCREEN_HEIGHT = 1000
SCREEN_WIDTH = 1920
default_screen = lambda x=SCREEN_WIDTH, y=SCREEN_HEIGHT, v=0xFF: np.full((y, x, 3), v, np.uint8)

@lru_cache
def to_color(str_color):
    r = int(f'0x{str_color[1:3]}', 16)
    g = int(f'0x{str_color[3:5]}', 16)
    b = int(f'0x{str_color[5:7]}', 16)
    return r, g, b


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
        size = map(int, frame_def.get('size', default_size()))
        abs_h, abs_w = absolute(tuple(size))
        position = map(int, frame_def.get('position', default_position()))
        abs_y, abs_x = absolute(tuple(position))
        color = frame_def.get('color', None)
        text_color = frame_def.get('textColor', '#000000')
        text = frame_def.get('text', None)
        img_file_path = frame_def.get('file', None)
        camera_id = frame_def.get('camera', None)

        if color is not None:
            rgb = to_color(str(color))
            frame[abs_y:abs_y + abs_h, abs_x:abs_x + abs_w] = default_screen(abs_w, abs_h, rgb)
        elif text is not None:
            rgb = to_color(str(text_color))
            print(rgb)
            frame = cv2.putText(frame, str(text),
                        (abs_x, abs_y), #position
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1, #fontScale
                        rgb, #color
                        2, #thickness
                        cv2.LINE_AA,
                        False)
        elif img_file_path is not None:
            img = img_read(str(img_file_path))
            actual_h, actual_w, _ = frame[abs_y:abs_y + abs_h, abs_x:abs_x + abs_w].shape
            frame[abs_y:abs_y + abs_h, abs_x:abs_x + abs_w] = cv2.resize(img, (actual_w, actual_h))
        elif camera_id is not None:
            ret, camera = capture(int(camera_id)).read()
            actual_h, actual_w, _ = frame[abs_y:abs_y + abs_h, abs_x:abs_x + abs_w].shape
            frame[abs_y:abs_y + abs_h, abs_x:abs_x + abs_w] = cv2.resize(camera, (actual_w, actual_h))
    return frame


if __name__ == "__main__":
    presentation_def_raw = open(sys.argv[1]).read()
    presentation_def = load(presentation_def_raw, presentation_schema)
    position = 0
    presentation_size = len(presentation_def['slides']) -1
    frame = default_screen()
    cv2.imshow('Frame', frame)
    while True:
        slide = presentation_def['slides'][position]
        frame = to_frame(slide)
        cv2.imshow('Frame', frame)
        position, change = navegate(position)


