import cv2
import numpy as np
import matplotlib.pyplot as plt
from kalman_filter import KalmanFilter
import time

# Function to get locations of all lights -> To be used as a calibration step before each run
def get_light_locations():
    cap = cv2.VideoCapture("D:\CMU\Assignments\IRL_Project\Pinbot\Ball Tracking\lights.mp4")
        
    if not cap.isOpened():
        print("Error: Could not open video in get_light_locations")
        return {}
    
    light_locs = set()
    
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply Background Subtraction
        fg_mask = bg_subtractor.apply(gray)

        # # Find contours in the processed mask
        # contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # for contour in contours:  
        #     (x, y), radius = cv2.minEnclosingCircle(contour)
        #     light_locs.add((int(x), int(y), int(radius)))
        
        blurred = cv2.GaussianBlur(fg_mask, (9, 9), 2)    # Remove noise
        
        circles = cv2.HoughCircles(
            blurred, 
            cv2.HOUGH_GRADIENT, 
            dp=1.2,               # Inverse ratio of resolution
            minDist=20,           # Minimum distance between detected centers
            param1=40,            # Upper threshold for Canny edge detector
            param2=25,            # Threshold for center detection
            minRadius=10,          # Minimum circle radius
            maxRadius=30          # Maximum circle radius
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                if x < 1700 and x > 50 and y > 150 and y < 1000:    # Only consider play area
                    light_locs.add((x, y, r))

    print("Retrieved light locations")
    return light_locs

# To check proximity to lights instead of checking for exact match
def is_near_light(x, y, rad, light_locs, frame, delta=2):
    for lx, ly, lr in light_locs:
        # cv2.circle(frame, (lx, ly), lr, (0, 255, 255), 1)
        # cv2.circle(frame, (x, y), rad, (0, 0, 255), 5)
        
        distance = np.sqrt((x - lx)**2 + (y - ly)**2)
        if distance < delta:
            return True
    return False

def track_pinball():
    cap = cv2.VideoCapture("D:\CMU\Assignments\IRL_Project\Pinbot\Ball Tracking\pinball_yt.mp4")
    
    if not cap.isOpened():
        print("Error: Could not open video.")
        return []
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # if output_path:
    #     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    #     out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    ball_positions = []
    last_ball_position = None
    
    # Initialize Background Subtractor
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)
    
    kf = KalmanFilter(2, 1, 10)
    ii = 0
    
    light_locs = get_light_locations()
    
    # Timer
    start = time.perf_counter()
    end = time.perf_counter()
    pause = False
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # cv2.circle(frame, (50, 150), 10, (0, 0, 255), 5)
        # cv2.circle(frame, (50, 1000), 10, (0, 255, 0), 5)
        # cv2.circle(frame, (1600, 1000), 10, (0, 255, 255), 5)
        # cv2.circle(frame, (1600, 150), 10, (255, 0, 0), 5)
        
        end = time.perf_counter()
        if end - start > 7:
            start = time.time()
            pause = False
            print("TIMER STOPPED")
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply Background Subtraction
        fg_mask = bg_subtractor.apply(gray)

        # Filter Out Bright Lights
       # _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)  

        # Apply Morphological Operations to Reduce Noise
        kernel = np.ones((5, 5), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)  
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)

        # Find contours in the processed foreground mask
        # contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        blurred = cv2.GaussianBlur(fg_mask, (9, 9), 2)    # Remove noise
        
        circles = cv2.HoughCircles(
            blurred, 
            cv2.HOUGH_GRADIENT, 
            dp=1.2,               # Inverse ratio of resolution
            minDist=10,           # Minimum distance between detected centers
            param1=40,            # Upper threshold for Canny edge detector
            param2=25,            # Threshold for center detection
            minRadius=5,          # Minimum circle radius
            maxRadius=30          # Maximum circle radius
        )
        
        possible_balls = []
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                if not is_near_light(x, y, r, light_locs, frame) and x < 1700 and x > 50 and y > 150 and y < 1000:    # Only consider play area
                    possible_balls.append((x, y, r))
                    # cv2.circle(frame, (x, y), r + 10, (0, 0, 255), 5)

        best_ball = None
        min_distance = float('inf')

        if possible_balls:
            if kf.initialized:
                kx, ky, kw, kh = kf.predict()
            for x, y, r in possible_balls:
                if kf.initialized:
                    distance = np.sqrt((x - kx)**2 + (y - ky)**2)   # Find the contour closest to Kalman prediction
                    if distance < min_distance:
                        min_distance = distance
                        best_ball = (x, y, r)
                else:
                    best_ball = (x, y, r)
        if not pause:
            if best_ball:
                x, y, r = best_ball
                cv2.circle(frame, (x, y), r, (0, 0, 255), 5)
                
                # x > 1650 -> Drain area
                if x > 1650:
                    print("TIMER STARTED")
                    start = time.perf_counter()
                    pause = True
                    continue
                
                # Only consider play area
                if x < 1700 and x > 50 and y > 150 and y < 1000:
                    ball_positions.append((x, y))
                    if not kf.initialized:
                        kf.__init__(2, 1, 10)
                        kf.initialize((x-r, y-r, 2*r, 2*r))
                        
                    kx, ky, kw, kh = kf.predict()
                    kf.update((x-r, y-r, 2*r, 2*r))
                    # cv2.rectangle(frame, (kx, ky),(kx+kw, ky+kh), (255, 0, 0), 3)  
                else:
                    ball_positions.append(None)
            else:
                if kf.initialized:
                    kx, ky, kw, kh = kf.predict()
                    
                    # Only consider play area
                    if x < 1700 and x > 50 and y > 150 and y < 1000:
                        # cv2.rectangle(frame, (kx, ky),(kx+kw, ky+kh), (0, 0, 255), 3)
                        ball_positions.append((kx, ky))
                    else:
                        ball_positions.append(None)
                else:
                    ball_positions.append(None)

            # Draw Ball Trajectory
            for i in range(1, len(ball_positions)):
                if ball_positions[i-1] is not None and ball_positions[i] is not None:
                    cv2.line(frame, ball_positions[i-1], ball_positions[i], (255, 0, 0), 2)            

        cv2.imshow('Filtered Grayscale', fg_mask)  # Left window (Filtered grayscale)
        cv2.imshow('Pinball Tracking', frame)  # Right window (Final tracking output)
        cv2.imwrite(f'frames2/{ii}.jpg', frame)
        ii+=1
        # if output_path:
        #     out.write(frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    # if output_path:
    #     out.release()
    cv2.destroyAllWindows()
    
    return ball_positions

# Run the script
# video_path = "D:\CMU\Assignments\IRL_Project\Pinbot\Ball Tracking\pinball_yt.mp4"
# output_path = "D:\CMU\Assignments\IRL_Project\Pinbot\Ball Tracking\Output\trial_pinball.mp4"

# positions = track_pinball(video_path, output_path)
# print(f"Tracked {len(positions)} frames")

if __name__ == '__main__':
    track_pinball()
