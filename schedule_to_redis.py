import redis
import argparse
from time import perf_counter_ns
import time

parser = argparse.ArgumentParser("USRP_to_redis")
parser.add_argument("--redis_host", nargs='?', help="The Redis host you are attempting to connect to", default='localhost')
parser.add_argument("--redis_host_port", nargs='?', help="The Redis hosts port you are attempting to connect to", default='6379')
parser.add_argument("--redis_transmit_channel", nargs='?', help="The Redis channel you attempting to publish to", default='usrp_time')

program_args = parser.parse_args()

redis_client = redis.StrictRedis(host=program_args.redis_host, port=program_args.redis_host_port, decode_responses=True)

def radio_process():
    while(True):
        payload = perf_counter_ns() + 1000
        redis_client.publish(program_args.redis_transmit_channel, payload)
        time.sleep(0.25)

radio_process()