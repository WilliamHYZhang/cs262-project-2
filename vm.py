import asyncio
import websockets
import json
import random
import time
import argparse

class VirtualMachine:
    def __init__(self, vm_id, port, peers, trial, duration):
        self.vm_id = vm_id
        self.port = port
        self.peers = peers  # dict mapping peer id to websocket URL
        self.clock_rate = random.randint(1, 20)  # ticks per (real world) second
        self.logical_clock = 0
        self.msg_queue = asyncio.Queue()
        self.connections = {}  # mapping: peer id -> websocket connection
        self.log_filename = f"vm_{vm_id}_trial{trial}.log"
        self.log_file = open(self.log_filename, "a")
        self.duration = duration
        print(f"VM {self.vm_id}: Clock rate = {self.clock_rate} ticks/sec. Log file: {self.log_filename}")

    def log_event(self, event_type, details):
        timestamp = time.time()
        log_line = f"{timestamp:.3f} - {event_type} - Logical Clock: {self.logical_clock} - {details}\n"
        self.log_file.write(log_line)
        self.log_file.flush()
        print(f"VM {self.vm_id}: {log_line.strip()}")

    async def server_handler(self, websocket, path):
        async for message in websocket:
            try:
                data = json.loads(message)
                await self.msg_queue.put(data)
            except Exception as e:
                print(f"VM {self.vm_id}: Error processing message: {e}")

    async def start_server(self):
        server = await websockets.serve(self.server_handler, "localhost", self.port)
        print(f"VM {self.vm_id}: WebSocket server started on port {self.port}")
        return server

    async def connect_to_peer(self, peer_id, peer_url):
        while True:
            try:
                ws = await websockets.connect(peer_url)
                self.connections[peer_id] = ws
                print(f"VM {self.vm_id}: Connected to peer {peer_id} at {peer_url}")
                break
            except Exception as e:
                print(f"VM {self.vm_id}: Could not connect to peer {peer_id} at {peer_url}. Retrying in 2 seconds...")
                await asyncio.sleep(2)

    async def connect_to_peers(self):
        tasks = []
        for peer_id, peer_url in self.peers.items():
            tasks.append(asyncio.create_task(self.connect_to_peer(peer_id, peer_url)))
        await asyncio.gather(*tasks)

    async def send_message(self, peer_id, message_data):
        if peer_id in self.connections:
            try:
                ws = self.connections[peer_id]
                await ws.send(json.dumps(message_data))
            except Exception as e:
                print(f"VM {self.vm_id}: Error sending message to peer {peer_id}: {e}")
        else:
            print(f"VM {self.vm_id}: No connection to peer {peer_id}")

    async def simulation_loop(self):
        start_time = time.time()
        tick_interval = 1 / self.clock_rate
        while time.time() - start_time < self.duration:
            loop_tick_start = time.time()
            if not self.msg_queue.empty():
                msg = await self.msg_queue.get()
                received_clock = msg.get("clock", 0)
                self.logical_clock = max(self.logical_clock, received_clock) + 1
                queue_length = self.msg_queue.qsize()
                self.log_event("RECEIVE", f"Received from VM {msg.get('sender')}. Queue length: {queue_length}")
            else:
                rand_val = random.randint(1, 20)
                if rand_val in (1, 2, 3):
                    targets = []
                    if rand_val == 1:
                        targets = [list(self.peers.keys())[0]]
                    elif rand_val == 2:
                        peer_keys = list(self.peers.keys())
                        targets = [peer_keys[1]] if len(peer_keys) > 1 else [peer_keys[0]]
                    elif rand_val == 3:
                        targets = list(self.peers.keys())
                    for target in targets:
                        self.logical_clock += 1
                        message_data = {
                            "sender": self.vm_id,
                            "clock": self.logical_clock,
                            "type": "SEND"
                        }
                        await self.send_message(target, message_data)
                        self.log_event("SEND", f"Sent to VM {target}")
                else:
                    self.logical_clock += 1
                    self.log_event("INTERNAL", "Internal event occurred")

            elapsed = time.time() - loop_tick_start
            await asyncio.sleep(max(0, tick_interval - elapsed))

    async def run(self):
        server = await self.start_server()
        # Allow some time for all servers to start.
        await asyncio.sleep(2)
        await self.connect_to_peers()
        await self.simulation_loop()
        # Gracefully close connections and the server.
        self.log_file.close()
        server.close()
        await server.wait_closed()
        # Also, close all peer connections.
        for ws in self.connections.values():
            await ws.close()

async def main(vm_id, trial, duration):
    ports = {1: 8001, 2: 8002, 3: 8003}
    all_peers = {1: f"ws://localhost:{ports[1]}",
                 2: f"ws://localhost:{ports[2]}",
                 3: f"ws://localhost:{ports[3]}"}
    peers = {peer_id: url for peer_id, url in all_peers.items() if peer_id != vm_id}
    port = ports[vm_id]
    vm = VirtualMachine(vm_id, port, peers, trial, duration)
    await vm.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Distributed Virtual Machine Simulation")
    parser.add_argument("--id", type=int, required=True, help="ID of the virtual machine (1, 2, or 3)")
    parser.add_argument("--trial", type=int, default=1, help="Trial number for log file differentiation")
    parser.add_argument("--duration", type=int, default=60, help="Duration (in seconds) to run the simulation")
    args = parser.parse_args()
    asyncio.run(main(args.id, args.trial, args.duration))
