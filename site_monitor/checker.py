import aiohttp
import asyncio
import time
import logging
import re
from site_monitor.schema import make_check_result

log = logging.getLogger('site_monitor.checker')

async def check_urls(on_check, urls, check_interval_seconds, check_regexp,
                     timeout):
    timeout = aiohttp.ClientTimeout(total=timeout)
    check_regexp_obj = re.compile(check_regexp, re.MULTILINE) \
                   if check_regexp is not None \
                   else None
    async with aiohttp.ClientSession(timeout=timeout) as session:
        check_time = time.perf_counter()
        while True:
            log.debug('check_urls')
            for url in urls:
                asyncio.create_task(_check_url(
                    url, session, on_check, timeout, check_regexp_obj))
            check_time += check_interval_seconds
            await asyncio.sleep(check_time - time.perf_counter())


async def _check_url(url, session, on_check, timeout, check_regexp):
    log.debug('check %s', url)
    time_start = time.perf_counter()
    request_timestamp = time.time()
    try:
        async with session.get(url) as resp:
            regexp_found = bool(check_regexp.search(await resp.text())) \
                    if check_regexp is not None \
                    else None
            on_check(
                make_check_result(
                    url, request_timestamp, status=resp.status,
                    response_time=time.perf_counter() - time_start,
                    regexp_found=regexp_found
            ))
    except aiohttp.ClientError as e:
        on_check(make_check_result(url, request_timestamp,
                                   error_msg=f'{type(e)}: {repr(e)}'))
    except asyncio.TimeoutError as e:
        on_check(make_check_result(url, request_timestamp,
                                   error_msg=f'timeout {timeout} sec'))
