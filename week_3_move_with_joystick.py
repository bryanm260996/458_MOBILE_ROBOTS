import time
import roslibpy
import pygame

# Initialize pygame for joystick control
pygame.init()

# Connect to the ROS bridge
ros_node = roslibpy.Ros(host='192.168.8.104', port=9012)
ros_node.run()

robot_name = 'foxtrot'

# Create publishers for the /cmd_vel and /cmd_lightring topics
cmd_vel_pub = roslibpy.Topic(ros_node, f'/{robot_name}/cmd_vel', 'geometry_msgs/Twist')
led_pub = roslibpy.Topic(ros_node, f'/{robot_name}/cmd_lightring', 'irobot_create_msgs/LightringLeds')

# Initialize joystick
pygame.joystick.init()
if pygame.joystick.get_count() == 0:
    print("No joystick detected. Please connect a joystick and restart.")
    exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Joystick initialized: {joystick.get_name()}")

# Define helper functions for publishing messages
def publish_twist(linear_x, angular_z):
    twist_message = {
        "linear": {"x": linear_x, "y": 0.0, "z": 0.0},
        "angular": {"x": 0.0, "y": 0.0, "z": angular_z}
    }
    cmd_vel_pub.publish(roslibpy.Message(twist_message))

def set_led_color(r, g, b):
    led_colors = [{"red": r, "green": g, "blue": b} for _ in range(6)]
    led_message = {"leds": led_colors, "override_system": True}
    led_pub.publish(roslibpy.Message(led_message))

# Main function to handle joystick input
def send_joystick_commands():
    manual_mode = False

    try:
        while True:
            pygame.event.pump()  # Process joystick events

            # Toggle manual mode when button 0 ("A" button) is pressed
            if joystick.get_button(0):
                manual_mode = not manual_mode
                print(f"Manual mode {'activated' if manual_mode else 'deactivated'}")
                time.sleep(0.3)  # Debounce delay

            if manual_mode:
                # Get joystick axes for linear and angular velocities
                linear_speed = -joystick.get_axis(1)  # Invert Y-axis for forward/backward
                angular_speed = joystick.get_axis(0)  # X-axis for rotation

                # Publish velocity and activate red light
                publish_twist(linear_speed, -angular_speed)
                set_led_color(255, 255, 0)

            else:
                # Stop the robot and turn off lights
                publish_twist(0.0, 0.0)
                set_led_color(0, 0, 0)

            time.sleep(0.1)  # Loop at 10 Hz

    except KeyboardInterrupt:
        print("Joystick control interrupted.")
    finally:
        # Stop the robot and clean up resources
        publish_twist(0.0, 0.0)
        set_led_color(0, 0, 0)
        cmd_vel_pub.unadvertise()
        led_pub.unadvertise()
        ros_node.terminate()
        joystick.quit()
        pygame.quit()

# Run the joystick control loop
if __name__ == "__main__":
    send_joystick_commands()
