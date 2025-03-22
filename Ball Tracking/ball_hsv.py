import cv2
import numpy as np

def pick_color(image_path):
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            pixel = hsv[y, x]
            print(f"HSV Value at ({x}, {y}): {pixel}")

    img = cv2.imread("D:\CMU\Assignments\IRL_Project\Pinbot\Ball Tracking\img5.png")
    cv2.imshow("Pick a point (click on the ball)", img)
    cv2.setMouseCallback("Pick a point (click on the ball)", mouse_callback)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

pick_color("frame.jpg")
