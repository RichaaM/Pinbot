import cv2
import numpy as np
from collections import deque
import yaml
import matplotlib.pyplot as plt

def detect_led_state(cap, roi, buffer_size=20, flash_variation_threshold=50):
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    brightness_buffer = deque(maxlen=buffer_size) 
    
    # while True:
    #     _, frame = cap.read()
    #     if np.mean(frame) < 50:
    #         continue
    #     roi = detect_roi(frame)
    #     break

    while True:
        _, frame = cap.read()

        x, y, w, h = roi
        led_region = frame[y:y+h, x:x+w]
        gray_led_region = cv2.cvtColor(led_region, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray_led_region)
        brightness_buffer.append(avg_brightness)

        if len(brightness_buffer) == buffer_size:
            max_brightness = max(brightness_buffer)
            min_brightness = min(brightness_buffer)
            brightness_variation = max_brightness - min_brightness

            if brightness_variation > flash_variation_threshold:
                game_over = True
            else:
                game_over = False
        else:
            game_over = False

       
        cv2.putText(frame, f"Game Over: {game_over}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  
        cv2.imshow("Game over detection", frame)

        with open("is_game_over.txt", "w") as file:
            file.write(str(game_over))
            file.close()

        if cv2.waitKey(1) & 0xFF == ord('q'):  ###  PRESS Q TO QUIT
            break

    cap.release()
    cv2.destroyAllWindows()

# def detect_roi(frame):
#     gray_locs = np.where((np.abs(frame[:,:,0] - frame[:,:,1]) + np.abs(frame[:,:,0] - frame[:,:,2]) + np.abs(frame[:,:,1] - frame[:,:,2]) < 50) & (np.min(frame, axis=2) > 100) & ())
#     frame[gray_locs[0], gray_locs[1], 0] = 255
#     frame[gray_locs[0], gray_locs[1], 1:] = 0
#     plt.imshow(frame)
#     plt.show()

if __name__ == "__main__":
    with open("config.yml", 'r') as stream:
        configs = yaml.safe_load(stream)
    roi = configs["start_camera"]["roi"]  #x, y, width, height
    start_camera = cv2.VideoCapture(configs["start_camera"]["index"])
    detect_led_state(start_camera, roi)
