TIMEOUT = 5
TOPIC = 'checks'


def add_common_cmd_args(arg_parser):
    arg_parser.add_argument(
        "--kafka-bootstrap-server",
        help="Kafka's service URI",
        required=True)
    arg_parser.add_argument(
        "--cert-path",
        help="Directory with SSL CA, cert and key files",
        default=".")
    arg_parser.add_argument("--kafka-topic", default=TOPIC)
    arg_parser.add_argument("--log-level", default='WARNING')
