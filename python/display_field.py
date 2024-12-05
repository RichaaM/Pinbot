import cv2
import matplotlib.pyplot as plt
import numpy as np
import copy
import yaml

def detect_aruco_markers(image, show=False):
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    
    img_copy = copy.deepcopy(image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    detectorParams = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, detectorParams)
    markerCorners, markerIds, rejectedCandidates = detector.detectMarkers(gray)

    top_left = None
    top_right = None
    bottom_left = None
    bottom_right = None

    if markerIds is not None:
        cv2.aruco.drawDetectedMarkers(image, markerCorners, markerIds)
        
        for i, marker_id in enumerate(markerIds):
            if marker_id[0] == 12:
                top_right = (int(markerCorners[i][0][0][0]), int(markerCorners[i][0][0][1]))
                cv2.circle(image, top_right, 10, (0,0,255),-1)
            elif marker_id[0] == 13:
                bottom_right = (int(markerCorners[i][0][1][0]), int(markerCorners[i][0][1][1]))
                cv2.circle(image, bottom_right, 10, (0,0,255),-1)
            elif marker_id[0] == 14:
                bottom_left = (int(markerCorners[i][0][3][0]), int(markerCorners[i][0][3][1]))
                cv2.circle(image, bottom_left, 10, (0,0,255),-1)
            elif marker_id[0] == 15:
                top_left = (int(markerCorners[i][0][2][0]), int(markerCorners[i][0][2][1]))
                cv2.circle(image, top_left, 10, (0,0,255),-1)
    
    if show:
        cv2.imshow('ArUco Marker Detection', image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    if top_left is None or top_right is None or bottom_left is None or bottom_right is None:
        return None, None
    
    return img_copy, np.array([list(top_left), list(top_right), list(bottom_right), list(bottom_left)])

def correct_perspective(image, points):

    points = np.float32(points)
    
    width_top = np.sqrt(((points[1][0] - points[0][0]) ** 2) + 
                       ((points[1][1] - points[0][1]) ** 2))
    
    width_bottom = np.sqrt(((points[2][0] - points[3][0]) ** 2) + 
                          ((points[2][1] - points[3][1]) ** 2))
    
    width = max(int(width_top), int(width_bottom))
    
    height_left = np.sqrt(((points[3][0] - points[0][0]) ** 2) + 
                         ((points[3][1] - points[0][1]) ** 2))
    height_right = np.sqrt(((points[2][0] - points[1][0]) ** 2) + 
                          ((points[2][1] - points[1][1]) ** 2))
    height = max(int(height_left), int(height_right))
    
    dst_points = np.float32([[0, 0],
                           [width - 1, 0],
                           [width - 1, height - 1],
                           [0, height - 1]])
    
    matrix = cv2.getPerspectiveTransform(points, dst_points)
    
    return matrix, width, height


def correctVideo(cap):


    perspective_matrix = None
    width = None
    height = None

    while True:
        _, frame = cap.read()
        
        image, points = detect_aruco_markers(frame)

        if image is None:
            continue

        if perspective_matrix is None:
            perspective_matrix, width, height = correct_perspective(image, points)

        res = cv2.warpPerspective(image, perspective_matrix, (width, height))

        cv2.imshow("field", res)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    with open("config.yml", 'r') as stream:
        configs = yaml.safe_load(stream)
    
    playfield_camera = cv2.VideoCapture(configs["playfield_camera"]["index"])
    playfield_camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, configs["score_camera"]["autoexposure"])
    correctVideo(playfield_camera)