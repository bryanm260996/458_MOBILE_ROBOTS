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

# Joystick class
class Joystick:
    def __init__(self):
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        self.stop_event = threading.Event()

        # State variables
        self.manual_mode = False
        self.secondary_mode = False
        self.autonomous_mode = False
        self.armed = False
        self.linear_x = 0.0
        self.angular_z = 0.0
        self.color = 'Off'
        self.blink = False

        # Create and start thread
        self.thread = threading.Thread(target=self.get_commands, daemon=True)
        self.thread.start()

    def get_commands(self):
        while not self.stop_event.is_set():
            pygame.event.pump()  # Process joystick events

            if self.joystick.get_button(0):  # "A" button
                self.manual_mode = not self.manual_mode
                self.secondary_mode = False
                self.autonomous_mode = False
                print(f"Manual mode {'activated' if self.manual_mode else 'deactivated'}")
                time.sleep(0.3)  # Debounce delay

            if self.joystick.get_button(2):  # "X" button
                self.secondary_mode = not self.secondary_mode
                self.manual_mode = False
                self.autonomous_mode = False
                print(f"Secondary mode {'activated' if self.secondary_mode else 'deactivated'}")
                time.sleep(0.3)

            if self.joystick.get_button(1):  # "B" button
                self.autonomous_mode = not self.autonomous_mode
                self.manual_mode = False
                self.secondary_mode = False
                print(f"Autonomous mode {'activated' if self.autonomous_mode else 'deactivated'}")
                time.sleep(0.3)

            if self.joystick.get_button(4):  # Left bumper
                self.armed = not self.armed
                print(f"Robot {'armed' if self.armed else 'disarmed'}")
                time.sleep(0.3)

            # Determine movement & LED state
            if self.manual_mode:
                self.linear_x = -self.joystick.get_axis(1)  # Invert Y-axis for forward/backward
                self.angular_z = -self.joystick.get_axis(0)  # X-axis for rotation
                self.color = 'Green'
            elif self.secondary_mode:
                self.color = 'Red'
            elif self.autonomous_mode:
                self.linear_x = 1
                self.angular_z = 1
                self.color = 'Violet'

            self.blink = self.armed  # Blink if armed
            if self.armed == False:
                self.linear_x = 0
                self.angular_z = 0

            time.sleep(0.1)  # Loop at 5 Hz

    def stop(self):
        self.stop_event.set()
        self.thread.join()
        self.joystick.quit()


# Robot class
class RobotController:
    def __init__(self, joystick):
        self.joystick = joystick
        self.stop_event = threading.Event()

        # ROS publishers
        self.led_pub = roslibpy.Topic(ros_node, f'/{robot_name}/cmd_lightring', 'irobot_create_msgs/LightringLeds')
        self.drive_pub = roslibpy.Topic(ros_node, f'/{robot_name}/cmd_vel', 'geometry_msgs/Twist')

        # Create and start threads
        self.drive_thread = threading.Thread(target=self.drive, daemon=True)
        self.led_thread = threading.Thread(target=self.leds, daemon=True)
        self.drive_thread.start()
        self.led_thread.start()

    def drive(self):
        while not self.stop_event.is_set():
            drive_message = {
                "linear": {"x": self.joystick.linear_x, "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0, "y": 0.0, "z": self.joystick.angular_z}
            }
            self.drive_pub.publish(roslibpy.Message(drive_message))
            time.sleep(0.1)  # 10Hz
            if self.joystick.armed == False:
                drive_message = {
                "linear": {"x": self.joystick.linear_x, "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0, "y": 0.0, "z": self.joystick.angular_z}
            }
            self.drive_pub.publish(roslibpy.Message(drive_message))
            time.sleep(0.1)  # 10Hz

    def leds(self):
        while not self.stop_event.is_set():
            play_lights(ros_node, robot_name, self.joystick.color)
            if self.joystick.blink:
                time.sleep(0.5)  # Blink on
                play_lights(ros_node, robot_name, 'Off')
                time.sleep(0.5)  # Blink off
            else:
                time.sleep(1)  # Keep the LED color

    def stop(self):
        self.stop_event.set()
        self.drive_thread.join()
        self.led_thread.join()
        self.cleanup()

    def cleanup(self):
        play_lights(ros_node, robot_name, 'Off')
        self.drive_pub.publish(roslibpy.Message({"linear": {"x": 0.0, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 0.0}}))
        self.led_pub.unadvertise()
        self.drive_pub.unadvertise()


# Main loop
if __name__ == "__main__":
    try:
        joystick = Joystick()
        robot = RobotController(joystick)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt  # Graceful exit

            time.sleep(0.1)  # 10Hz loop

    except KeyboardInterrupt:
        print("\nShutting down...")
        robot.stop()
        joystick.stop()
        pygame.quit()
        ros_node.terminate()
        print("Shutdown complete.")
