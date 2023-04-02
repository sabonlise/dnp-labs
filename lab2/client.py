import os
import socket
import time
import multiprocessing
import threading
import shutil

from PIL import Image

SERVER_URL = '127.0.0.1:1234'
FILE_NAME = 'result.gif'
CLIENT_BUFFER = 1024
FRAME_COUNT = 5000
CHUNK_SIZE = 20

gathered_frames = set()


def download_frames(frame_id):
    # Downloading frames in chunks per thread
    for cur_frame in range(frame_id * CHUNK_SIZE, (frame_id + 1) * CHUNK_SIZE):
        download_frame(cur_frame)


def download_frame(frame_id):
    global gathered_frames

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        ip, port = SERVER_URL.split(':')

        try:
            s.connect((ip, int(port)))
        except ConnectionRefusedError:
            # Sometimes connection from server is refused and frames are missed
            return

        image = b''
        while True:
            packet = s.recv(CLIENT_BUFFER)
            if not packet:
                break
            image += packet

        with open(f'frames/{frame_id}.png', 'wb') as f:
            f.write(image)

        gathered_frames.add(frame_id)


def process_frame(frame_id):
    return Image.open(f"frames/{frame_id}.png").convert("RGBA")


def create_gif():
    usable_cores = multiprocessing.cpu_count() - 1
    t = time.time()

    # Creating pool of processes to concurrently open multiple images
    with multiprocessing.Pool(usable_cores) as pool:
        frames = list(pool.map(process_frame, range(FRAME_COUNT)))

    frames[0].save(FILE_NAME, format="GIF",
                   append_images=frames[1:], save_all=True, duration=500, loop=0)

    return time.time() - t


if __name__ == '__main__':
    if os.path.exists('frames'):
        shutil.rmtree('frames')

    if not os.path.exists('frames'):
        os.mkdir('frames')

    all_frames = set(range(FRAME_COUNT))
    threads = []

    t0 = time.time()
    # Creating multiple threads to process frames in chunks concurrently
    for frame in range(FRAME_COUNT // CHUNK_SIZE):
        thread = threading.Thread(target=download_frames, args=(frame,))
        threads.append(thread)
        thread.start()

    [thread.join() for thread in threads]
    threads.clear()

    # Handling frames that are mysteriously lost due to connection refusal from server
    # I have no clue why this is happening (server queue is of FRAME_COUNT size)
    if missing_frames := all_frames.difference(gathered_frames):
        missing_frames_iters = 0

        print(f'Time without missed frames: {time.time() - t0}')
        gathered_frames.clear()
        while missing_frames := missing_frames.difference(gathered_frames):
            print('Lost frames:', len(missing_frames))
            missing_frames_iters += 1
            for frame in missing_frames:
                thread = threading.Thread(target=download_frame, args=(frame,))
                threads.append(thread)
                thread.start()

            [thread.join() for thread in threads]

        print(missing_frames_iters)

    print(f'Frames download time: {time.time() - t0}')
    print(f'GIF creation time: {create_gif()}')
