
"""
record.py
---------------

Main Function for recording a video sequence into cad (color-aligned-to-depth) 
images and depth images

This code is compatible with legacy camera models supported on librealsense SDK v1
and use 3rd party python wrapper https://github.com/toinsson/pyrealsense

For the newer D series cameras, please use record2.py


"""

# record for 30s after a 5s count down
# or exit the recording earlier by pressing q

RECORD_LENGTH = 30

import png
import json
import logging
logging.basicConfig(level=logging.INFO)
import numpy as np
import cv2
import pyrealsense2 as rs
import time
import os
import sys

def make_directories(folder):
    if not os.path.exists(folder+"JPEGImages/"):
        os.makedirs(folder+"JPEGImages/")
    if not os.path.exists(folder+"depth/"):
        os.makedirs(folder+"depth/")

def print_usage():
    
    print("Usage: record.py <foldername>")
    print("foldername: path where the recorded data should be stored at")
    print("e.g., record.py LINEMOD/mug")
    

if __name__ == "__main__":
    try:
        folder = sys.argv[1]+"/"
    except:
        print_usage()
        exit()

    make_directories(folder)
    pipeline = rs.pipeline()
    config = rs.config()

    #config frame
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    #Start record
    profile = pipeline.start(config)

    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()

    intr = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
    

    camera_parameters = {'fx': intr.fx, 'fy': intr.fy,
                        'ppx': intr.ppx, 'ppy': intr.ppy,
                        'height': intr.height, 'width': intr.width,
                        'depth_scale': depth_scale}
    
    with open(folder+'intrinsics.json', 'w') as fp:
        json.dump(camera_parameters, fp)

        FileName = 0
        T_start = time.time()

    try:
        while True:
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            # Convert images to numpy arrays
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())

            # Visualize countdown
            if time.time() - T_start > 5:
                filecad = folder + "JPEGImages/%s.jpg" % FileName
                filedepth = folder + "depth/%s.png" % FileName
                cv2.imwrite(filecad, color_image)

                # Save depth image
                with open(filedepth, 'wb') as f:
                    writer = png.Writer(width=depth_image.shape[1], height=depth_image.shape[0], bitdepth=16, greyscale=True)
                    depth_list = depth_image.tolist()
                    writer.write(f, depth_list)

                FileName += 1

            if time.time() - T_start > RECORD_LENGTH + 5:
                break

            if time.time() - T_start < 5:
                cv2.putText(color_image, str(5 - int(time.time() - T_start)), (240, 320), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 2, cv2.LINE_AA)
            if time.time() - T_start > RECORD_LENGTH:
                cv2.putText(color_image, str(RECORD_LENGTH + 5 - int(time.time() - T_start)), (240, 320), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 2, cv2.LINE_AA)

            # Display the resulting frame
            cv2.imshow('COLOR FRAME', color_image)

            # Press 'q' to stop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Stop streaming
        pipeline.stop()

    # Release everything if job is finished
    cv2.destroyAllWindows()