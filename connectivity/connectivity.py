import socket
import asyncio
import logging
from config import Config, Mode


logger = None
transport = None


class UDPServer:
    # https://docs.python.org/3/library/asyncio-protocol.html#asyncio-protocol
    def connection_made(self, transport):
        self.transport = transport
        logger.debug(f'Connection made')

    def datagram_received(self, data, addr):
        msg = data.decode()
        logger.info(f'{addr} {msg}')


class UDPClient:

    def connection_made(self, transport):
        self.transport = transport
        transport.sendto('beat'.encode(), (Config.TARGET_ADDR, Config.PORT))


async def create_server():
    global transport
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPServer(),
        local_addr=(Config.LOCAL_ADDR, Config.PORT)
    )
    logger.debug(dir(transport))
    logger.debug(protocol.__str__)


async def beat_sender():
    while True:
        if transport is not None:
            logger.debug('Sending beat...')
            transport.sendto('beat'.encode(), (Config.TARGET_ADDR, Config.PORT))
        await asyncio.sleep(Config.BEAT_SECS)


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


def main():
    setup_logging()
    loop = asyncio.get_event_loop()
    tasks = []
    if Config.MODE is Mode.CLIENT:
        '''
        Just send heart beats to target
        '''
        tasks.append(loop.create_task(beat_sender()))
    elif Config.MODE is Mode.SERVER:
        '''
        Just listen for heart beats from target
        '''
        tasks.append(loop.create_task(create_server()))
    if Config.MODE is Mode.CLIENT_SERVER:
        '''
        Listen for heart beats and send heart beats
        '''
        tasks.append(loop.create_task(create_server()))
        tasks.append(loop.create_task(beat_sender()))

    all_tasks = asyncio.gather(*tasks)

    try:
        loop.run_until_complete(all_tasks)
    except KeyboardInterrupt:
        logger.info('Program exiting...')
        logging.shutdown()


if __name__ == '__main__':
    main()