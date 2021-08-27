#!/usr/bin/env python

import argparse

import asyncio
import websockets
import json
import time
import queue
from threading import Thread, Lock

QUEUE = []
START_AT = time.monotonic()


def run(target_url, change_delay, host, port):
    remote = websockets.connect(target_url)

    mutex = Lock()

    async def queue_mgmt():
        global QUEUE
        while True:
            mutex.acquire()
            print(QUEUE)
            if len(QUEUE) > 0:
                QUEUE = QUEUE[1:]
            mutex.release()
            await asyncio.sleep(change_delay)

    async def hello(websocket, path):

        async for message in websocket:
            mutex.acquire()
            if path not in QUEUE:
                QUEUE.append(path)
            mutex.release()
            if next(iter(QUEUE), '') == path:
                print("sending", path)
                t = (time.monotonic() - START_AT)+100
                jdata = json.loads(message[:-1])
                jdata['Data']['Compile'] = True
                jdata['Data']['ShaderTime'] = t
                async with remote as server:

                    await server.send(json.dumps(jdata) + message[-1])

    start_server = websockets.serve(hello, host, int(port))

    asyncio.ensure_future(queue_mgmt())
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create a merge server')
    parser.add_argument('target_url', type=str)
    parser.add_argument('--change_delay', type=int, default=5)
    parser.add_argument('--host', type=str, default="0.0.0.0")
    parser.add_argument('--port', type=int, default=8888)
    args = parser.parse_args()
    print(args)
    run(target_url=args.target_url,
        change_delay=args.change_delay,
        host=args.host,
        port=args.port)
