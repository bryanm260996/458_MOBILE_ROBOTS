import time
import roslibpy
import pygame
from lights_function import play_lights
import threading

# Initialize pygame and joystick control
pygame.init()
pygame.joystick.init()
if pygame.joystick.get_count() == 0:
        print("No joystick detected. Please connect a joystick and restart.")
        exit(1)

# Connect to the ROS bridge
ros_node = roslibpy.Ros(host='192.168.8.104', port=9012)
ros_node.run()

robot_name = 'echo'
#
#
#joystick class
class Joystick:
    def __init__(self):
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        self.thread_targets = [self.get_commands]
        self.threads = [threading.Thread(target = t, daemon=True) for t in self.thread_targets]
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        #modes
        self.manual_mode
        self.secondary_mode
        self.autonomous_mode

    # Main function to handle joystick input
    def get_commands(self):
        while not self.stop_event.is_set():

            # Toggle manual mode when button 0 ("A" button) is pressed
            if self.joystick.get_button(0):
                manual_mode = not manual_mode
                print(f"Manual mode {'activated' if manual_mode else 'deactivated'}")
                time.sleep(0.3)  # Debounce delay
            elif self.joystick.get_button(2):
                secondary_mode = not secondary_mode
                print(f"Secondary mode {'activated' if secondary_mode else 'deactivated'}")
                time.sleep(0.3)  # Debounce delay
            elif self.joystick.get_button(1):
                autonomous_mode = not autonomous_mode
                print(f"Autonomous mode {'activated' if autonomous_mode else 'deactivated'}")
                time.sleep(0.3)
            elif self.joystick.get_button(4):
                armed = not armed
                print(f"Robot {'armed' if armed else 'disarmed'}")
            else:
                pass

            if manual_mode == True:
                # Get joystick axes for linear and angular velocities
                linear_x = -self.joystick.get_axis(1)  # Invert Y-axis for forward/backward
                angular_z = self.joystick.get_axis(0)  # X-axis for rotation

                # set light
                color = 'Green'
            elif secondary_mode == True:
                color = 'Red'
            elif autonomous_mode == True:
                linear_x = 1
                angular_z = 1
                color = 'Violet'

            if armed:
                blink = True
            elif not armed:
                blink = False

            time.sleep(0.2)  # Loop at 5 Hz
        return color, blink, linear_x, angular_z
    
    def start_threads(self):
        [t.start() for t in self.threads]

    def end_threads(self):
        self.stop_event.set() #interrupt threads
        [t.join() for t in self.threads]
    
    def quit(self):
        self.joystick.quit()
#
#
# Robot class
class RobotController:
    def __init__(self):
        self.thread_targets = [self.drive, self.leds]
        self.threads = [threading.Thread(target = t, daemon=True) for t in self.thread_targets]
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        # create publisher on cmd_lightring topic, documentation at https://github.com/iRobotEducation/irobot_create_msgs/tree/rolling
        self.led_pub = roslibpy.Topic(ros_node, f'/{robot_name}/cmd_lightring', 'irobot_create_msgs/LightringLeds')
        # publisher on cmd_vel topic
        self.drive_pub = roslibpy.Topic(ros_node, f'/{robot_name}/cmd_vel', 'geometry_msgs/Twist')
        # publisher to cmd_audio topic
        #self.audio_pub = roslibpy.Topic(ros_node, f'/{robot_name}/cmd_audio', 'irobot_create_msgs/AudioNoteVector')

    def drive(self, linear_x, angular_z):
        # robot movement
        while not self.stop_event.is_set():
            drive_message = {"linear": {"x": linear_x, "y": 0.0, "z": 0.0},
                            "angular": {"x": 0.0, "y": 0.0, "z": angular_z}}
            self.drive_pub.publish(roslibpy.Message(drive_message))
            time.sleep(0.1) #10Hz

    def leds(self, color, blink = True):
        if blink == True:
            while not self.stop_event.is_set():
                play_lights(ros_node, robot_name, color)
                time.sleep(0.5) #2Hz
                play_lights(ros_node, robot_name, 'Off')
                time.sleep(0.5)
        elif blink == False:
            while not self.stop_event.is_set():
                play_lights(ros_node, robot_name, color)

    def start_threads(self):
        [t.start() for t in self.threads]

    def end_threads(self):
        self.stop_event.set() #interrupt threads
        [t.join() for t in self.threads]

    def cleanup(self):
        self.leds('Off')
        self.drive(0.0, 0.0)
        self.led_pub.unadvertise()
        self.drive_pub.unadvertise()


manual_mode = False
secondary_mode = False
autonomous_mode = False
armed = False
# main loop
if __name__ == "__main__":
    # initialize publishers, threads, and joystick
    robot = RobotController()
    joy = Joystick()
    
    #start all threads
    robot.start_threads()
    joy.start_threads()

    while True:
        pygame.event.get()  # Process joystick events
        if pygame.event.get():
            #join threads
            robot.end_threads()
            joy.end_threads()
            joy.get_commands()
            robot.drive()
            robot.leds()

        time.sleep(0.1) #10Hz

    #cleanup
    robot.cleanup()
    joy.quit()
    pygame.quit()
    ros_node.terminate()
