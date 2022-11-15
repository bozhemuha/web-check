#!/usr/bin/env python3

import asyncio
import aiohttp
import json
import logging
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(ROOT, "config.json")
LOG = os.path.join(ROOT, "web_check_results.log")


def get_config(option: str):
    with open(CONFIG) as data:
        config = json.loads(data.read())

        if option in config:
            return config[option]
        raise Exception(f"No attribute {option} in {CONFIG}")


def get_timeout(timeout_type: str, default_timeout=5):
    timeout = get_config(f"timeout_{timeout_type}")

    if not timeout:
        timeout = default_timeout
    return timeout


def get_target_list():
    targets = []

    for target in get_config("target_list"):
        targets.append(target)
    return targets


async def on_request_start(session, trace_config_ctx, params):
    trace_config_ctx.start = asyncio.get_event_loop().time()


async def on_request_end(session, trace_config_ctx, params):
    elapsed = asyncio.get_event_loop().time() - trace_config_ctx.start

    if params.response.status == 200:
        logging.info(f'{params.response.url} elapsed in {round(elapsed, 3)} with status: {params.response.status}')
        return
    
    raise Exception(f"{params.response.url} got unexpected status: {params.response.status}")


async def fetch(client, target, timeout):
    url = target["url"]
    expected_size = target["expected_content_size"]

    try:
        async with client.get(url, timeout=timeout) as response:
            result = await response.read()

            if len(result) != expected_size:
                logging.warning(f"Content size for {response.url} changed from {expected_size} to {len(result)} bytes")

    except asyncio.TimeoutError:
        logging.error(f"Timeout occurred for {url}")
    except Exception as e:
        logging.error(e)


async def main(targets, timeout):
    trace_config = aiohttp.TraceConfig()
    trace_config.on_request_start.append(on_request_start)
    trace_config.on_request_end.append(on_request_end)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=10), trace_configs=[trace_config]) as client:
        tasks = []
        for target in targets:
            task = asyncio.ensure_future(fetch(client, target, timeout))
            tasks.append(task)
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    target_list = get_target_list()
    timeout_global = get_timeout("global")
    timeout_request = get_timeout("request")
    timeout_interval = get_timeout("interval")

    logging.basicConfig(
        filename=LOG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
        level=logging.INFO,
    )

    print(f"\nRunning web check... \nTime estimated: {timeout_global} seconds")

    if os.name == 'nt':
    	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while timeout_global > 0:
        loop.run_until_complete(main(target_list, timeout_request))
        timeout_global -= timeout_interval
        time.sleep(timeout_interval)

    print(f"\nRun completed. \nResults: {LOG}\n")
