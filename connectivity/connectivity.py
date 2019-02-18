import socket
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from collections import deque
from config import Config, Mode


logger = None
transport = None


class Client:
    def __init__(self, ip, port, sent_time):
        self.ip = ip
        self.port = port
        self.sent_time = sent_time
        self._previous_timestamp = datetime.now()
        self._current_timestamp = datetime.now()

    def update_sent_time(self, sent_time):
        self.sent_time = sent_time
        self._previous_timestamp = self._current_timestamp
        self._current_timestamp = datetime.now()

    @property
    def is_active(self):
        time_delta = datetime.now() - self._current_timestamp
        if time_delta > timedelta(seconds=Config.INACTIVE_SECS):
            return False
        else:
            return True


class ClientHandler:
    clients = []

    def add(self, new_client):
        existing_client_i = None
        for i, client in enumerate(ClientHandler.clients):
            if client.ip == new_client.ip:
                client.update_sent_time(new_client.sent_time)
                existing_client_i = i
                break
        if existing_client_i is None:
            logger.debug(f'Adding new client {new_client.ip}')
            ClientHandler.clients.append(new_client)

    def remove(self, client):
        ClientHandler.clients.remove(client)

    @property
    def count(self):
        return len(ClientHandler.clients)

client_handler = ClientHandler()

class UDPServerProtocol:
    # https://docs.python.org/3/library/asyncio-protocol.html#asyncio-protocol
    def connection_made(self, transport):
        self.transport = transport
        sock = transport.get_extra_info('socket')
        if sock is not None:
            addr = sock.getsockname()
            logger.debug(f'Server listening at {addr[0]}:{addr[1]}')

    def datagram_received(self, data, addr):
        sent_time = data.decode()
        latency = datetime.utcnow() - datetime.utcfromtimestamp(Decimal(sent_time))
        logger.info(f'Received from {addr[0]}:{addr[1]} {latency.microseconds / 1000}ms')
        client = Client(addr[0], addr[1], sent_time)
        client_handler.add(client)
        #log_beat(tuple([datetime.now(), f'{addr[0]}:{addr[1]}']))

    def connection_lost(self, exc):
        if exc is None:
            logger.debug('Server connection closed.')


class UDPClientProtocol:
    def connection_made(self, transport):
        self.transport = transport
        sock = transport.get_extra_info('socket')
        if sock is not None:
            laddr = sock.getsockname()
            raddr = sock.getpeername()
            logger.debug(f'Sending beat from {laddr[0]}:{laddr[1]} to {raddr[0]}:{raddr[1]}')
        transport.sendto(str(datetime.now().timestamp()).encode(), (Config.REMOTE_ADDR, Config.REMOTE_PORT))
        transport.close()

    def connection_lost(self, exc):
        pass


async def create_server():
    global transport
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPServerProtocol(),
        local_addr=(Config.LOCAL_ADDR, Config.LOCAL_PORT)
    )


async def beat_sender():
    global transport
    while True:
        if transport is None and Config.MODE is Mode.CLIENT:
            # Create new connection to send beat to target server.
            loop = asyncio.get_running_loop()
            client_transport, protocol = await loop.create_datagram_endpoint(
                lambda: UDPClientProtocol(),
                remote_addr=(Config.REMOTE_ADDR, Config.REMOTE_PORT)
    )
        await asyncio.sleep(Config.BEAT_SECS)


async def beat_monitor():
    global active_clients
    while True:
        if client_handler.count > 0:
            for client in client_handler.clients:
                if not client.is_active:
                    logger.info(f'Client {client.ip} is no longer active!')
                    client_handler.remove(client)
                    logger.debug(f'Active clients {client_handler.count}')
        await asyncio.sleep(1)


def setup_logging():
    global logger
    logging.basicConfig(
        format=Config.LOG_FORMAT,
        level=Config.LOG_LEVEL) # logging.DEBUG
    logger = logging.getLogger(__name__)
    if Config.SAVE_LOG:
        if not Config.LOG_FILE_PATH.parent.exists():
            Config.LOG_FILE_PATH.parent.mkdir()
            logger.info(f'Created {Config.LOG_FILE_PATH.parent}')
        fh = logging.FileHandler(Config.LOG_FILE_PATH)
        fh.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        fh.setLevel(Config.LOG_LEVEL)
        logger.addHandler(fh)
    # logger = logging.LoggerAdapter(logger, {'mode': str(Config.MODE)})


def main():
    setup_logging()
    loop = asyncio.get_event_loop()
    tasks = []
    if Config.MODE is Mode.CLIENT:
        # Just send heart beats to target
        tasks.append(loop.create_task(beat_sender()))
    elif Config.MODE is Mode.SERVER:
        # Just listen for heart beats.
        tasks.append(loop.create_task(create_server()))
        tasks.append(loop.create_task(beat_monitor()))

    all_tasks = asyncio.gather(*tasks)
    try:
        loop.run_until_complete(all_tasks)
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('Program exiting...')
        logging.shutdown()


if __name__ == '__main__':
    main()