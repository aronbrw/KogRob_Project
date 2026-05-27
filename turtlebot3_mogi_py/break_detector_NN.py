import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage, Image
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
import cv2
import numpy as np
import threading
import os
import joblib
from ament_index_python.packages import get_package_share_directory


class ImageSubscriber(Node):
    def __init__(self):
        super().__init__('image_subscriber')
        
        '''
        # Create a subscriber with a queue size of 1 to only keep the last frame
        self.subscription = self.create_subscription(
            Image,
            'image_raw',  # Replace with your topic name
            self.image_callback,
            1  # Queue size of 1
        )
        '''

        self.subscription = self.create_subscription(
            CompressedImage,
            'image_raw/compressed',  # Replace with your topic name
            self.image_callback,
            1  # Queue size of 1
        )

        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        
       
        self.break_publisher = self.create_publisher(
        Bool,
        '/break_detected',
        10
        )
        pkg_turtlebot3_mogi_py = get_package_share_directory('turtlebot3_mogi_py')
        model_path = pkg_turtlebot3_mogi_py + "/network_model/break_detector_model.joblib"

        print("Loading model:", model_path)
        self.break_model = joblib.load(model_path)
        
        # Initialize CvBridge
        self.bridge = CvBridge()
        
        # Variable to store the latest frame
        self.latest_frame = None
        self.frame_lock = threading.Lock()  # Lock to ensure thread safety
        
        # Flag to control the display loop
        self.running = True

        # Start a separate thread for spinning (to ensure image_callback keeps receiving new frames)
        self.spin_thread = threading.Thread(target=self.spin_thread_func)
        self.spin_thread.start()

    def spin_thread_func(self):
        """Separate thread function for rclpy spinning."""
        while rclpy.ok() and self.running:
            rclpy.spin_once(self, timeout_sec=0.05)

    def image_callback(self, msg):
        """Callback function to receive and store the latest frame."""
        # Convert ROS Image message to OpenCV format and store it
        with self.frame_lock:
            #self.latest_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            self.latest_frame = self.bridge.compressed_imgmsg_to_cv2(msg, desired_encoding="bgr8")

    def display_image(self):

        # Create a single OpenCV window
        cv2.namedWindow("frame", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("frame", 800,600)

        while rclpy.ok():
            # Check if there is a new frame available
            if self.latest_frame is not None:

                # Process the current image
                mask, contour, crosshair,break_detect = self.process_image(self.latest_frame)

                # Add processed images as small images on top of main image
                result = self.add_small_pictures(self.latest_frame, [mask, contour, break_detect])

                # Show the latest frame
                cv2.imshow("frame", result)
                self.latest_frame = None  # Clear the frame after displaying

            # Check for quit key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop_robot()
                self.running = False
                break

        # Close OpenCV window after quitting
        cv2.destroyAllWindows()
        self.running = False

    def process_image(self, img):

        msg = Twist()
        msg.linear.x = 0.0
        msg.linear.y = 0.0
        msg.linear.z = 0.0
        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = 0.0

        rows,cols = img.shape[:2]

        # 1. Convert to HLS color space to extract lightness channel
        H,L,S = self.convert2hls(img)

        # 2. Invert lightness channel if we follow a dark line on a light background
        L = 255 - L # Invert lightness channel

        # 3. apply a polygon mask to filter out simulation's bright sky
        L_masked, mask = self.apply_polygon_mask(L)

        # 4. For light line on dark background in simulation:
        lightnessMask = self.threshold_binary(L_masked, (120, 255))

        ############ Sajat kod
        break_detected, upper_pixels, middle_pixels, lower_pixels = self.detect_break(lightnessMask)

        break_msg = Bool()
        break_msg.data = bool(break_detected)
        self.break_publisher.publish(break_msg)

        self.get_logger().info(f"NN szerint szakadas van:{break_detected}")
        #######################



        # For light line on dark background in real life environment:
        #lightnessMask = self.threshold_binary(L_masked, (180, 255))
        stackedMask = np.dstack((lightnessMask, lightnessMask, lightnessMask))
        contourMask = stackedMask.copy()
        crosshairMask = stackedMask.copy()
        breakdetectMask = stackedMask.copy()

        ###breakdetactMask-hoz:
        rows, cols = lightnessMask.shape[:2]

        center_width = int(cols * 0.5)
        x1 = int(cols/2 - center_width/2)
        x2 = int(cols/2 + center_width/2)

        y_up1 = int(rows * 0.25)
        y_up2 = int(rows * 0.45)
        y_mid1 = int(rows * 0.45)
        y_mid2 = int(rows * 0.65)
        y_low1 = int(rows * 0.65)
        y_low2 = int(rows * 0.90)
        cv2.rectangle(breakdetectMask, (x1, y_up1), (x2, y_up2), (255, 0, 0), 2)
        cv2.rectangle(breakdetectMask, (x1, y_mid1), (x2, y_mid2), (0, 255, 255), 2)
        cv2.rectangle(breakdetectMask, (x1, y_low1), (x2, y_low2), (0, 255, 0), 2)
        ####


        # 5. return value of findContours depends on OpenCV version
        (contours,hierarchy) = cv2.findContours(lightnessMask.copy(), 1, cv2.CHAIN_APPROX_NONE)

        # overlay mask on lightness image to show masked area on the small picture
        lightnessMask = cv2.addWeighted(mask,0.2,lightnessMask,0.8,0)

        # 6. Find the biggest contour (if detected) and calculate its centroid
        if len(contours) > 0:
            
            biggest_contour = max(contours, key=cv2.contourArea)
            M = cv2.moments(biggest_contour)

            # Make sure that "m00" won't cause ZeroDivisionError: float division by zero
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = 0, 0

            # Show contour and centroid
            cv2.drawContours(contourMask, biggest_contour, -1, (0,255,0), 10)
            cv2.circle(contourMask, (cx, cy), 20, (0, 0, 255), -1)

            # Show crosshair and difference from middle point
            cv2.line(crosshairMask,(cx,0),(cx,rows),(0,0,255),10)
            cv2.line(crosshairMask,(0,cy),(cols,cy),(0,0,255),10)
            cv2.line(crosshairMask,(int(cols/2),0),(int(cols/2),rows),(255,0,0),10)

            # Chase the ball
            #print(abs(cols - cx), cx, cols)
            if abs(cols/2 - cx) > 20:
                msg.linear.x = 0.05
                if cols/2 > cx:
                    msg.angular.z = 0.15
                else:
                    msg.angular.z = -0.15

            else:
                msg.linear.x = 0.1
                msg.angular.z = 0.0

        else:
            msg.linear.x = 0.0
            msg.angular.z = 0.0

        # Publish cmd_vel
        self.publisher.publish(msg)

    
        # Return processed frames
        return L_masked, contourMask, crosshairMask, breakdetectMask


    # AZ általam készített szakadás detekcio
    def detect_break(self, binary_img):
        rows, cols = binary_img.shape[:2]

        center_width = int(cols * 0.5)
        x1 = int(cols/2 - center_width/2)
        x2 = int(cols/2 + center_width/2)

        roi = binary_img[:, x1:x2]

        upper = roi[int(rows*0.25):int(rows*0.45), :]
        middle = roi[int(rows*0.45):int(rows*0.65), :]
        lower = roi[int(rows*0.65):int(rows*0.90), :]

        upper_pixels = cv2.countNonZero(upper)
        middle_pixels = cv2.countNonZero(middle)
        lower_pixels = cv2.countNonZero(lower)

        #upper_pixels = 101
        #middle_pixels = 19
        #lower_pixels = 124

        X = np.array([[upper_pixels, middle_pixels, lower_pixels]])
        prediction = self.break_model.predict(X)[0]

        break_detected = bool(prediction)

        return break_detected, upper_pixels, middle_pixels, lower_pixels



    # Convert to RGB channels
    def convert2rgb(self, img):
        R = img[:, :, 2]
        G = img[:, :, 1]
        B = img[:, :, 0]

        return R, G, B

    # convert to HLS color space
    def convert2hls(self, img):
        hls = cv2.cvtColor(img, cv2.COLOR_RGB2HLS)
        H = hls[:, :, 0]
        L = hls[:, :, 1]
        S = hls[:, :, 2]

        return H, L, S
    
    # apply a trapezoid polygon mask, size is hardcoded for 640x480px
    def apply_polygon_mask(self, img):
        mask = np.zeros_like(img)
        ignore_mask_color = 255
        imshape = img.shape
        vertices = np.array([[(0,imshape[0]),(80, 100), (560, 100), (imshape[1],imshape[0])]], dtype=np.int32)
        cv2.fillPoly(mask, vertices, ignore_mask_color)
        masked_image = cv2.bitwise_and(img, mask)

        return masked_image, mask

    # Apply threshold and result a binary image
    def threshold_binary(self, img, thresh=(200, 255)):
        binary = np.zeros_like(img)
        binary[(img >= thresh[0]) & (img <= thresh[1])] = 1

        return binary*255

    # Add small images to the top row of the main image
    def add_small_pictures(self, img, small_images, size=(160, 120)):

        x_base_offset = 40
        y_base_offset = 10

        x_offset = x_base_offset
        y_offset = y_base_offset

        for small in small_images:
            small = cv2.resize(small, size)
            if len(small.shape) == 2:
                small = np.dstack((small, small, small))

            img[y_offset: y_offset + size[1], x_offset: x_offset + size[0]] = small

            x_offset += size[0] + x_base_offset

        return img

    def stop_robot(self):
        msg = Twist()
        msg.linear.x = 0.0
        msg.linear.y = 0.0
        msg.linear.z = 0.0
        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = 0.0

        self.publisher.publish(msg)

    def stop(self):
        """Stop the node and the spin thread."""
        self.running = False
        self.spin_thread.join()

def main(args=None):

    print("OpenCV version: %s" % cv2.__version__)

    rclpy.init(args=args)
    node = ImageSubscriber()
    
    try:
        node.display_image()  # Run the display loop
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()  # Ensure the spin thread and node stop properly
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()