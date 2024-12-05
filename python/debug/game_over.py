import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

def detect_game_over(video_path, image_path):
    # Read the image and video files

    # Read the reference image
    reference_img = cv2.imread(image_path)
    if reference_img is None:
        print(f"Error: Could not read image from {image_path}")
        return

    # Blur the reference image
    reference_img = cv2.resize(reference_img, dsize=(0, 0), fx = 0.25, fy = 0.25, interpolation=cv2.INTER_CUBIC)
    blurred_reference = cv2.GaussianBlur(reference_img, (21, 21), 0)
    # Open the video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video from {video_path}")
        return
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter("game_over.mp4", fourcc, 
                          cap.get(cv2.CAP_PROP_FPS), 
                          (blurred_reference.shape[1], blurred_reference.shape[0]))

    while True:
        # Read a frame from the video
        ret, frame = cap.read()
        
        # Break the loop if no more frames
        if not ret:
            break

        # Blur the current frame
        

        # Resize blurred reference to match frame size if needed
        if blurred_reference.shape != frame.shape:
            frame_resized = cv2.resize(frame, (blurred_reference.shape[1], blurred_reference.shape[0]))
        else:
            frame_resized = frame

        blurred_frame = cv2.GaussianBlur(frame_resized, (21, 21), 0)
        # Convert images to grayscale for SSIM
        gray_reference = cv2.cvtColor(blurred_reference, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2GRAY)
        #print(blurred_frame.shape, blurred_reference.shape)
        # Compute Structural Similarity Index (SSIM)
        similarity_score = ssim(blurred_reference, blurred_frame, channel_axis=2)

        # Add similarity score to the frame
        text = f'Similarity: {similarity_score:.4f}'
        cv2.putText(blurred_frame, text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if similarity_score >= 0.8:
            cv2.putText(blurred_frame, "Game Over Detected", (10, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        # Display the frame
        out.write(blurred_frame)

    # Release resources
    cap.release()
    out.release()
    cv2.destroyAllWindows()

import os
def save_frames(video_path, out_path):
    cap = cv2.VideoCapture(video_path)
    
    # Check if video opened successfully
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return 0
    
    # Initialize frame counter
    frame_count = 0
    
    # Read frames until end of video
    while True:
        # Read a frame
        ret, frame = cap.read()
        
        # Break the loop if no more frames
        if not ret:
            break
        
        # Generate filename
        filename = os.path.join(out_path, f'{frame_count}.png')
        
        # Save the frame
        cv2.imwrite(filename, frame)
        
        # Increment frame counter
        frame_count += 1
    
    # Release video capture object
    cap.release()
if __name__ == "__main__":
    detect_game_over("tna_end.mp4", "./frames/256.png")