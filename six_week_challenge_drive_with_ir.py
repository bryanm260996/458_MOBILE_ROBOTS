import roslibpy
import time

# Configuration
IP = '192.168.8.104'
PORT = 9012
ROBOT_NAME = 'india'

# Initialize ROS connection
ros = roslibpy.Ros(host=IP, port=PORT)
ros.run()

# Function to create movement commands
def create_movement_command(linear_speed=0.1, angular_speed=0.0):
    return {
        'linear': {'x': linear_speed, 'y': 0.0, 'z': 0.0},
        'angular': {'x': 0.0, 'y': 0.0, 'z': angular_speed}
    }

# Movement functions
def move_forward():
    movement_command = create_movement_command(linear_speed=0.5)
    movement_publisher.publish(roslibpy.Message(movement_command))

def move_slow_and_turn(error):
    k = 1  # Proportional control constant
    angular_speed = k * error * -0.1  # Negative for right turn
    movement_command = create_movement_command(linear_speed=0.3, angular_speed=angular_speed)
    movement_publisher.publish(roslibpy.Message(movement_command))

def move_slow_and_turn(error):
    k = 1  # Proportional control constant
    angular_speed = k * error * -0.1  # Negative for right turn
    movement_command = create_movement_command(linear_speed=0.3, angular_speed=angular_speed)
    movement_publisher.publish(roslibpy.Message(movement_command))
def stop_robot():
    movement_command = create_movement_command(linear_speed=0.0)
    movement_publisher.publish(roslibpy.Message(movement_command))


def move_right(error):
    k = 1  # Proportional control constant
    angular_speed = k * error * -0.1  # Negative for right turn
    movement_command = create_movement_command(linear_speed=0.0, angular_speed=angular_speed)
    movement_publisher.publish(roslibpy.Message(movement_command))


def move_left(error):
    k = 1  # Proportional control constant
    angular_speed = k * error * -0.1  # Positive for left turn
    movement_command = create_movement_command(linear_speed=0.0, angular_speed=angular_speed)
    movement_publisher.publish(roslibpy.Message(movement_command))



# IR sensor callback
def callback_ir(message):
    values = [reading['value'] for reading in message['readings']]
    front_value = values[3]  # Adjust index based on sensor configuration
    left_value = values[0]
    right_value = values[6]
    left_center= values[2]
    right_center=values[5]

    error = left_value - right_value

    #print(f'{ROBOT_NAME} IR values: {values}')
    if front_value>10:
        print('object in front')
        error=error*100
        move_slow_and_turn(error)
    elif left_center>10:
        error= error*100
        move_slow_and_turn(error)
    elif right_center>10:
        error= error*100
        move_slow_and_turn(error)
    elif left_value>10:
        error= error*100
        move_slow_and_turn(error)
    elif right_value>10:
        error= error*100
        move_slow_and_turn(error)   


    if error > 10:
        #print('Obstacle detected on the left! Turning RIGHT...')
        print(f'moving right error is:{error}')
        move_right(error)
    elif error < -10:
        #print('Obstacle detected on the right! Turning LEFT...')
        print(f'moving left error is:{error}')
        move_left(error)
    else:
        print('Path is clear. Moving FORWARD...')
        move_forward()

    return error

# Initialize movement publisher
movement_topic = roslibpy.Topic(ros, f'/{ROBOT_NAME}/cmd_vel', 'geometry_msgs/Twist')
movement_publisher = movement_topic

# Initialize IR sensor subscriber
ir_intensity_topic = roslibpy.Topic(ros, f'/{ROBOT_NAME}/ir_intensity', 'irobot_create_msgs/msg/IrIntensityVector')
ir_subscriber = ir_intensity_topic.subscribe(callback_ir)

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('Shutting down robot control...')
    ir_subscriber.unsubscribe()
    stop_robot()
    ros.terminate()
