import redis
import json
import argparse
from time import perf_counter_ns
import numpy as np
import uhd

parser = argparse.ArgumentParser("USRP_to_redis")
parser.add_argument("--redis_host", nargs='?', help="The Redis host you are attempting to connect to", default='localhost')
parser.add_argument("--redis_host_port", nargs='?', help="The Redis hosts port you are attempting to connect to", default='6379')
parser.add_argument("--redis_time_step_channel", nargs='?', help="The Redis channel you attempting to subscribe to for time steps", default='can')
parser.add_argument("--redis_transmit_channel", nargs='?', help="The Redis channel you attempting to publish to", default='can')
parser.add_argument("--usrp_serial_num", help="The serial number of the radio you are connecting to")
parser.add_argument("--usrp_num_samples", nargs='?', help="The number of samples you would like to read in each time step", default=1000)
parser.add_argument("--usrp_center_freq", nargs='?', help="The center frequency you would like to tune the radio to", default=2.403e9)
parser.add_argument("--usrp_sample_rate", nargs='?', help="The sampling rate of the radio", default=14e6)
parser.add_argument("--usrp_gain", nargs='?', help="The gain of the radio", default=20)
parser.add_argument("--mock_file_path", nargs="?", help="File you would like to read in inplace of serial device (used for testing)")

program_args = parser.parse_args()

redis_client = redis.StrictRedis(host=program_args.redis_host, port=program_args.redis_host_port, decode_responses=True)
redis_sub_client = redis_client.pubsub()
redis_sub_client.subscribe(program_args.redis_time_step_channel)

def radio_process():
    usrp = uhd.usrp.MultiUSRP(f"serial={program_args.usrp_serial_num}")
    usrp.set_rx_rate(program_args.usrp_sample_rate, 0)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(program_args.usrp_center_freq), 0)
    usrp.set_rx_gain(program_args.usrp_gain, 0)

    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    st_args.channels = [0,1]
    metadata = uhd.types.RXMetadata()
    streamer = usrp.get_rx_stream(st_args)
    recv_buffer = np.zeros((1, program_args.usrp_num_samples), dtype=np.complex64)
    while(True):
        scheduled_time_object = redis_sub_client.get_message()

        scheduled_time = scheduled_time_object["data"]

        while (perf_counter_ns() < scheduled_time):
            pass

        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        stream_cmd.stream_now = True
        streamer.issue_stream_cmd(stream_cmd)

        streamer.recv(recv_buffer, metadata)

        # Stop Stream
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
        streamer.issue_stream_cmd(stream_cmd)

        [phase_angle, sum_of_squares] = compute_signal_metrics(recv_buffer)
        angle_of_arrival = compute_angle_of_arrival(phase_angle)
        payload = {}
        payload["aoa"] = angle_of_arrival
        payload["ss"] = sum_of_squares
        payload["serial_num"] = program_args.usrp_serial_num
        redis_client.publish(program_args.redis_transmit_channel, json.dumps(payload))

def compute_signal_metrics(samples):

    complex_ss = np.multiply(samples[0], samples[0])

    complex_signal_diff = np.multiply(samples[0], np.conjugate(samples[1]))

    mean_complex_signal_diff = np.mean(complex_signal_diff)

    sum_of_squares = sum(np.absolute(complex_ss))

    phase_diff_rad = np.angle(mean_complex_signal_diff)

    return [phase_diff_rad, sum_of_squares]

def compute_angle_of_arrival(phase_angle):
    
    # Compute angle of arrival using phase interferometry formula
    aoa_rad = np.arcsin(phase_angle/ np.pi)
    
    # Convert angle from radians to degrees
    aoa_deg = np.degrees(aoa_rad)
    
    return aoa_deg