import socket
import asyncio
import logging
from datetime import datetime
from collections import deque
from config import Config, Mode


logger = None
transport = None
active_clients = deque([])


def log_beat(client):
    global active_clients
    active_clients.append(client)


class UDPServer:
    # https://docs.python.org/3/library/asyncio-protocol.html#asyncio-protocol
    def connection_made(self, transport):
        self.transport = transport
        sock = transport.get_extra_info('socket')
        if sock is not None:
            addr = sock.getsockname()
            logger.debug(f'Server listening at {addr[0]}:{addr[1]}')

    def datagram_received(self, data, addr):
        msg = data.decode()
        logger.info(f'Received from {addr[0]}:{addr[1]} {msg}')
        log_beat(tuple([datetime.now(), f'{addr[0]}:{addr[1]}']))

    def connection_lost(self, exc):
        if exc is None:
            logger.debug('Server connection closed.')


class UDPClient:

    def connection_made(self, transport):
        self.transport = transport
        sock = transport.get_extra_info('socket')
        if sock is not None:
            laddr = sock.getsockname()
            raddr = sock.getpeername()
            logger.debug(f'Sending beat from {laddr[0]}:{laddr[1]} to {raddr[0]}:{raddr[1]}')
        transport.sendto('beat'.encode(), (Config.REMOTE_ADDR, Config.REMOTE_PORT))
        transport.close()

    def connection_lost(self, exc):
        pass


async def create_server():
    global transport
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPServer(),
        local_addr=(Config.LOCAL_ADDR, Config.LOCAL_PORT)
    )


async def beat_sender():
    global transport
    while True:
        if transport is None and Config.MODE is Mode.CLIENT:
            # Create new connection to send beat to target server.
            loop = asyncio.get_running_loop()
            client_transport, protocol = await loop.create_datagram_endpoint(
                lambda: UDPClient(),
                remote_addr=(Config.REMOTE_ADDR, Config.REMOTE_PORT)
    )
        await asyncio.sleep(Config.BEAT_SECS)


async def beat_monitor():
    global active_clients
    while True:
        if len(active_clients) > 0:
            for client in active_clients:
                logger.debug(f'Processing {client}') 
            active_clients.pop()
        await asyncio.sleep(0.1)



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