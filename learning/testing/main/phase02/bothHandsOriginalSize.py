import mediapipe as mp
from cvzone.ClassificationModule import Classifier
import cv2
import numpy as np
import math
import time
import os

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

classifier = Classifier("learning/model/keras_model.h5", "learning/model/labels.txt")

# Initialize hand tracking
hands = mp_hands.Hands(min_detection_confidence=0.6, min_tracking_confidence=0.5, max_num_hands=2)

# Initialize webcam
cap = cv2.VideoCapture(0)

# Hand cropping constants
offset = 30  # Adjust this offset as needed
imgSize = 400
folder = "Data/one"
counter = 0

# Create the "Data" folder if it doesn't exist
if not os.path.exists(folder):
    os.makedirs(folder)

# Flags to track the state of each hand
left_hand_detected = False
right_hand_detected = False

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Process the frame using mediapipe hands
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = hands.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Reset flags for each iteration
        left_hand_detected = False
        right_hand_detected = False

        if results.multi_hand_landmarks:
            # Initialize lists to store coordinates of each hand's landmarks
            left_hand_landmarks = []
            right_hand_landmarks = []

            for landmarks, hand in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Determine if the hand is left or right and assign a unique color.
                if hand.classification[0].label == "Left":
                    hand_color = (121, 22, 76)  # Color for the left hand
                    left_hand_detected = True
                else:
                    hand_color = (121, 44, 250)  # Color for the right hand
                    right_hand_detected = True

                # Draw landmarks and connections using the determined hand color for both hands
                mp_drawing.draw_landmarks(image, landmarks, mp_hands.HAND_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=hand_color, thickness=2, circle_radius=4),
                                          mp_drawing.DrawingSpec(color=hand_color, thickness=2, circle_radius=2))

                # Append landmarks coordinates to the respective hand list
                if hand.classification[0].label == "Left":
                    left_hand_landmarks.extend([(lm.x * image.shape[1], lm.y * image.shape[0]) for lm in landmarks.landmark])
                else:
                    right_hand_landmarks.extend([(lm.x * image.shape[1], lm.y * image.shape[0]) for lm in landmarks.landmark])

                # Hand cropping
                min_x = min(int(lm.x * image.shape[1]) for lm in landmarks.landmark)
                max_x = max(int(lm.x * image.shape[1]) for lm in landmarks.landmark)
                min_y = min(int(lm.y * image.shape[0]) for lm in landmarks.landmark)
                max_y = max(int(lm.y * image.shape[0]) for lm in landmarks.landmark)

                x, y, w, h = min_x, min_y, max_x - min_x, max_y - min_y
                cropHand = image[y - offset:y + h + offset, x - offset:x + w + offset]

            # Check if both hands are close
            if left_hand_detected and right_hand_detected:
                # Create a rectangle that encloses both hands
                min_x = min(left_hand_landmarks + right_hand_landmarks, key=lambda item: item[0])[0]
                min_y = min(left_hand_landmarks + right_hand_landmarks, key=lambda item: item[1])[1]
                max_x = max(left_hand_landmarks + right_hand_landmarks, key=lambda item: item[0])[0]
                max_y = max(left_hand_landmarks + right_hand_landmarks, key=lambda item: item[1])[1]

                # Add offset to the rectangle
                min_x -= offset
                min_y -= offset
                max_x += offset
                max_y += offset

                # Crop the region enclosed by the modified rectangle
                cropHands = image[int(min_y):int(max_y), int(min_x):int(max_x)]

            # Display the cropped hand image when the 's' key is pressed
            if (left_hand_detected and not right_hand_detected) or (right_hand_detected and not left_hand_detected):
                cv2.imshow("ImageCrop", cropHand)
                prediction, index = classifier.getPrediction(cropHand)
                print(prediction,index)

            # Check if both hands are close
            if left_hand_detected and right_hand_detected:
                # Display the cropped hand image when the 's' key is pressed
                cv2.imshow("ImageCrop", cropHands)
                prediction, index = classifier.getPrediction(cropHands)
                print(prediction,index)
                

        # Display the frame with hand tracking
        cv2.imshow('Hand Tracking', image)

        # Exit the loop when the 'Esc' key is pressed
        if cv2.waitKey(5) & 0xFF == 27:
            break

finally:
    # Release resources
    cap.release()
    cv2.destroyAllWindows()
