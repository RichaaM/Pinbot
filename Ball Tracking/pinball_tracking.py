import cv2
import numpy as np

def initialize_kalman(fps):
    kf = cv2.KalmanFilter(4, 2)  # 4 states (x, y, vx, vy), 2 measurements (x, y)

    dt = 1/fps
    
    # State transition matrix (A)
    kf.transitionMatrix = np.array([[1, 0, dt, 0],  # x' = x + vx
                                    [0, 1, 0, dt],  # y' = y + vy
                                    [0, 0, 1, 0],  # vx' = vx
                                    [0, 0, 0, 1]], # vy' = vy
                                    dtype=np.float32)

    # Measurement matrix (H)
    kf.measurementMatrix = np.array([[1, 0, 0, 0],  # Measuring x
                                     [0, 1, 0, 0]], # Measuring y
                                     dtype=np.float32)

    # Process noise covariance (Q)
    q_var = 0.03
    kf.processNoiseCov = np.array([
        [q_var*dt**4/4, 0, q_var*dt**3/2, 0],
        [0, q_var*dt**4/4, 0, q_var*dt**3/2],
        [q_var*dt**3/2, 0, q_var*dt**2, 0],
        [0, q_var*dt**3/2, 0, q_var*dt**2]
    ], dtype=np.float32)

    # Measurement noise covariance (R)
    kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.0  

    # Error covariance matrix (P)
    kf.errorCovPost = np.eye(4, dtype=np.float32)

    return kf

# Function to get locations of all lights -> To be used as a calibration step before each run
def get_light_locations():
    cap = cv2.VideoCapture("D:\CMU\Assignments\IRL_Project\Ball Tracking\lights.mp4")
    
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

        # Find contours in the processed mask
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:  
            (x, y), radius = cv2.minEnclosingCircle(contour)
            light_locs.add((int(x), int(y), int(radius)))

    print("Retrieved light locations")
    return light_locs
    
# def track_pinball(video_path, output_path=None):
def track_pinball():
    cap = cv2.VideoCapture("D:\CMU\Assignments\IRL_Project\Ball Tracking\pinball_yt.mp4")

    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # if output_path:
    #     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    #     out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    ball_positions = []
    last_ball_position = None

    # Background subtractor
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

    # Define HSV color range for the ball -> Need to tune
    lower_color = np.array([6, 0, 70])
    upper_color = np.array([130, 255, 255])
    
    # KF initialization 
    kf = initialize_kalman(fps)
    # Get pixel coordinates of starting location
    start_x = 5000
    start_y = 480  
    kf.statePre = np.array([[start_x], [start_y], [0], [0]], dtype=np.float32)
    kf.statePost = kf.statePre.copy()
    
    light_locs = get_light_locations()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  # Convert to HSV for color filtering

        # Apply Background Subtraction
        fg_mask = bg_subtractor.apply(gray)

        # Apply Color Filtering
        color_mask = cv2.inRange(hsv, lower_color, upper_color)

        # Combine Background and Color Mask
        # filtered_mask = cv2.bitwise_and(fg_mask, color_mask)
        filtered_mask = fg_mask

        # Apply Morphological Operations to Reduce Noise
        kernel = np.ones((5, 5), np.uint8)
        filtered_mask = cv2.morphologyEx(filtered_mask, cv2.MORPH_OPEN, kernel)  
        filtered_mask = cv2.morphologyEx(filtered_mask, cv2.MORPH_CLOSE, kernel)

        # Find contours in the processed mask
        contours, _ = cv2.findContours(filtered_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        possible_balls = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 2000:  
                (x, y), radius = cv2.minEnclosingCircle(contour)
                if (int(x), int(y), int(radius)) not in light_locs and 8 < radius < 30:  
                    possible_balls.append((int(x), int(y), int(radius)))

        best_ball = None
        min_distance = float('inf')

        if possible_balls:
            for x, y, r in possible_balls:
                if last_ball_position:
                    distance = np.sqrt((x - last_ball_position[0])**2 + (y - last_ball_position[1])**2)
                    if distance < min_distance:
                        min_distance = distance
                        best_ball = (x, y, r)
                else:
                    best_ball = (x, y, r)

        # KF prediction
        predicted = kf.predict()
        kf_x, kf_y = int(predicted[0]), int(predicted[1])
        
        if best_ball:
            x, y, r = best_ball
                
            last_ball_position = (x, y)
            
            # KF correction
            measurement = np.array([[np.float32(x)], [np.float32(y)]])
            kf.correct(measurement)
            corrected_state = kf.statePost
            kf_x, kf_y = int(corrected_state[0]), int(corrected_state[1])
        else:
            measurement = None
            last_ball_position = None
        
        # Using current state estimate from the KF
        
        ball_positions.append((kf_x, kf_y))

        # Draw Ball Trajectory
        for i in range(1, len(ball_positions)):
            if ball_positions[i-1] is not None and ball_positions[i] is not None:
                cv2.line(frame, ball_positions[i-1], ball_positions[i], (255, 0, 0), 2)

        cv2.imshow('Filtered Mask', filtered_mask)  # Shows combined mask
        cv2.imshow('Pinball Tracking', frame)  # Shows tracking output

        # if output_path:
        #     out.write(frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    # if output_path:
    #     out.release()
    cv2.destroyAllWindows()

    return ball_positions

if __name__ == '__main__':
    track_pinball()
    