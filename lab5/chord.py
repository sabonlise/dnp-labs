from argparse import ArgumentParser
from bisect import bisect_left
from threading import Thread
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer

M = 5
PORT = 1234
RING = [2, 7, 11, 17, 22, 27]
RING_SPACE = 2 ** M


class Node(Thread):
    def __init__(self, node_id):
        """Initializes the node properties and constructs the finger table according to the Chord formula"""
        self.node_id = node_id
        Thread.__init__(self)
        self.data = {}
        self.successor = RING[bisect_left(RING, node_id + 1) % len(RING)]
        self.predecessor = RING[(bisect_left(RING, node_id) - 1) % len(RING)]
        self.finger_table = [None] * M

        for i in range(M):
            self.finger_table[i] = self.find_successor((2 ** i + node_id) % RING_SPACE)

        print(f"Node created! Finger table = {self.finger_table}")

    def closest_preceding_node(self, id: int):
        """Returns node_id of the closest preceding node (from n.finger_table) for a given id"""
        for finger in self.finger_table[::-1]:
            if finger and finger in range(self.node_id + 1, id % RING_SPACE):
                return finger

        return self.node_id

    def find_successor(self, id):
        """Recursive function returning the identifier of the node responsible for a given id"""
        if id == self.node_id:
            return id

        if id in range(self.node_id + 1, self.successor + 1):
            return self.successor

        return RING[bisect_left(RING, id % RING_SPACE) % len(RING)]

    def put(self, key, value):
        """Stores the given key-value pair in the node responsible for it"""
        # item = int(value.split('value_')[1]) if isinstance(value, str) else value

        peer = self.find_successor(key)

        if peer == self.node_id:
            return self.store_item(key, value)

        with ServerProxy(f'http://node_{peer}:{PORT}') as node:
            return node.put(key, value)

    def get(self, key):
        """Gets the value for a given key from the node responsible for it"""
        if self.predecessor < key <= self.node_id:
            return self.retrieve_item(key)
        elif self.node_id < key <= self.successor:
            with ServerProxy(f'http://node_{self.successor}:{PORT}') as node:
                print(f"Forwarding request (key={key}) to node {self.successor}")
                return node.get(key)
        else:
            peer = self.closest_preceding_node(key)
            if peer == self.node_id:
                item = self.retrieve_item(key)
                if item == -1:
                    pr = self.find_successor(key)
                    # print(f'Failed. Forwarding to successor {pr}')
                    with ServerProxy(f'http://node_{pr}:{PORT}') as node:
                        print(f"Forwarding request (key={key}) to node {pr}")
                        return node.get(key)
                else:
                    return item

            with ServerProxy(f'http://node_{peer}:{PORT}') as node:
                print(f"Forwarding request (key={key}) to node {peer}")
                return node.get(key)

    def store_item(self, key, value):
        """Stores a key-value pair into the data store of this node"""
        try:
            self.data[key] = value
        except Exception as E:
            print(f'Exception {E} occurred on insertion')
            return False

        return True

    def retrieve_item(self, key):
        """Retrieves a value for a given key from the data store of this node"""
        val = self.data.get(key, -1)
        return val


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('node_id', type=int)
    args = parser.parse_args()

    n = int(args.node_id)

    with SimpleXMLRPCServer(('0.0.0.0', 1234), logRequests=False) as server:
        server.register_introspection_functions()
        server.register_instance(Node(n))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down...")
