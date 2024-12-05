import cv2 
import yaml
import numpy as np

with open("../config.yml", 'r') as stream:
    configs = yaml.safe_load(stream)

score_camera = cv2.VideoCapture(configs["score_camera"]["index"])
playfield_camera = cv2.VideoCapture(configs["playfield_camera"]["index"])
start_camera = cv2.VideoCapture(configs["start_camera"]["index"])

while True:
    _, score_frame = score_camera.read()
    _, play_frame = playfield_camera.read()
    _, start_frame = start_camera.read()
    
    frames = np.vstack((score_frame, play_frame, start_frame))
    frames = cv2.resize(frames, (0,0), fx = 0.25, fy = 0.25)
    cv2.imshow('frame', frames)

    if cv2.waitKey(1) == ord('q'):
        break

# Release the capture
score_camera.release()
playfield_camera.release()
start_camera.release()
cv2.destroyAllWindows()
