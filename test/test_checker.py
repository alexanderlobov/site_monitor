import asyncio
import pytest
from aiohttp import web
from site_monitor.checker import check_urls


async def respond_hello(request):
    return web.Response(text='hello')


async def check_result(unused_tcp_port, server_respond, check_regexp, test_func):
    server = web.Application()
    server.add_routes([web.get('/', server_respond)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', unused_tcp_port)
    await site.start()

    queue = asyncio.Queue()

    def on_check(check_result):
        queue.put_nowait(check_result)

    url = 'http://localhost:' + str(unused_tcp_port)

    client_task = asyncio.create_task(
        check_urls(on_check, [url], check_interval_seconds=1000,
                   check_regexp=check_regexp, timeout=0.3))

    check_result = await queue.get()

    assert check_result['url'] == url

    test_func(check_result)

    client_task.cancel()
    await runner.cleanup()


@pytest.mark.asyncio
async def test_200_regexp_true(unused_tcp_port):
    def test(check_result):
        assert check_result['status'] == 200
        assert check_result['error_msg'] == None
        assert check_result['regexp_found'] == True

    await check_result(unused_tcp_port, respond_hello, 'hello', test)


@pytest.mark.asyncio
async def test_200_regexp_false(unused_tcp_port):
    def test(check_result):
        assert check_result['status'] == 200
        assert check_result['error_msg'] == None
        assert check_result['regexp_found'] == False

    await check_result(unused_tcp_port, respond_hello, 'notfound', test)


@pytest.mark.asyncio
async def test_long_answer(unused_tcp_port):
    def test(check_result):
        assert check_result['status'] == None
        assert 'timeout' in check_result['error_msg']
        assert check_result['regexp_found'] == None

    async def server_respond(request):
        await asyncio.sleep(100)

    await check_result(unused_tcp_port, server_respond, 'hello', test)


@pytest.mark.asyncio
async def test_not_found(unused_tcp_port):
    def test(check_result):
        assert check_result['status'] == 404
        assert check_result['error_msg'] == None
        assert check_result['regexp_found'] == False

    async def server_respond(request):
        return web.Response(status=404)

    await check_result(unused_tcp_port, server_respond, 'hello', test)
