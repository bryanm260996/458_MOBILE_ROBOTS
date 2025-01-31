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

robot_name = 'foxtrot'
#
#
#joystick class
class Joystick:
    def __init__(self):
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

    # Main function to handle joystick input
    def get_commands(self):
        manual_mode = False

        try:
            while True:
                pygame.event.pump()  # Process joystick events

                # Toggle manual mode when button 0 ("A" button) is pressed
                if self.joystick.get_button(0):
                    manual_mode = not manual_mode
                    print(f"Manual mode {'activated' if manual_mode else 'deactivated'}")
                    time.sleep(0.3)  # Debounce delay

                if manual_mode:
                    # Get joystick axes for linear and angular velocities
                    linear_speed = -self.joystick.get_axis(1)  # Invert Y-axis for forward/backward
                    angular_speed = self.joystick.get_axis(0)  # X-axis for rotation

                    # Publish velocity and publish red light
                    publish_twist(linear_speed, -angular_speed)
                    play_lights(ros_node, robot_name, 'Red')

                else:
                    # Stop the robot and turn off lights
                    publish_twist(0.0, 0.0)
                    play_lights(ros_node, robot_name, 'Off')

                time.sleep(0.1)  # Loop at 10 Hz

        except KeyboardInterrupt:
            print("Joystick control interrupted.")
    
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

# main loop
if __name__ == "__main__":
    # initialize publishers, threads, and joystick
    robot = RobotController()
    joy = Joystick()

    while True:
        #start button event thread

        if pygame.event.get() == True:
            #join threads
            robot.end_threads()
            break
        #start all threads
        robot.start_threads()
        time.sleep(0.1) #10Hz

    #cleanup
    robot.cleanup()
    joy.quit()
    pygame.quit()
    ros_node.terminate()
