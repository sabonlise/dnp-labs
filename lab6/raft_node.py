import random
import sched
import socket
import time
from threading import Thread
from argparse import ArgumentParser
from enum import Enum
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer

PORT = 1234
CLUSTER = [1, 2, 3]
ELECTION_TIMEOUT = (6, 8)
HEARTBEAT_INTERVAL = 5


class NodeState(Enum):
    """Enumerates the three possible node states (follower, candidate, or leader)"""
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3


class Node:
    def __init__(self, node_id):
        """Non-blocking procedure to initialize all node parameters and start the first election timer"""
        self.node_id = node_id
        self.state = NodeState.FOLLOWER
        self.term = 0
        self.votes = {}
        self.log = []
        self.pending_entry = ''
        self.current_task = None
        self.scheduler = sched.scheduler()

        self.reset_election_timer()
        print(f"Node started! State: {self.state}. Term: {self.term}")

    def is_leader(self):
        """Returns True if this node is the elected cluster leader and False otherwise"""
        return self.state == NodeState.LEADER

    def reset_election_timer(self):
        """Resets election timer for this (follower or candidate) node and returns it to the follower state"""
        try:
            if self.scheduler and self.current_task:
                self.scheduler.cancel(self.current_task)
        except ValueError:
            pass

        self.state = NodeState.FOLLOWER
        r = random.uniform(*ELECTION_TIMEOUT)
        # print(f'Starting timer with {r} seconds for node {self.node_id}')
        self.current_task = self.scheduler.enter(r, 1, self.hold_election)
        t = Thread(target=self.scheduler.run)
        t.start()
        return

    def hold_election(self):
        """Called when this follower node is done waiting for a message from a leader (election timeout)
            The node increments term number, becomes a candidate and votes for itself.
            Then call request_vote over RPC for all other online nodes and collects their votes.
            If the node gets the majority of votes, it becomes a leader and starts the hearbeat timer
            If the node loses the election, it returns to the follower state and resets election timer.
        """
        self.term += 1
        self.state = NodeState.CANDIDATE
        print(f"New election term {self.term}. State: Candidate")
        current_votes = 1

        for node_id in CLUSTER:
            try:
                if node_id == self.node_id:
                    continue

                print(f'Requesting vote from node {node_id}')
                with ServerProxy(f'http://node_{node_id}:{PORT}') as node:
                    if node.request_vote(self.term, self.node_id):
                        current_votes += 1
            except Exception:
                print(f'Follower node {node_id} is offline')

        print(f'Received {current_votes} votes. State: ', end='')
        if current_votes > len(CLUSTER) // 2:
            self.state = NodeState.LEADER
            print('Leader')
        else:
            self.reset_election_timer()
            print('Candidate')

        while self.is_leader():
            self.append_entries()
            time.sleep(HEARTBEAT_INTERVAL)

        return

    def request_vote(self, term, candidate_id):
        """Called remotely when a node requests voting from other nodes.
            Updates the term number if the received one is greater than `self.term`
            A node rejects the vote request if it's a leader or it already voted in this term.
            Returns True and update `self.votes` if the vote is granted to the requester candidate and False otherwise.
        """
        print(f"Got a vote request from {candidate_id} (term={term})")
        if self.is_leader():
            print(f'Didn\'t vote for {candidate_id} (I\'m a leader)')
            return False

        if term > self.term:
            self.term = term

        if self.term in self.votes and self.node_id in self.votes[self.term]:
            print(f'Didn\'t vote for {candidate_id} (already voted for {self.votes[self.term][self.node_id]})')
            return False
        else:
            try:
                self.votes[self.term][self.node_id] = candidate_id
            except KeyError:
                self.votes[self.term] = {self.node_id: candidate_id}
            self.reset_election_timer()
            print(f'Voted for {candidate_id}. Term: {self.term}')

        return True

    def append_entries(self):
        """Called by leader every HEARTBEAT_INTERVAL, sends a heartbeat message over RPC to all online followers.
            Accumulates ACKs from followers for a pending log entry (if any)
            If the majority of followers ACKed the entry, the entry is committed to the log and is no longer pending
        """
        print('Sending a heartbeat to followers')
        acknowledgments = 1
        for node_id in CLUSTER:
            try:
                if node_id == self.node_id:
                    continue

                with ServerProxy(f'http://node_{node_id}:{PORT}') as node:
                    if node.heartbeat(self.pending_entry):
                        acknowledgments += 1
            except Exception:
                print(f'Node {node_id} is offline')

        if self.pending_entry and acknowledgments > len(CLUSTER) // 2:
            self.log.append(self.pending_entry)
            print(f'Leader committed \'{self.pending_entry}\'')
            self.pending_entry = ''

        return

    def heartbeat(self, leader_entry):
        """Called remotely from the leader to inform followers that it's alive and supply any pending log entry
            Followers would commit an entry if it was pending before, but is no longer now.
            Returns True to ACK the heartbeat and False on any problems.
        """
        print(f"Heartbeat received from leader (entry='{leader_entry}')")
        try:
            self.reset_election_timer()
            if leader_entry:
                self.pending_entry = leader_entry

            if self.pending_entry and not leader_entry:
                self.log.append(self.pending_entry)
                print(f'Follower committed \'{self.pending_entry}\'')
                self.pending_entry = ''

            return True
        except Exception as E:
            print('Error on heartbeat', E)
            return False

    def leader_receive_log(self, log):
        """Called remotely from the client. Executed only by the leader upon receiving a new log entry
            Returns True after the entry is committed to the leader log and False on any problems
        """
        print(f"Leader received log '{log}' from client")
        try:
            self.pending_entry = log
            self.append_entries()
            return True
        except Exception as E:
            print('Error on receiving logs', E)
            return False


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('node_id', type=int)
    args = parser.parse_args()

    n = int(args.node_id)
    with SimpleXMLRPCServer(('0.0.0.0', 1234), logRequests=False) as server:
        server.register_introspection_functions()
        server.register_instance(Node(n))
        try:
            # print("RPC server is listening at http://0.0.0.0:1234")
            server.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down...")
