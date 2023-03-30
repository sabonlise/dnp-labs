import socket
import argparse
import os
import math

RECV_BUF_SIZE = 20480

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=str)
    args = parser.parse_args()

    port = int(args.port)

    chunks = received_chunk = file = message_type = ack = None

    with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as s:
        local_addr = ('0.0.0.0', port)
        s.bind(local_addr)
        print(f'{local_addr}: Listening...')

        while True:
            try:
                data, addr = s.recvfrom(RECV_BUF_SIZE)
            except KeyboardInterrupt:
                print('Server: Exiting...')
                exit()
            except ConnectionResetError:
                print('Client sends delayed chunk after closing connection. Denying...')
                continue

            # Splitting received data
            fields = data.split(b'|')
            # Handling retransmitted starting message
            if message_type is not None and ack is not None and fields[0].decode() == message_type == 's':
                s.sendto(f'{ack}'.encode(), addr)
                continue

            message_type, sequence_number = fields[0].decode(), int(fields[1].decode())
            ack = f'a|{str((sequence_number + 1) % 2)}'

            if message_type == 's':
                file_name, file_size = fields[2].decode(), int(fields[3].decode())

                print(f'{addr}: Received the starting message')
                print(f'Preparing to receive {file_name} with size of {file_size} bytes')
                # Calculating the amount of chunks that we will receive from client
                chunks = math.ceil(file_size / RECV_BUF_SIZE)

                s.sendto(ack.encode(), addr)

                # Checking if the file already exists
                if os.path.exists(file_name):
                    print(f'File {file_name} already exists. Data will be overwritten\n')
                    os.remove(file_name)

                file = open(file_name, 'ab')
            elif message_type == 'd':
                # Handling retransmitted chunk (not writing same chunk to file)
                if received_chunk is not None and received_chunk == b'|'.join(fields[2:]):
                    s.sendto(ack.encode(), addr)
                    continue
                received_chunk = b'|'.join(fields[2:])
                chunks -= 1
                print(f'{addr}: Received the chunk with size {len(received_chunk)}. Chunks left: {chunks}')
                s.sendto(ack.encode(), addr)

                file.write(received_chunk)

            # Closing the file after receiving all chunks
            if chunks == 0 and file is not None:
                print('Successfully received entire file\n')
                file.close()
