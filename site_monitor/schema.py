# Use this function to check the number of parameters in check result.
# It also serves as a documentation.
# One also can use @dataclass, but it adds overhead for serialization because
# one need to call asdict(), that creates a copy of the variables dict

# parameters of these functions and variables should match
# TODO: autogeneration

def make_check_result(
        url,
        request_timestamp,
        status=None,
        error_msg=None,
        response_time=None,
        regexp_found=None,
        checker_name=None):
    return locals()

def create_scheme_request(table_name):
    return f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        url text,
        status smallint,
        error_msg text,
        response_time real,
        request_timestamp double precision,
        regexp_found boolean,
        checker_name text,
        consumer_name text,
        partition int
    )
    '''

EXECUTE_TEMPLATE=(
    "(%(url)s, "
    "%(status)s, "
    "%(error_msg)s, "
    "%(response_time)s, "
    "%(request_timestamp)s, "
    "%(regexp_found)s, "
    "%(checker_name)s,"
    "%(consumer_name)s,"
    "%(partition)s)"
)
