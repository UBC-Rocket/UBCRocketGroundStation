import os
import kiss
import aprs
import aprslib
import subprocess
from threading import Thread
from typing import Optional, Callable, List, Dict, Any
from util.detail import LOGGER

DEFAULT_KISS_PORT = 8001
CALLSIGN = "KD2ZWJ-2"

# $HOST_IP:8001

class KissServer():
    def __init__(self, kiss_address: Optional[str] = None):
        # List of subscribers to KISS packets
        # A subscriber is a function that takes a dictionary of parsed APRS data
        self.subscribers: List[Callable[[Dict[str, Any]], None]] = []
        
        # Determine if we should launch a KISS server
        if kiss_address is None or kiss_address == "direwolf":
            # Start Direwolf
            self.start_kiss = True
            self.address = "localhost"
            self.port = DEFAULT_KISS_PORT
        else:
            # Use given KISS server
            self.start_kiss = False
            # TODO: Fix This!
            # Hacky way to check if address is valid
            if (":" not in kiss_address) or ("/" in kiss_address):
                raise ValueError("Invalid KISS Address")
            self.address = kiss_address.split(":")[0]
            self.port = int(kiss_address.split(":")[1])
            
            # HACK: If running on WSL, if $HOST_IP is passed, use the host ip!!
            if self.address.startswith("$"):
                self.address = os.environ[self.address[1:]]
        
        # Start Kiss Server If Necessary
        if self.start_kiss:
            LOGGER.info(f"Launching Direwolf Instance for KISS Server")
            self.direwolf = subprocess.Popen(["direwolf", "-t", "0", "-c", "direwolf.conf", "-p", str(self.port)])

        # Create Kiss Connection
        LOGGER.info(f"Connecting to KISS Server at {self.address}:{self.port}")
        self.kiss_connection = kiss.TCPKISS(self.address, self.port)
        self.kiss_connection.start()
        
        # Start Kiss Thread
        LOGGER.info(f"Starting KISS Reading Thread {self.address}:{self.port}")
        self.kiss_thread = Thread(
            target=self.kiss_connection.read, 
            kwargs={'callback': self.read_kiss_packet}, 
            daemon=True
        )
        self.kiss_thread.start()
        
    def read_kiss_packet(self, packet):
        try:
            raw = aprs.parse_frame(packet)
            parsed = aprslib.parse(str(raw))
            LOGGER.debug(f"Received New KISS Packet: {parsed}")
            for subscriber in self.subscribers:
                subscriber(parsed)
        except Exception as e:
            LOGGER.error(f"Error While Parsing APRS Packet: {e}")
            
    def add_subscriber(self, subscriber: Callable[[Dict[str, Any]], None]):
        # Subscribers are functions that take in a raw KISS packet and parses them.
        # Add subscriber to list
        self.subscribers.append(subscriber)
        
