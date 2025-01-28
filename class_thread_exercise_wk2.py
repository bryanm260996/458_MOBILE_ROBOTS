import time
import roslibpy
import threading
import math
import random

# establish roslibpy connection to sim
ros_node = roslibpy.Ros(host='127.0.0.1', port=9012)
robot_name = '/juliet'

# establish connection to foxtrot
#ros_node = roslibpy.Ros(host='192.168.8.104', port=9012)
#robot_name = '/foxtrot'

ros_node.run()

# create class RobotController
class RobotController:
    def __init__(self):
        self.thread_targets = [ self.random_led, self.play_audio, self.circle_track]
        self.threads = [threading.Thread(target = t, daemon=True) for t in self.thread_targets]
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        # create publisher on cmd_lightring topic, documentation at https://github.com/iRobotEducation/irobot_create_msgs/tree/rolling
        self.led_pub = roslibpy.Topic(ros_node, f'{robot_name}/cmd_lightring', 'irobot_create_msgs/LightringLeds')
        # publisher on cmd_vel topic
        self.circle_track_pub = roslibpy.Topic(ros_node, f'{robot_name}/cmd_vel', 'geometry_msgs/Twist')
        # publisher to cmd_audio topic
        self.audio_pub = roslibpy.Topic(ros_node, f'{robot_name}/cmd_audio', 'irobot_create_msgs/AudioNoteVector')

    def circle_track(self):
        # placeholder for robot movement
        while not self.stop_event.is_set():
            drive_message = {'linear':{'x':1, 'y':0, 'z':0}, 
                            'angular':{'x':0, 'y':0, 'z':2}}
            self.circle_track_pub.publish(roslibpy.Message(drive_message))
            time.sleep(0.25)

    def random_led(self):
        while not self.stop_event.is_set():
            # create random led array
            led_rand = [{'red':random.randint(0,255), 'green':random.randint(0,255), 'blue':random.randint(0,255)},
                        {'red':random.randint(0,255), 'green':random.randint(0,255), 'blue':random.randint(0,255)},
                        {'red':random.randint(0,255), 'green':random.randint(0,255), 'blue':random.randint(0,255)},
                        {'red':random.randint(0,255), 'green':random.randint(0,255), 'blue':random.randint(0,255)},
                        {'red':random.randint(0,255), 'green':random.randint(0,255), 'blue':random.randint(0,255)},
                        {'red':random.randint(0,255), 'green':random.randint(0,255), 'blue':random.randint(0,255)},
                        ]
            # generate and publish to robot
            lightring_led_message = {'leds': led_rand, 'override_system': True}
            self.led_pub.publish(roslibpy.Message(lightring_led_message))
            time.sleep(0.2) #send at 5 Hz

    def play_audio(self):
        # documentation: https://github.com/iRobotEducation/irobot_create_msgs/blob/rolling/msg/AudioNoteVector.msg
        while not self.stop_event.is_set():
            notes = [{'frequency': 750, 'max_runtime': {'sec': 1,'nanosec':0}},
                    {'frequency': 600, 'max_runtime': {'sec': 1,'nanosec':0}}]
            audio_message = {'notes': notes,'append': False}
            self.audio_pub.publish(roslibpy.Message(audio_message))
            time.sleep(2)
    
    def start_threads(self):
        [t.start() for t in self.threads]

    def end_threads(self):
        self.stop_event.set() #interrupt threads
        [t.join() for t in self.threads]

    def run_loop(self):
        self.start_threads()
        time.sleep(10)
        self.end_threads()

    def cleanup(self):
        self.led_pub.unadvertise()
        self.circle_track_pub.unadvertise()

if __name__ == '__main__':
    #create object of class
    robot_interface = RobotController()

    robot_interface.run_loop()
    
    robot_interface.cleanup()
    print('finished')

ros_node.terminate()