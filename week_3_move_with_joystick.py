import time
import roslibpy
import pygame

# Initialize pygame for joystick control
pygame.init()

# Connect to the ROS bridge
ros_node = roslibpy.Ros(host='192.168.8.104', port=9012)
ros_node.run()

robot_name = 'foxtrot'

# Create publisher for the /cmd_vel topic
cmd_vel_pub = roslibpy.Topic(ros_node, f'/{robot_name}/cmd_vel', 'geometry_msgs/Twist')

# Initialize joystick
if pygame.joystick.get_count() == 0:
    print("No joystick detected. Please connect a joystick and restart.")
    exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Joystick initialized: {joystick.get_name()}")

# Define a function to send velocity commands based on joystick input
def send_joystick_commands():
    manual_mode = False
    try:
        while True:
            pygame.event.pump()  # Process joystick events

            # Check for button press to toggle manual mode
            if joystick.get_button(0):  # Assuming "A" button is button 0
                manual_mode = not manual_mode
                print(f"Manual mode {'activated' if manual_mode else 'deactivated'}")
                time.sleep(0.3)  # Debounce delay

            if manual_mode:
                # Get joystick axes for linear and angular velocities
                linear_speed = -joystick.get_axis(1)  # Invert Y-axis for forward/backward
                angular_speed = joystick.get_axis(0)  # X-axis for rotation

                # Define the Twist message
                twist_message = {
                    "linear": {"x": linear_speed, "y": 0.0, "z": 0.0},
                    "angular": {"x": 0.0, "y": 0.0, "z": -angular_speed}
                }

                # Publish the message
                ros_msg = roslibpy.Message(twist_message)
                cmd_vel_pub.publish(ros_msg)

            else:
                # Stop the robot if manual mode is deactivated
                stop_message = {
                    "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
                }
                cmd_vel_pub.publish(roslibpy.Message(stop_message))

            time.sleep(0.1)  # Loop at 10 Hz

    except KeyboardInterrupt:
        print("Joystick control interrupted.")
    finally:
        # Stop the robot when exiting
        stop_message = {
            "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
            "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
        }
        cmd_vel_pub.publish(roslibpy.Message(stop_message))
        cmd_vel_pub.unadvertise()
        ros_node.terminate()
        joystick.quit()
        pygame.quit()

# Run the joystick control loop
send_joystick_commands()
