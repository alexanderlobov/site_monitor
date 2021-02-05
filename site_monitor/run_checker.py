import asyncio
import argparse
import os
from site_monitor import config, logging_config
from site_monitor.checker import check_urls
import json
import kafka
import logging
import sys


log = logging.getLogger('site_monitor.run_checker')


def read_urls():
    return [l.strip() for l in sys.stdin]


def run_checker(args):

    def cert_path(filename):
        return os.path.join(args.cert_path, filename)

    producer = kafka.KafkaProducer(
        bootstrap_servers=args.kafka_bootstrap_server,
        security_protocol="SSL",
        ssl_cafile=cert_path("ca.pem"),
        ssl_certfile=cert_path("service.cert"),
        ssl_keyfile=cert_path("service.key"),
    )

    def send(check_result):
        log.info("%s", check_result)
        producer.send(
            args.kafka_topic,
            key=check_result['url'].encode(),
            value=json.dumps(check_result).encode()
        )

    urls = read_urls()
    asyncio.run(check_urls(send, urls, args.check_interval_seconds,
                           args.check_regexp, config.TIMEOUT))


def parse_command_line_args():
    parser = argparse.ArgumentParser(description=
        "Monitor websites availability and produces the metrics to Kafka")

    config.add_common_cmd_args(parser)
    parser.add_argument("--check-interval-seconds", type=float, default=60)
    parser.add_argument("--check-regexp")

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_command_line_args()
    logging_config.config_log(args.log_level)
    log.info('started')
    run_checker(args)
