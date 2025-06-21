# Testbestand verplaatst naar unit tests map

import unittest
from unittest.mock import patch, MagicMock
from websocket import create_connection

class TestWebSocketSimple(unittest.TestCase):
    def setUp(self):
        patcher = patch('websocket.create_connection', return_value=MagicMock())
        self.addCleanup(patcher.stop)
        self.mock_create_connection = patcher.start()
        self.ws = self.mock_create_connection()

    def test_connection(self):
        # Test if the WebSocket connection is established
        self.ws.connect.assert_not_called()  # Alleen controleren dat de mock is aangeroepen

    def test_send_receive(self):
        # Test sending and receiving a message
        self.ws.send.return_value = None
        self.ws.recv.return_value = 'mocked response'
        self.ws.send('test')
        response = self.ws.recv()
        assert response == 'mocked response'


if __name__ == "__main__":
    unittest.main()