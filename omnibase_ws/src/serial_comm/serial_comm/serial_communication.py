import rclpy
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node
from std_msgs.msg import String, Float32, Float32MultiArray, Int32MultiArray
import serial
import threading
import time
import re

class SerialCommNode(Node):
    def __init__(self):
        super().__init__('serial_comm_node')

        # Set up serial
        self.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.2)

        # Desired pose: [x, y, phi, d, r]  + PID GAINS
        # self.message_tx = [6, 3, 0.5, 1.0, 1.0, 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 7.1, 7.2, 7.3]
        self.count = 0

        self.pose_names = ['x', 'y', 'phi', 'd', 'r']
        default_gains = [0.5, 0.1, 0.0, 0.5, 0.1, 0.0, 0.5, 0.1, 0.0, 0.5, 0.1, 0.0, 0.5, 0.1, 0.0, 0.5, 0.1, 0.0, 0.5, 0.1, 0.0]
        default_pose = [6.0, 3.0, 0.5, 1.0, 1.0]
        default_velocities = [0.5, 0.6, 0.7, 0.4]
        self.velocity_names = ['u1_desired', 'u2_desired', 'u3_desired', 'u4_desired']
        # PID gain parameters
        self.gain_names = [
            'x_kp', 'x_ki', 'x_kd',
            'y_kp', 'y_ki', 'y_kd',
            'phi_kp', 'phi_ki', 'phi_kd',
            'u0_kp', 'u0_ki', 'u0_kd',
            'u1_kp', 'u1_ki', 'u1_kd',
            'u2_kp', 'u2_ki', 'u2_kd',
            'u3_kp', 'u3_ki', 'u3_kd',
        ]

        # Declare all parameters
        for i, name in enumerate(self.pose_names):
            self.declare_parameter(name, default_pose[i])
        for i, name in enumerate(self.velocity_names):
            self.declare_parameter(name, default_velocities[i])
        for i, name in enumerate(self.gain_names):
            self.declare_parameter(name, default_gains[i])

        self.message_tx = [self.get_parameter(n).value for n in self.pose_names + self.velocity_names + self.gain_names]

        # Set parameter callback
        self.add_on_set_parameters_callback(self.update_parameters)

        # Timer to send pose
        self.timer_period = 0.1
        self.timer = self.create_timer(self.timer_period, self.send_mesage)

        # Publisher for full STM32 parsed state as debug
        self.state_pub = self.create_publisher(String, 'stm32_debug', 10)
        
        # Received INFO publishers
        self.pose_pub         = self.create_publisher(Float32MultiArray, 'stm32/pose', 10)         # [x, y, phi, d, r]
        self.imu_pub          = self.create_publisher(Float32MultiArray, 'stm32/imu', 10)          # [roll, pitch, yaw]
        self.omega_pub        = self.create_publisher(Float32MultiArray, 'stm32/omegas', 10)       # [ω1, ω2, ω3, ω4]
        self.real_speeds_pub  = self.create_publisher(Float32MultiArray, 'stm32/real_speeds', 10)  # [φ_dot, x_dot, y_dot]
        self.odom_pub         = self.create_publisher(Float32MultiArray, 'stm32/odom', 10)         # [phi, x, y]
        self.errors_pub       = self.create_publisher(Float32MultiArray, 'stm32/errors', 10)       # [dx, dy, dphi]
        self.u_errors_pub     = self.create_publisher(Float32MultiArray, 'stm32/u_errors', 10)     # [u_err[0], u_err[1], u_err[2],u_err[3]]
        self.ctrl_speeds_pub  = self.create_publisher(Float32MultiArray, 'stm32/ctrl_speeds', 10)  # [x_dot, y_dot, phi_dot]
        self.ctrl_u_pub       = self.create_publisher(Float32MultiArray, 'stm32/ctrl_u', 10)       # [u1, u2, u3, u4]
        self.pwm_pub          = self.create_publisher(Int32MultiArray,   'stm32/pwm', 10)          # [duty1, duty2, duty3, duty4]
        self.ts_pub           = self.create_publisher(Int32MultiArray,   'stm32/timing', 10)       # [ts_current, ts_previous, ts_delta]
        self.encoders_pub     = self.create_publisher(Int32MultiArray,   'stm32/encoders', 10)     # [TIM1, TIM2, TIM4, TIM8]
        self.x_pid_pub   = self.create_publisher(Float32MultiArray, 'stm32/pid_gains/x', 10)       # X position PID gains
        self.y_pid_pub   = self.create_publisher(Float32MultiArray, 'stm32/pid_gains/y', 10)       # Y position PID gains
        self.phi_pid_pub = self.create_publisher(Float32MultiArray, 'stm32/pid_gains/phi', 10)     # heading angle PID gains
        self.u0_pid_pub  = self.create_publisher(Float32MultiArray, 'stm32/pid_gains/u0', 10)      # Motor1 velocity PID gains
        self.u1_pid_pub  = self.create_publisher(Float32MultiArray, 'stm32/pid_gains/u1', 10)      # Motor2 velocity PID gains
        self.u2_pid_pub  = self.create_publisher(Float32MultiArray, 'stm32/pid_gains/u2', 10)      # Motor3 velocity PID gains
        self.u3_pid_pub  = self.create_publisher(Float32MultiArray, 'stm32/pid_gains/u3', 10)      # Motor4 velocity PID gains


        self.pose_data = Float32MultiArray()
        self.imu_data = Float32MultiArray()
        self.omega_data = Float32MultiArray()
        self.odom_data = Float32MultiArray()
        self.errors_data = Float32MultiArray()
        self.u_errors_data = Float32MultiArray()
        self.ctrl_speeds_data = Float32MultiArray()
        self.ctrl_u_data = Float32MultiArray()
        self.pwm_data = Int32MultiArray()
        self.ts_data = Int32MultiArray()
        self.encoders_data = Int32MultiArray()
        self.x_pid_data   = Float32MultiArray()
        self.y_pid_data   = Float32MultiArray()
        self.phi_pid_data = Float32MultiArray()
        self.u0_pid_data  = Float32MultiArray()
        self.u1_pid_data  = Float32MultiArray()
        self.u2_pid_data  = Float32MultiArray()
        self.u3_pid_data  = Float32MultiArray()

        # Start receiver thread
        self.recv_thread = threading.Thread(target=self.receiver, daemon=True)
        self.recv_thread.start()


    def update_parameters(self, params):
        for param in params:
            if param.name in self.pose_names:
                idx = self.pose_names.index(param.name)
                self.message_tx[idx] = param.value
            elif param.name in self.velocity_names:
                idx = self.velocity_names.index(param.name)
                self.message_tx[5 + idx] = param.value
            elif param.name in self.gain_names:
                idx = self.gain_names.index(param.name)
                self.message_tx[9 + idx] = param.value
        return SetParametersResult(successful=True)


    def send_mesage(self):
        rounded_pose = [round(val, 2) for val in self.message_tx]
        cmd_str = f"{' '.join(map(str, rounded_pose))}\r\n"
        self.ser.write(cmd_str.encode())
        self.get_logger().info(f"📤 [{self.count}] Sent: {repr(cmd_str)}")
        self.count += 1

    def receiver(self):
        while rclpy.ok():
            line = self.ser.readline().decode(errors='ignore').strip()
            if line:
                # self.get_logger().info(f"🔤 Raw line: {line}")
                try:
                    matches = re.findall(r'(\w+)=([-+]?\d*\.\d+|\d+)', line)
                    data = {key: float(val) for key, val in matches}
                    # self.get_logger().info(f"✅ Parsed values: {data}")
                    output = f"""📥 Parsed Robot State:
    ➤ Desired Pose: x={data.get('x_desired', 0):.2f}, y={data.get('y_desired', 0):.2f}, phi={data.get('phi_desired', 0):.2f}, d={data.get('d', 0):.2f}, r={data.get('r', 0):.2f}
    ➤ IMU: roll={data.get('roll', 0):.2f}, pitch={data.get('pitch', 0):.2f}, yaw={data.get('yaw', 0):.2f}
    ➤ Encoders: TIM1={int(data.get('TIM1', 0))}, TIM2={int(data.get('TIM2', 0))}, TIM4={int(data.get('TIM4', 0))}, TIM8={int(data.get('TIM8', 0))}
    ➤ Omegas: {data.get('Enc_Wheel_Omega1', 0):.2f}, {data.get('Enc_Wheel_Omega2', 0):.2f}, {data.get('Enc_Wheel_Omega3', 0):.2f}, {data.get('Enc_Wheel_Omega4', 0):.2f}
    ➤ Real Speeds: φ_dot={data.get('Inertial_ang_vel_calc', 0):.2f}, x_dot={data.get('Inertial_x_vel_calc', 0):.2f}, y_dot={data.get('Inertial_y_vel_calc', 0):.2f}
    ➤ Odom: φ={data.get('ODOM_phi', 0):.2f}, x={data.get('ODOM_x_pos', 0):.2f}, y={data.get('ODOM_y_pos', 0):.2f}
    ➤ Errors: dx={data.get('ODOM_Err_x', 0):.2f}, dy={data.get('ODOM_Err_y', 0):.2f}, dφ={data.get('ODOM_Err_phi', 0):.2f}
    ➤ U_errors: u_err1={data.get('U_Err_1', 0):.2f}, u_err2={data.get('U_Err_2', 0):.2f}, u_err3={data.get('U_Err_3', 0):.2f}, u_err4={data.get('U_Err_4', 0):.2f}
    ➤ Ctrl Speeds: x_dot={data.get('Ctrl_Inertial_x_dot', 0):.2f}, y_dot={data.get('Ctrl_Inertial_y_dot', 0):.2f}, φ_dot={data.get('Ctrl_Inertial_phi_dot', 0):.2f}
    ➤ Ctrl Wheel u: u1={data.get('Ctrl_necc_u1', 0):.2f}, u2={data.get('Ctrl_necc_u2', 0):.2f}, u3={data.get('Ctrl_necc_u3', 0):.2f}, u4={data.get('Ctrl_necc_u4', 0):.2f}
    ➤ PWM: {data.get('Ctrl_duty_u1', 0):.0f}, {data.get('Ctrl_duty_u2', 0):.0f}, {data.get('Ctrl_duty_u3', 0):.0f}, {data.get('Ctrl_duty_u4', 0):.0f}
    ➤ ts: current={data.get('ts_current', 0):.0f}, previous={data.get('ts_previous', 0):.0f}, delta={data.get('ts_delta', 0):.0f}
                    """
                    self.state_pub.publish(String(data=output))

                    # Prepare data groups
                    self.pose_data.data = [ data.get('x_desired', 0), data.get('y_desired', 0), data.get('phi_desired', 0), data.get('d', 0), data.get('r', 0)]
                    self.imu_data.data = [ data.get('roll', 0), data.get('pitch', 0), data.get('yaw', 0) ]
                    self.encoders_data.data = [ int(data.get('TIM1', 0)), int(data.get('TIM2', 0)), int(data.get('TIM4', 0)), int(data.get('TIM8', 0)) ]
                    self.omega_data.data = [ data.get('Enc_Wheel_Omega1', 0), data.get('Enc_Wheel_Omega2', 0), data.get('Enc_Wheel_Omega3', 0), data.get('Enc_Wheel_Omega4', 0) ]
                    self.odom_data.data = [ data.get('ODOM_phi', 0), data.get('ODOM_x_pos', 0), data.get('ODOM_y_pos', 0) ]
                    self.errors_data.data = [ data.get('ODOM_Err_x', 0), data.get('ODOM_Err_y', 0), data.get('ODOM_Err_phi', 0) ]
                    self.u_errors_data.data = [ data.get('U_Err_1', 0), data.get('U_Err_2', 0), data.get('U_Err_3', 0), data.get('U_Err_4', 0) ]
                    self.ctrl_speeds_data.data = [ data.get('Ctrl_Inertial_x_dot', 0), data.get('Ctrl_Inertial_y_dot', 0), data.get('Ctrl_Inertial_phi_dot', 0) ]
                    self.ctrl_u_data.data = [ data.get('Ctrl_necc_u1', 0), data.get('Ctrl_necc_u2', 0), data.get('Ctrl_necc_u3', 0), data.get('Ctrl_necc_u4', 0) ]
                    self.pwm_data.data = [ int(data.get('Ctrl_duty_u1', 0)), int(data.get('Ctrl_duty_u2', 0)), int(data.get('Ctrl_duty_u3', 0)), int(data.get('Ctrl_duty_u4', 0)) ]
                    self.ts_data.data = [ int(data.get('ts_current', 0)), int(data.get('ts_previous', 0)), int(data.get('ts_delta', 0)) ]
                    # PID gains
                    self.x_pid_data.data   = [ data.get('xKp', 0), data.get('xKi', 0), data.get('xKd', 0) ]
                    self.y_pid_data.data   = [ data.get('yKp', 0), data.get('yKi', 0), data.get('yKd', 0) ]
                    self.phi_pid_data.data = [ data.get('phiKp', 0), data.get('phiKi', 0), data.get('phiKd', 0) ]
                    self.u0_pid_data.data  = [ data.get('u0Kp', 0), data.get('u0Ki', 0), data.get('u0Kd', 0) ]
                    self.u1_pid_data.data  = [ data.get('u1Kp', 0), data.get('u1Ki', 0), data.get('u1Kd', 0) ]
                    self.u2_pid_data.data  = [ data.get('u2Kp', 0), data.get('u2Ki', 0), data.get('u2Kd', 0) ]
                    self.u3_pid_data.data  = [ data.get('u3Kp', 0), data.get('u3Ki', 0), data.get('u3Kd', 0) ]

                    # Publish to topics
                    self.pose_pub.publish(self.pose_data)
                    self.imu_pub.publish(self.imu_data)
                    self.encoders_pub.publish(self.encoders_data)
                    self.omega_pub.publish(self.omega_data)
                    self.odom_pub.publish(self.odom_data)
                    self.errors_pub.publish(self.errors_data)
                    self.u_errors_pub.publish(self.u_errors_data)
                    self.ctrl_speeds_pub.publish(self.ctrl_speeds_data)
                    self.ctrl_u_pub.publish(self.ctrl_u_data)
                    self.pwm_pub.publish(self.pwm_data)
                    self.ts_pub.publish(self.ts_data)
                    self.x_pid_pub.publish(self.x_pid_data)
                    self.y_pid_pub.publish(self.y_pid_data)
                    self.phi_pid_pub.publish(self.phi_pid_data)
                    self.u0_pid_pub.publish(self.u0_pid_data)
                    self.u1_pid_pub.publish(self.u1_pid_data)
                    self.u2_pid_pub.publish(self.u2_pid_data)
                    self.u3_pid_pub.publish(self.u3_pid_data)


                except Exception as e:
                    self.get_logger().error(f"❌ UART RX Error: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = SerialCommNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
