import asyncio
from asyncio.subprocess import PIPE
import os
import psycopg2
import pytest

def run_producer(name, kafka_bootstrap_server):
    return asyncio.create_subprocess_exec(
        "python",
        "-m",  "site_monitor.run_checker",
        "--kafka-bootstrap-server", kafka_bootstrap_server,
        "--check-interval-seconds", "100",
        "--log-level", "info",
        "--name", name,
        stdin=PIPE,
        stderr=open(name + ".log", "w"),
    )

def run_consumer(name, kafka_bootstrap_server, db_conn_string, table_name):
    return asyncio.create_subprocess_exec(
        "python", "-m", "site_monitor.postgres_connector",
        "--kafka-bootstrap-server", kafka_bootstrap_server,
        "--db-connection-string", db_conn_string,
        "--log-level", "info",
        "--db-table-name", table_name,
        "--name", name,
        stderr=open(name + ".log", "w"),
    )


def producer_name(index):
    return "producer" + str(index)


def consumer_name(index):
    return "consumer" + str(index)

# for this test the kafka topic should contains at least 3 partitions 

@pytest.mark.asyncio
async def test_many():
    kafka_bootstrap_server = os.environ['KAFKA_BOOTSTRAP_SERVER']
    db_conn_string = os.environ['DB_CONNECTION_STRING']
    table_name = 'test_table'
    n_producers = 3
    n_consumers = 3

    db_conn = psycopg2.connect(db_conn_string)
    db_cursor = db_conn.cursor()
    db_cursor.execute('DROP TABLE IF EXISTS ' + table_name)
    db_conn.commit()

    producers = [await run_producer(producer_name(id), kafka_bootstrap_server)
                 for id in range(n_producers)
                ]
    consumer0 = await run_consumer(consumer_name(0), kafka_bootstrap_server,
                                  db_conn_string, table_name)

    # let the first consumer create the table
    await asyncio.sleep(0.5)

    consumers = [consumer0] + \
                [await run_consumer(consumer_name(id), kafka_bootstrap_server,
                              db_conn_string, table_name)
                 for id in range(1, n_consumers)]

    with open("urls-1000.txt", "rb") as f:
        urls = f.readlines()

    n_urls_per_producer = len(urls) // n_producers;
    n_urls_total = n_urls_per_producer * n_producers;
    urls = urls[:n_urls_total]
    assert n_urls_per_producer > 0

    for i, p in enumerate(producers):
        start = i * n_urls_per_producer
        end  = start + n_urls_per_producer
        p.stdin.writelines(urls[start:end])
        p.stdin.write_eof()

    await asyncio.sleep(10)

    for p in producers:
        p.terminate()
        
    for c in consumers:
        c.terminate()

    for p in producers + consumers:
        await p.wait()

    db_cursor.execute('SELECT * from ' + table_name)
    records = db_cursor.fetchall()

    assert len(records) == n_urls_total;

    urls_in_db = set()
    producer_names = set()
    consumer_names = set()

    for rec in records:
        urls_in_db.add(rec[0])
        producer_names.add(rec[6])
        consumer_names.add(rec[7])

    for i in range(n_producers):
        assert producer_name(i) in producer_names

    for i in range(n_consumers):
        assert consumer_name(i) in consumer_names

    for url in urls:
        assert url.decode().strip() in urls_in_db

    db_cursor.close()
    db_conn.close()

if __name__ == "__main__":
    asyncio.run(test_many())
