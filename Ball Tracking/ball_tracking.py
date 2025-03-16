import numpy as np
import cv2 as cv

# Open video
cap = cv.VideoCapture(r"D:\CMU\Assignments\IRL_Project\Ball Tracking\pinball_yt.mp4")

if not cap.isOpened():
    print("Could not open file")
    exit()
    
cv.namedWindow("Original", cv.WINDOW_NORMAL)
cv.namedWindow("MOG", cv.WINDOW_NORMAL)
cv.namedWindow("Contour", cv.WINDOW_NORMAL)

cv.resizeWindow("Original", 1200, 800)
cv.resizeWindow("MOG", 1200, 800)
cv.resizeWindow("Contour", 1200, 800)

# Background subtraction using MOG
fgbg = cv.createBackgroundSubtractorMOG2()

while(1):
    ret, frame = cap.read()
    if ret:
        fgmask = fgbg.apply(frame)
        
        # Original frame
        cv.imshow('Original', frame)
        # After background subraction
        cv.imshow('MOG', fgmask)
        
        contours, hierarchy = cv.findContours(fgmask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        filtered_contours = []
        for c in  contours:
            x, y, w, h = cv.boundingRect(c)
            aspect_ratio = w / float(h)
            area  = cv.contourArea(c)
            
            if 600 < area < 3000 and 0.7 < aspect_ratio < 1.3:
                filtered_contours.append(c)
        
        c_frame = frame.copy()
        mask = np.zeros_like(frame, dtype = np.uint8)
        cv.drawContours(mask, filtered_contours, -1, (0, 0, 255), 2)
        ret, mask = cv.threshold(mask, 1, 255, cv.THRESH_BINARY)
        
        # After contour detection
        # cv.imshow("Contour", c_frame)
        cv.imshow("Contour", mask)
        
        k = cv.waitKey(30) & 0xff
        if k == 27:
            break
    else:
        print("Could not read frame")
        break
    
cap.release()
cv.destroyAllWindows()