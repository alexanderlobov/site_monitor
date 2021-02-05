import logging
import json
import argparse
import os
import kafka
import psycopg2
from psycopg2.extras import execute_values
from site_monitor import config, logging_config
from site_monitor import schema


log = logging.getLogger('site_monitor.postgres_connector')


def consume_all(args):

    def cert_path(filename):
        return os.path.join(args.cert_path, filename)

    consumer = kafka.KafkaConsumer(
        args.kafka_topic,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        bootstrap_servers=args.kafka_bootstrap_server,
        security_protocol="SSL",
        ssl_cafile=cert_path("ca.pem"),
        ssl_certfile=cert_path("service.cert"),
        ssl_keyfile=cert_path("service.key"),
        group_id=args.kafka_group_id,
    )

    db_conn = psycopg2.connect(args.db_connection_string)
    db_cursor = db_conn.cursor()

    db_cursor.execute(schema.create_scheme_request(args.db_table_name))
    db_conn.commit()

    # default iterator interface can have issues. Details:
    # see https://blog.datasyndrome.com/a-tale-of-two-kafka-clients-c613efab49df

    try:
        while True:
            log.info('consume')
            raw_msgs = consumer.poll(timeout_ms=100000, max_records=10000)
            msgs = (
                json.loads(msg.value.decode())
                for partition, msgs in raw_msgs.items()
                for msg in msgs
            )
            execute_values(
                db_cursor,
                f"INSERT INTO {args.db_table_name} VALUES %s;",
                msgs,
                template=schema.EXECUTE_TEMPLATE
            )
            db_conn.commit()
            consumer.commit_async()
    finally:
        db_cursor.close()
        db_conn.close()

def parse_command_line_args():
    parser = argparse.ArgumentParser(
        description="Consumes data from Kafka and writes them to postgres")

    config.add_common_cmd_args(parser)
    parser.add_argument(
        "--kafka-group-id",
        help="Kafka's consumer group id",
        default="url-checks-to-postgres")
    parser.add_argument("--db-connection-string", required=True)
    parser.add_argument("--db-table-name", default="site_checks")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_command_line_args()
    logging_config.config_log(args.log_level)
    log.info('started')
    consume_all(args)
