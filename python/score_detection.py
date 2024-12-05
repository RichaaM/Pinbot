from PIL import Image
import matplotlib.pyplot as plt
import numpy as np 
from scipy import ndimage
import pytesseract
import cv2
from collections import deque
from statistics import mode
import yaml 

def read_nums(im):
    im[im < 220] = 0
    im[im > 220] = 255
    white_locs = np.argwhere(im > 0)
    if len(white_locs) < 500:
        return ""
    top_left = (min(white_locs[:, 0]), min(white_locs[:, 1]))
    bot_right = (max(white_locs[:, 0]), max(white_locs[:, 1]))
    pad = 20

    cropped = im[top_left[0] - pad : bot_right[0] + pad, top_left[1] - pad : bot_right[1] + pad]
    dilated = ~ndimage.binary_dilation(cropped.astype(np.bool))
    text = pytesseract.image_to_string(Image.fromarray(dilated), lang="ssd", config='--psm 7 -c  tessedit_char_whitelist="0123456789."')
    print(text)
    text = text.replace(".", "")
    return text.replace(" ", "")

def read_video(cap):
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) 
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) 

    current_score = 0
    score_cache = deque([0]*10)
    prev_score = 0
    frames = []
    if not cap.isOpened():
        print("Error: Could not open video.")
        return
    
    while True:
        ret, frame = cap.read()
        score = read_nums(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        try:
            current_score = int(score)
            score_cache.popleft()
            score_cache.append(current_score)
        except:
            pass

        temp = mode(list(score_cache))
        # if temp < prev_score:
        #     temp = prev_score
        cv2.putText(frame, str(temp), (10,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2)
        cv2.imshow('Camera Feed', frame)
        
        prev_score = temp

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
        with open("scores.txt", "w") as file:
            file.write(str(temp))
            file.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    with open("config.yml", 'r') as stream:
        configs = yaml.safe_load(stream)
        
    score_camera_configs = configs["score_camera"]
    score_camera = cv2.VideoCapture(score_camera_configs["index"])
    #score_camera.set(cv2.CAP_PROP_ZOOM, score_camera_configs["zoom"])
    score_camera.set(cv2.CAP_PROP_AUTOFOCUS, score_camera_configs["autofocus"])
    score_camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, score_camera_configs["autoexposure"])
    score_camera.set(cv2.CAP_PROP_EXPOSURE, score_camera_configs["exposure"])
    score_camera.set(cv2.CAP_PROP_GAIN, score_camera_configs["gain"])
    score_camera.set(cv2.CAP_PROP_BRIGHTNESS, score_camera_configs["brightness"])
    score_camera.set(cv2.CAP_PROP_SATURATION, score_camera_configs["saturation"])
    score_camera.set(cv2.CAP_PROP_CONTRAST, score_camera_configs["contrast"])
    read_video(score_camera)