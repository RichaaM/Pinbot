import cv2
import numpy as np
import matplotlib.pyplot as plt
from kalman_filter import KalmanFilter


def track_pinball(video_path, output_path=None):
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Error: Could not open video.")
        return []
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    ball_positions = []
    last_ball_position = None
    
    # **Initialize Background Subtractor**
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)
    kf = KalmanFilter(2, 1, 10)
    ii = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # **Apply Background Subtraction**
        fg_mask = bg_subtractor.apply(gray)

        # **Filter Out Bright Lights**
       # _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)  

        # **Apply Morphological Operations to Reduce Noise**
        kernel = np.ones((5, 5), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)  
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)

        # **Find contours in the processed foreground mask**
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        possible_balls = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 2000:  
                (x, y), radius = cv2.minEnclosingCircle(contour)
                if 8 < radius < 30:  
                    possible_balls.append((int(x), int(y), int(radius)))

        best_ball = None
        min_distance = float('inf')

        if possible_balls:
            

            for x, y, r in possible_balls:
                cv2.circle(frame, (x, y), r, (0, 255, 0), 2)  
                cv2.circle(frame, (x, y), 2, (0, 0, 255), 3)  
                if last_ball_position:
                    distance = np.sqrt((x - last_ball_position[0])**2 + (y - last_ball_position[1])**2)
                    if distance < min_distance:
                        min_distance = distance
                        print(min_distance)
                        best_ball = (x, y, r)
                else:
                    best_ball = (x, y, r)

        if best_ball:
            
            x, y, r = best_ball
            cv2.circle(frame, (x, y), r, (0, 255, 0), 2)  
            cv2.circle(frame, (x, y), 2, (0, 0, 255), 3)  
            
            ball_positions.append((x, y))
            last_ball_position = (x, y)
            if not kf.initialized:
                kf.__init__(2, 1, 10)
                kf.initialize((x-r, y-r, 2*r, 2*r))

            kx, ky, kw, kh = kf.predict()
            kf.update((x-r, y-r, 2*r, 2*r))
            cv2.rectangle(frame, (kx, ky),(kx+kw, ky+kh), (255, 0, 0), 3)  
        else:
            if kf.initialized:

                kx, ky, kw, kh = kf.predict()
                cv2.rectangle(frame, (kx, ky),(kx+kw, ky+kh), (0, 0, 255), 3)  
            ball_positions.append(None)

        # **Draw Ball Trajectory**
        for i in range(1, len(ball_positions)):
            if ball_positions[i-1] is not None and ball_positions[i] is not None:
                cv2.line(frame, ball_positions[i-1], ball_positions[i], (255, 0, 0), 2)

        # **Show Two Separate Windows**
        #cv2.imshow('Filtered Grayscale', fg_mask)  # Left window (Filtered grayscale)
        #cv2.imshow('Pinball Tracking', frame)  # Right window (Final tracking output)
        cv2.imwrite(f'frames2/{ii}.jpg', frame)
        ii+=1
        if output_path:
            out.write(frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    if output_path:
        out.release()
    cv2.destroyAllWindows()
    
    return ball_positions

# Run the script
video_path = "D:\CMU\Assignments\IRL_Project\Pinbot\Ball Tracking\pinball_yt.mp4"
output_path = "D:\CMU\Assignments\IRL_Project\Pinbot\Ball Tracking\Output\trial_pinball.mp4"

positions = track_pinball(video_path, output_path)
print(f"Tracked {len(positions)} frames")
