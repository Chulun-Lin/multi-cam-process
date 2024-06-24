import pyrealsense2 as rs
import numpy as np
import cv2
print("Environment is Ready")

# Creating a Pipeline
pipe = rs.pipeline()                      # Create a pipeline
cfg = rs.config()                         # Create a default configuration
print("Pipeline is created")

# Find RealSense Devices
print("Searching Devices..")
selected_devices = []                     # Store connected device(s)

for d in rs.context().devices:
    selected_devices.append(d)
    print(d.get_info(rs.camera_info.name))
if not selected_devices:
    print("No RealSense device is connected!")

# Find Depth and RGB Sensors
rgb_sensor = depth_sensor = None

for device in selected_devices:                         
    print("Required sensors for device:", device.get_info(rs.camera_info.name))
    for s in device.sensors:                              # Show available sensors in each device
        if s.get_info(rs.camera_info.name) == 'RGB Camera':
            print(" - RGB sensor found")
            rgb_sensor = s                                # Set RGB sensor
        if s.get_info(rs.camera_info.name) == 'Stereo Module':
            depth_sensor = s                              # Set Depth sensor
            print(" - Depth sensor found")

# Displaying Depth and Color Frames
colorizer = rs.colorizer()                                # Mapping depth data into RGB color space
profile = pipe.start(cfg)                                 # Configure and start the pipeline

for _ in range(10):                                       # Skip first frames to give syncer and auto-exposure time to adjust
    frameset = pipe.wait_for_frames()

try:
    while True:
        frameset = pipe.wait_for_frames()                     # Read frames from the file, packaged as a frameset
        depth_frame = frameset.get_depth_frame()              # Get depth frame
        color_frame = frameset.get_color_frame()              # Get RGB frame

        if depth_frame:
            depth_image = np.asanyarray(colorizer.colorize(depth_frame).get_data())
        if color_frame:
            rgb_image = np.asanyarray(color_frame.get_data())

        depth_colormap_dim = depth_image.shape
        color_colormap_dim = rgb_image.shape

        # If depth and rgb resolutions are different, resize rgb image to match depth image for display
        if depth_colormap_dim != color_colormap_dim:
            resized_color_image = cv2.resize(rgb_image, dsize=(depth_colormap_dim[1], depth_colormap_dim[0]), interpolation=cv2.INTER_AREA)
            images = np.hstack((resized_color_image, depth_image))
        else:
            images = np.hstack((rgb_image, depth_image))

        # Show images
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', cv2.cvtColor(images, cv2.COLOR_RGB2BGR))
        cv2.waitKey(1)

finally:
    # Stop streaming
    pipe.stop()
