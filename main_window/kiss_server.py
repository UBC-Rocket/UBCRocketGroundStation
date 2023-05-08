import os
import kiss
import aprs
import aprslib
import subprocess
from threading import Thread
from typing import Optional, Callable, List, Dict, Any, Union
from util.detail import LOGGER

DEFAULT_KISS_PORT = 8001

# $HOST_IP:8001

class KissServer():
    def __init__(self, kiss_address: Optional[str] = None):
        # List of subscribers to KISS packets
        # A subscriber is a function that takes a dictionary of parsed APRS data
        self.subscribers: List[Callable[[Dict[str, Any]], None]] = []
        
        # Clean up the kiss address
        kiss_address = kiss_address.strip() if kiss_address else kiss_address  # KEEP THIS HERE! kiss_address is sometimes None!
        
        # Determine if we should launch a KISS server
        if kiss_address in ("noaprs", "nodirewolf", "nostart", "none", "null", "na", "ns", "nd"):
            # Do not start direwolf
            self.address = None
            self.port = None
            return            
        elif kiss_address is None or kiss_address == "direwolf" or kiss_address == "":
            # Start Direwolf
            self.address = "localhost"
            self.port = DEFAULT_KISS_PORT
            
            # TODO: Start Direwolf
            LOGGER.info(f"Launching Direwolf Instance for KISS Server")
            self.direwolf = subprocess.Popen(["direwolf", "-t", "0", "-c", "direwolf.conf", "-p", str(self.port)])
        else:
            # TODO: Fix This!
            # Hacky way to check if address is valid
            if (":" not in kiss_address) or ("/" in kiss_address):
                raise ValueError("Invalid KISS Address")
            self.address = kiss_address.split(":")[0]
            self.port = int(kiss_address.split(":")[1])
            
            # HACK: If running on WSL, if $HOST_IP is passed, use the host ip!!
            if self.address.startswith("$"):
                self.address = os.environ[self.address[1:]]

        # Create Kiss Connection
        LOGGER.info(f"Connecting to KISS Server at {self.address}:{self.port}")
        self.kiss_connection = kiss.TCPKISS(self.address, self.port)
        self.kiss_connection.start()
        
    def start(self):
        # If we are not running a KISS server, do nothing
        if self.address is None:
            return
        
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
            # Try to parse the packet
            raw = aprs.parse_frame(packet)
            parsed = aprslib.parse(str(raw))
            
            # Do some additional parsing to make rest of program easier to work with
            if '-' in parsed.get('from', ''):
                parsed['from'], parsed['ssid'] = parsed['from'].split('-')
            
            LOGGER.debug(f"Received New KISS Packet: {parsed}")
            for subscriber in self.subscribers:
                subscriber(parsed)
        except Exception as e:
            LOGGER.error(f"Error While Parsing APRS Packet: {e}")
            
    def add_subscriber(self, subscriber: Callable[[Dict[str, Any]], None]):
        # Subscribers are functions that take in a raw KISS packet and parses them.
        # Add subscriber to list
        self.subscribers.append(subscriber)
