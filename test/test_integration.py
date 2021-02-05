import asyncio
import os
import signal
import pytest
import psycopg2

@pytest.mark.asyncio
async def test1():
    kafka_bootstrap_server = os.environ['KAFKA_BOOTSTRAP_SERVER']
    db_conn_string = os.environ['DB_CONNECTION_STRING']
    table_name = 'test_table'

    db_conn = psycopg2.connect(db_conn_string)
    db_cursor = db_conn.cursor()
    db_cursor.execute('DROP TABLE IF EXISTS ' + table_name)
    db_conn.commit()

    producer = await asyncio.create_subprocess_exec(
        "python",
        "-m",  "site_monitor.run_checker",
        "--kafka-bootstrap-server", kafka_bootstrap_server,
        "--check-interval-seconds", "100",
        "--log-level", "info",
        stdin=open("test/urls.txt")
    )

    consumer = await asyncio.create_subprocess_exec(
        "python", "-m", "site_monitor.postgres_connector",
        "--kafka-bootstrap-server", kafka_bootstrap_server,
        "--db-connection-string", db_conn_string,
        "--log-level", "info",
        "--db-table-name", table_name,
    )

    await asyncio.sleep(10)

    producer.terminate()
    consumer.terminate()

    db_cursor.execute('SELECT * from ' + table_name)
    records = db_cursor.fetchall()

    rec_dict = {rec[0]: rec for rec in records}
    # TODO: add more checks
    assert 'https://google.com' in rec_dict
    assert 'https://youtube.com' in rec_dict
    assert 'https://facebook.com' in rec_dict

    await producer.wait()
    await consumer.wait()

    db_cursor.close()
    db_conn.close()
