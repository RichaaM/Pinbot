import cv2 
import yaml
import numpy as np

with open("config.yml", 'r') as stream:
    configs = yaml.safe_load(stream)

print(configs)

score_camera_configs = configs["score_camera"]
score_camera = cv2.VideoCapture(score_camera_configs["index"])
    
score_camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, score_camera_configs["autoexposure"])
score_camera.set(cv2.CAP_PROP_EXPOSURE, score_camera_configs["exposure"])
score_camera.set(cv2.CAP_PROP_GAIN, score_camera_configs["gain"])
score_camera.set(cv2.CAP_PROP_BRIGHTNESS, score_camera_configs["brightness"])
score_camera.set(cv2.CAP_PROP_SATURATION, score_camera_configs["saturation"])
score_camera.set(cv2.CAP_PROP_CONTRAST, score_camera_configs["contrast"])

playfield_camera = cv2.VideoCapture(configs["playfield_camera"]["index"])

start_camera = cv2.VideoCapture(configs["start_camera"]["index"])

while True:
    _, score_frame = score_camera.read()
    
    _, start_frame = start_camera.read()
    _, play_frame = playfield_camera.read()

    frames = np.vstack((score_frame, play_frame, start_frame))
    frames = cv2.resize(frames, (0,0), fx = 0.5, fy = 0.5)
    cv2.imshow('frame', frames)

    if cv2.waitKey(20) == ord('q'):
        break


# Release the capture
score_camera.release()
playfield_camera.release()
start_camera.release()
cv2.destroyAllWindows()
