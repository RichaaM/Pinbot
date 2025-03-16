import numpy as np
import cv2 as cv

# Open video
cap = cv.VideoCapture(r"D:\CMU\Assignments\IRL_Project\Ball Tracking\pinball.mp4")
template = cv.imread(r"D:\CMU\Assignments\IRL_Project\Ball Tracking\temp.png", cv.IMREAD_GRAYSCALE)

w, h = template.shape[::-1]

if not cap.isOpened():
    print("Could not open file")
    exit()
    
cv.namedWindow("Original", cv.WINDOW_NORMAL)

cv.resizeWindow("Original", 800, 1200)

threshold = 0.8
min_scale = 0.5  # Minimum scale factor
max_scale = 1.5  # Maximum scale factor
scale_step = 0.05  # Step size for scaling

while(1):
    ret, frame = cap.read()
    if ret:        
        frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        
        res = cv.matchTemplate(frame_gray, template, cv.TM_SQDIFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
        
        top_left = min_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)

        # if max_val >= threshold:
        #     top_left = max_loc
        #     bottom_right = (top_left[0] + w, top_left[1] + h)
        cv.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
        
        cv.imshow('Original', frame)
        
        # result_found = False  # Flag to check if any match was found
        
        # # Loop over multiple scales
        # for scale in np.arange(min_scale, max_scale, scale_step):
        #     # Resize the template according to the current scale
        #     resized_template = cv.resize(template, (int(w * scale), int(h * scale)))
            
        #     # Perform template matching
        #     res = cv.matchTemplate(frame_gray, resized_template, cv.TM_SQDIFF_NORMED)
            
        #     # Get the minimum and maximum values of the result
        #     min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
            
        #     # If the match is above the threshold, draw a rectangle
        #     if max_val >= threshold:
        #         top_left = min_loc
        #         bottom_right = (top_left[0] + resized_template.shape[1], top_left[1] + resized_template.shape[0])
                
        #         # Draw rectangle on the frame where the match is found
        #         cv.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
                
        #         result_found = True
        #         break  # Exit the loop if a match is found for this scale

        # # Show the result only if a match is found
        # if result_found:
        #     cv.imshow('Original', frame)
        
        k = cv.waitKey(30) & 0xff
        if k == 27:
            break
    else:
        print("Could not read frame")
        break
    
cap.release()
cv.destroyAllWindows()