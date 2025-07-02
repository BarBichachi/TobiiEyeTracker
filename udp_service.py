import json
import socket
import logging
import threading
from typing import Optional, Callable

class UDPService:
    """ A class that manages UDP communication:
    sending data and receiving it asynchronously via callback. """

    def __init__(self, config_path: str = "ServerSettings.json"):
        """ Initializes sockets and configuration from a JSON file. """
        try:
            with open(config_path, "r") as file:
                data = json.load(file)

            self.ServerIP = data.get("ServerIP")
            self.ServerPort = data.get("ServerPort")
            self.TvtClientIP = data.get("TvtClientIP")
            self.TvtClientPort = data.get("TvtClientPort")

            if not all([self.ServerIP, self.ServerPort, self.TvtClientIP, self.TvtClientPort]):
                raise ValueError("Missing configuration keys in ServerSettings.json")

            self.UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            self.UDPTvtClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            self.UDPTvtClientSocket.bind((self.TvtClientIP, self.TvtClientPort))

            self._listener_thread: Optional[threading.Thread] = None
            self._stop_thread = False
            self.data_received_event: Optional[Callable[[bytes], None]] = None

        except Exception as e:
            logging.error(f"Failed to initialize UDP service: {e}", exc_info=True)
            raise

    def send(self, data):
        """Sends data to the configured server over UDP."""
        if not self.ServerIP or not self.ServerPort:
            raise RuntimeError("Server IP and port are not configured.")
        if not isinstance(data, bytes):
            raise TypeError("Data must be of type 'bytes'.")

        try:
            self.UDPServerSocket.sendto(data, (self.ServerIP, self.ServerPort))
        except Exception as e:
            logging.error(f"Failed to send UDP data: {e}", exc_info=True)

    def start_receiving(self):
        """ Starts a background thread to listen for incoming UDP messages. """
        if self._listener_thread and self._listener_thread.is_alive():
            logging.warning("UDP listener is already running.")
            return

        self._stop_thread = False
        self._listener_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._listener_thread.start()
        logging.info("UDP listener thread started.")

    def _receive_loop(self):
        """ Internal loop that receives messages and triggers callback. """
        while not self._stop_thread:
            try:
                data, addr = self.UDPTvtClientSocket.recvfrom(1024)
                self._handle_incoming_data(data)
            except OSError:
                break  # socket was closed
            except Exception as e:
                logging.error(f"Error receiving UDP data: {e}", exc_info=True)

    def _handle_incoming_data(self, data):
        """ Invokes the registered callback with incoming data. """
        if self.data_received_event:
            try:
                self.data_received_event(data)
            except Exception as e:
                logging.error(f"Error in data_received_event callback: {e}", exc_info=True)

    def set_data_received_event(self, handler: Callable[[bytes], None]):
        """ Registers a callback that is called when data is received. """
        self.data_received_event = handler

    def close(self):
        """
        Stops the listener and closes all sockets.
        """
        self._stop_thread = True
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=1)

        try:
            self.UDPServerSocket.close()
            self.UDPTvtClientSocket.close()
            logging.info("UDP service closed successfully.")
        except Exception as e:
            logging.error(f"Error closing UDP sockets: {e}", exc_info=True)