import roslibpy
import time

def run_lights(ros_node, robot_name):
    # Initialize the LED publisher
    led_pub = roslibpy.Topic(ros_node, f'/{robot_name}/cmd_lightring', 'irobot_create_msgs/LightringLeds')

    # Define color patterns
    colors = [
        [{"red": 255, "green": 0, "blue": 0}]*6,  # Red
        [{"red": 0, "green": 255, "blue": 0}]*6,  # Green
        [{"red": 0, "green": 0, "blue": 255}]*6   # Blue
    ]
    
    # Main loop
    try:
        while True:
            for color_pattern in colors:
                # Compose a LightringLeds message
                lightring_led_message = {"leds": color_pattern, "override_system": True}
                lightring_ros_msg = roslibpy.Message(lightring_led_message)

                # Publish the message
                led_pub.publish(lightring_ros_msg)
                time.sleep(1)  # Wait for 1 second between updates
    except KeyboardInterrupt:
        print("Shutting down lights...")
    finally:
        # Clean up when exiting the loop
        led_pub.unadvertise()
        ros_node.terminate()
