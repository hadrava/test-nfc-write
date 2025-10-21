import socket
import json

class NFCWriter:
    def __init__(self, socket_path):
        self._socket_path = socket_path

    def _send_to_unix_socket(self, message: dict) -> dict:
        """Send JSON message to the async UNIX socket server and get response."""
        try:
            # Connect to the existing UNIX socket
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.connect(self._socket_path)
                # Send JSON + newline (server expects line-delimited JSON)
                client.sendall((json.dumps(message) + "\n").encode())

                # Receive response (up to 4 KB)
                data = client.recv(4096)
                if not data:
                    return {"error": "No response from nfc_main.py"}

                return json.loads(data.decode().strip())

        except FileNotFoundError:
            return {"error": "socket to NFC writer not found"}
        except ConnectionRefusedError:
            return {"error": "socket connection refused"}
        except json.JSONDecodeError:
            return {"error": "invalid JSON in server response"}
        except Exception as e:
            return {"error": str(e)}

    def write_tag(self, tag_uid, tag_content):
        write_cmd = {
                "command": "write_tag",
                "tag_uid": tag_uid,
                "content": tag_content.hex(),
                }
        response = self._send_to_unix_socket(write_cmd)
        return response
