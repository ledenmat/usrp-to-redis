
import redis
import json
import argparse
from time import perf_counter_ns
import numpy as np
import uhd

parser = argparse.ArgumentParser("USRP_to_redis")
parser.add_argument("--redis_host", nargs='?', help="The Redis host you are attempting to connect to", default='localhost')
parser.add_argument("--redis_host_port", nargs='?', help="The Redis hosts port you are attempting to connect to", default='6379')
parser.add_argument("--redis_time_step_channel", nargs='?', help="The Redis channel you attempting to subscribe to for time steps", default='usrp')
parser.add_argument("--redis_transmit_channel", nargs='?', help="The Redis channel you attempting to publish to", default='usrp')

program_args = parser.parse_args()

redis_client = redis.StrictRedis(host=program_args.redis_host, port=program_args.redis_host_port, decode_responses=True)
redis_sub_client = redis_client.pubsub(ignore_subscribe_messages=True)
redis_sub_client.subscribe(program_args.redis_time_step_channel)

serial_nums = ["316405C", "3164076"]

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



def intersection_point_calculation(angle1, distance2, angle2):
    # Convert angles to radians
    angle1_rad = np.radians(angle1)
    angle2_rad = np.radians(angle2)
    
    # Calculate x-coordinate of the second endpoint (which lies on the y-axis)
    end_point2_x = 0
    
    # Calculate y-coordinate of the second endpoint
    end_point2_y = distance2
    
    # Calculate direction vectors of the rays
    direction1 = np.array([np.cos(angle1_rad), np.sin(angle1_rad)])
    direction2 = np.array([np.cos(angle2_rad), np.sin(angle2_rad)])
    
    # Calculate intersection point using vectorized calculations
    # If determinant of direction vectors is zero, rays are parallel
    det = np.linalg.det(np.stack([direction1, direction2], axis=0))
    if np.isclose(det, 0):
        print("The rays are parallel, no intersection point exists.")
        return None
    else:
        # Calculate intersection point using vectorized formula
        intersection = np.linalg.solve(np.stack([direction1, -direction2], axis=1), end_point2_x - np.array([0, end_point2_y]))
        return intersection
    
def radio_process():
    radios = {}
    for data_object in redis_sub_client.listen():
        data = json.loads(data_object["data"])
        if data['serial_num'] != "Distance to Drone" and data['ss'] >7:
            radios[data['serial_num']] = data

            if len(radios) >= 2:
                payload = {}
                
                payload['aoa'] = np.linalg.norm(intersection_point_calculation(radios[serial_nums[0]]['aoa'], 1.473, radios[serial_nums[1]]['aoa']))
                payload['serial_num'] = "Distance to Drone"
                payload["ss"] = 1
                print(payload)
                redis_client.publish(program_args.redis_transmit_channel, json.dumps(payload))

radio_process()