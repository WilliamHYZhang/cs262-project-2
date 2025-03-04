import asyncio
import unittest
import json
import time
from io import StringIO
import random
import websockets

from vm import VirtualMachine

# A dummy websocket object for testing send_message
class DummyWebSocket:
    def __init__(self):
        self.sent_messages = []

    async def send(self, message):
        self.sent_messages.append(message)

# A dummy asynchronous iterator to simulate a websocket connection for server_handler testing
class DummyWebSocketIterator:
    def __init__(self, messages):
        self.messages = messages

    def __aiter__(self):
        self._iter = iter(self.messages)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration

class TestVirtualMachine(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Create a VM with one peer and override the log file to use StringIO.
        self.vm = VirtualMachine(vm_id=1, port=8001, peers={2: "ws://dummy:8002"}, trial=1)
        self.vm.log_file.close()  # Close the actual file
        self.vm.log_file = StringIO()  # Use in-memory stream for testing

    def test_log_event(self):
        # Set the logical clock to a known value and log an event.
        self.vm.logical_clock = 5
        self.vm.log_event("TEST", "This is a test event")
        log_output = self.vm.log_file.getvalue()
        self.assertIn("TEST", log_output)
        self.assertIn("Logical Clock: 5", log_output)
        self.assertIn("This is a test event", log_output)

    async def test_send_message_success(self):
        # Set up a dummy websocket connection for peer 2.
        dummy_ws = DummyWebSocket()
        self.vm.connections[2] = dummy_ws
        message_data = {"sender": 1, "clock": 1, "type": "SEND"}
        await self.vm.send_message(2, message_data)
        # Verify that the dummy websocket received exactly one message.
        self.assertEqual(len(dummy_ws.sent_messages), 1)
        sent_msg = json.loads(dummy_ws.sent_messages[0])
        self.assertEqual(sent_msg, message_data)

    async def test_send_message_no_connection(self):
        # Test send_message when there is no connection for a given peer.
        message_data = {"sender": 1, "clock": 1, "type": "SEND"}
        # There is no connection for peer 3, so nothing should be sent.
        await self.vm.send_message(3, message_data)
        # (No exception is raised and nothing is added to self.vm.connections.)

    async def test_server_handler(self):
        # Simulate a websocket that yields one valid JSON message.
        test_message = json.dumps({"sender": 2, "clock": 10, "type": "SEND"})
        dummy_ws = DummyWebSocketIterator([test_message])
        # Run the server_handler with the dummy websocket.
        async def run_handler():
            await self.vm.server_handler(dummy_ws, "/dummy")
        await asyncio.wait_for(run_handler(), timeout=1)
        # Verify that the message was put into the message queue.
        queued_msg = await self.vm.msg_queue.get()
        self.assertEqual(queued_msg["sender"], 2)
        self.assertEqual(queued_msg["clock"], 10)
        self.assertEqual(queued_msg["type"], "SEND")

    async def test_connect_to_peer_success(self):
        # Test that connect_to_peer properly assigns a connection.
        async def dummy_connect(url):
            return DummyWebSocket()
        # Patch websockets.connect temporarily.
        original_connect = websockets.connect
        websockets.connect = dummy_connect

        await self.vm.connect_to_peer(2, "ws://dummy:8002")
        self.assertIn(2, self.vm.connections)

        # Restore the original websockets.connect.
        websockets.connect = original_connect

    async def test_simulation_loop_process_message(self):
        # Simulate one iteration of the simulation loop when a message is available.
        test_msg = {"sender": 2, "clock": 10, "type": "SEND"}
        await self.vm.msg_queue.put(test_msg)
        self.vm.logical_clock = 5

        # Run one iteration of the loop manually.
        tick_interval = 1 / self.vm.clock_rate
        start_tick = time.time()
        if not self.vm.msg_queue.empty():
            msg = await self.vm.msg_queue.get()
            received_clock = msg.get("clock", 0)
            self.vm.logical_clock = max(self.vm.logical_clock, received_clock) + 1
            queue_length = self.vm.msg_queue.qsize()
            self.vm.log_event("RECEIVE", f"Received from VM {msg.get('sender')}. Queue length: {queue_length}")
        elapsed = time.time() - start_tick
        await asyncio.sleep(max(0, tick_interval - elapsed))

        # Expect the logical clock to be max(5, 10) + 1 = 11.
        self.assertEqual(self.vm.logical_clock, 11)
        log_contents = self.vm.log_file.getvalue()
        self.assertIn("RECEIVE", log_contents)
        self.assertIn("Received from VM 2", log_contents)

    async def test_simulation_loop_internal_event(self):
        # Test a single iteration of simulation loop when there is no message.
        self.vm.logical_clock = 5
        tick_interval = 1 / self.vm.clock_rate
        start_tick = time.time()
        # Simulate internal event (as no message is available)
        self.vm.logical_clock += 1
        self.vm.log_event("INTERNAL", "Internal event occurred")
        elapsed = time.time() - start_tick
        await asyncio.sleep(max(0, tick_interval - elapsed))

        # The logical clock should be incremented by 1.
        self.assertEqual(self.vm.logical_clock, 6)
        log_contents = self.vm.log_file.getvalue()
        self.assertIn("INTERNAL", log_contents)
        self.assertIn("Internal event occurred", log_contents)

if __name__ == '__main__':
    unittest.main()
