import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
from PIL import Image
from exercise_tracker import ExerciseTracker
import time
import pyttsx3
import threading

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 1.0)  # Volume level

# Global variable to store the last feedback
last_feedback = ""

def speak_feedback(feedback):
    """Speak the feedback in a separate thread"""
    global last_feedback
    if feedback != last_feedback and st.session_state.voice_enabled:
        last_feedback = feedback
        threading.Thread(target=engine.say, args=(feedback,)).start()
        threading.Thread(target=engine.runAndWait).start()

def process_frame(frame, exercise_tracker):
    # Convert the BGR image to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process the frame and get pose landmarks
    results = pose.process(rgb_frame)
    
    # Draw pose landmarks on the frame
    annotated_frame = frame.copy()
    count = 0
    feedback = ""
    
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            annotated_frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )
        
        # Update exercise count and get feedback
        count, feedback = exercise_tracker.update(results.pose_landmarks.landmark)
        
        # Add feedback text to the frame
        cv2.putText(annotated_frame, feedback, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Speak the feedback if voice is enabled
        speak_feedback(feedback)
    
    return annotated_frame, count, feedback

def main():
    st.title("Real-time Exercise Tracking with Computer Vision")
    
    # Initialize voice enabled state
    if 'voice_enabled' not in st.session_state:
        st.session_state.voice_enabled = True
    
    # Sidebar for exercise selection
    exercise_type = st.sidebar.selectbox(
        "Select Exercise Type",
        ["Push-ups", "Squats", "Crunches", "Pull-ups", "Plank"]
    )
    
    # Voice assistant toggle
    voice_toggle = st.sidebar.toggle("Voice Assistant", value=st.session_state.voice_enabled)
    st.session_state.voice_enabled = voice_toggle
    
    # Voice settings (only show if voice is enabled)
    if st.session_state.voice_enabled:
        st.sidebar.markdown("### Voice Settings")
        voice_rate = st.sidebar.slider("Speech Rate", 100, 200, 150)
        voice_volume = st.sidebar.slider("Volume", 0.0, 1.0, 1.0)
        
        # Update voice settings
        engine.setProperty('rate', voice_rate)
        engine.setProperty('volume', voice_volume)
    
    # Add exercise instructions
    st.sidebar.markdown("### Exercise Instructions")
    if exercise_type == "Push-ups":
        st.sidebar.markdown("""
        - Start in a plank position
        - Lower your body until your chest nearly touches the floor
        - Push back up to the starting position
        - Keep your body straight throughout the movement
        """)
    elif exercise_type == "Squats":
        st.sidebar.markdown("""
        - Stand with feet shoulder-width apart
        - Lower your body by bending your knees
        - Keep your back straight and chest up
        - Return to the starting position
        """)
    elif exercise_type == "Crunches":
        st.sidebar.markdown("""
        - Lie on your back with knees bent
        - Place hands behind your head
        - Lift your upper body towards your knees
        - Lower back down with control
        """)
    elif exercise_type == "Pull-ups":
        st.sidebar.markdown("""
        - Hang from a bar with hands shoulder-width apart
        - Pull your body up until your chin clears the bar
        - Lower yourself back down with control
        - Keep your core engaged throughout
        """)
    elif exercise_type == "Plank":
        st.sidebar.markdown("""
        - Start in a push-up position
        - Lower onto your forearms
        - Keep your body in a straight line
        - Hold the position
        """)
    
    # Initialize exercise tracker
    if 'tracker' not in st.session_state or st.session_state.exercise_type != exercise_type:
        st.session_state.tracker = ExerciseTracker(exercise_type)
        st.session_state.exercise_type = exercise_type
        # Speak welcome message if voice is enabled
        if st.session_state.voice_enabled:
            speak_feedback(f"Starting {exercise_type} exercise. Follow the instructions on screen.")
    
    # Try different camera indices
    camera_index = st.sidebar.selectbox("Select Camera", [0, 1, 2], index=0)
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        st.error("""
            Failed to access webcam. Please try:
            1. Select a different camera from the sidebar
            2. Make sure your webcam is connected and not being used by another application
            3. Check if your webcam is enabled in system settings
            4. Try restarting the application
        """)
        return
    
    # Create placeholders for the video and feedback
    video_placeholder = st.empty()
    feedback_placeholder = st.empty()
    count_placeholder = st.empty()
    
    # Add a stop button
    stop_button = st.button("Stop")
    
    try:
        # Process webcam feed
        while cap.isOpened() and not stop_button:
            ret, frame = cap.read()
            if not ret:
                st.error("Lost connection to webcam")
                break
                
            # Process the frame
            processed_frame, count, feedback = process_frame(frame, st.session_state.tracker)
            
            # Convert the frame to RGB for display
            rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            
            # Display the frame
            video_placeholder.image(rgb_frame, channels="RGB")
            
            # Display feedback and count
            feedback_placeholder.write(f"Feedback: {feedback}")
            count_placeholder.write(f"Exercise Count: {count}")
            
            # Add a small delay to control frame rate
            time.sleep(0.01)  # 10ms delay
    
    finally:
        # Release resources
        cap.release()
        # Speak goodbye message if voice is enabled
        if st.session_state.voice_enabled:
            speak_feedback("Exercise session completed. Great job!")

if __name__ == "__main__":
    main() 