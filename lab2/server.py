import socket
import threading
import os
import logging
import numpy as np
import io

from PIL import Image


logging.basicConfig(level=logging.NOTSET)
PORT = 1234
FRAME_COUNT = 5000


def generate_random_image():
    arr = np.random.randint(0, 255, (10, 10, 3), dtype='uint8')
    img = Image.fromarray(arr, 'RGB')

    with io.BytesIO() as output:
        img.save(output, format='PNG')

        raw_data = output.getvalue()

        return raw_data


def handle_connection(connection, address):
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(f'{address}')
    try:
        logger.debug(f'Connected to {connection}')
        raw_image = generate_random_image()
        connection.sendall(raw_image)
    except Exception as err:
        logger.exception(f'Exception occurred: {err}')
    except KeyboardInterrupt:
        logger.info('Received interrupt, exiting...')
        exit()
    finally:
        logger.debug('Closing socket connection')
        connection.close()


class Server:
    def __init__(self, server_ip, server_port):
        self.socket = None
        self.logger = logging.getLogger('server')
        self.server_ip = server_ip
        self.server_port = server_port

    def start(self):
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.server_ip, self.server_port))
        self.socket.listen(FRAME_COUNT)
        thread_count = 0

        while True:
            connection, address = self.socket.accept()

            # Creating separate thread for each connection
            thread = threading.Thread(target=handle_connection, args=(connection, address))
            thread.daemon = True
            thread.start()
            thread_count += 1

            self.logger.debug(f"Started thread {thread}: {thread_count}")


if __name__ == '__main__':
    server = Server('', PORT)
    try:
        if not os.path.exists('frames'):
            os.mkdir('frames')

        logging.info('Listening...')
        server.start()
    except Exception as error:
        logging.exception(f'Exception occurred: {error}')
    finally:
        for t in threading.enumerate():
            if t is threading.main_thread():
                continue
            t.join()

        logging.info('Terminating...')
