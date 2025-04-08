import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
from PIL import Image
from exercise_tracker import ExerciseTracker
import time
import threading
import os

# Conditionally import pyttsx3 - it may not work on Streamlit Cloud
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# Initialize text-to-speech engine with error handling
tts_available = False
tts_lock = threading.Lock()  # Add a lock for thread safety

# We'll initialize the TTS engine later in the main function if available
engine = None

# Check if we're running on Streamlit Cloud
is_streamlit_cloud = os.environ.get('STREAMLIT_SHARING', '') == 'true' or \
                    os.environ.get('STREAMLIT_CLOUD', '') == 'true'

# Global variable to store the last feedback
last_feedback = ""

def speak_feedback(feedback):
    """Speak the feedback safely"""
    global last_feedback, engine
    
    # Only proceed if TTS is available and enabled
    if not (tts_available and st.session_state.voice_enabled):
        return
        
    # Only speak if feedback has changed
    if feedback == last_feedback:
        return
        
    last_feedback = feedback
    
    # Skip actual TTS on Streamlit Cloud as it won't work there
    if is_streamlit_cloud:
        return
    
    # Use the lock to prevent multiple threads from using the engine simultaneously
    if tts_lock.acquire(blocking=False):
        try:
            # Define a function that releases the lock when done
            def speak_and_release():
                try:
                    engine.say(feedback)
                    engine.runAndWait()
                except Exception as e:
                    # Silently handle errors to prevent app crashes
                    pass
                finally:
                    # Always release the lock
                    tts_lock.release()
            
            # Start a thread for speaking
            thread = threading.Thread(target=speak_and_release)
            thread.daemon = True  # Make thread a daemon so it doesn't block app exit
            thread.start()
        except Exception:
            # If anything goes wrong, make sure to release the lock
            tts_lock.release()

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
    st.set_page_config(
        page_title="FitFusion - Exercise Tracker",
        page_icon="💪",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS for better mobile experience
    st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    [data-testid=stSidebar] {padding-top: 2rem;}
    .stButton button {width: 100%;}
    @media (max-width: 640px) {
        .block-container {padding: 1rem 0.5rem;}
        h1 {font-size: 1.8rem !important;}
        .stButton button {padding: 0.75rem 0.5rem;}
    }
    </style>
    """, unsafe_allow_html=True)
    
    # App title with emoji
    st.title("💪 FitFusion Exercise Tracker")
    st.markdown("*Real-time exercise tracking powered by computer vision*")
    
    # Initialize voice enabled state
    if 'voice_enabled' not in st.session_state:
        st.session_state.voice_enabled = True
        
    # Initialize TTS engine here to avoid Streamlit's script rerun issues
    global engine, tts_available
    
    # Skip TTS initialization on Streamlit Cloud
    if is_streamlit_cloud:
        if 'cloud_warning_shown' not in st.session_state:
            st.sidebar.info("ℹ️ Voice feedback is disabled on Streamlit Cloud")
            st.session_state.cloud_warning_shown = True
        tts_available = False
    elif PYTTSX3_AVAILABLE and engine is None:
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)  # Speed of speech
            engine.setProperty('volume', 1.0)  # Volume level
            tts_available = True
        except Exception as e:
            st.sidebar.warning("⚠️ Voice feedback unavailable: " + str(e))
            tts_available = False
    else:
        if 'tts_warning_shown' not in st.session_state:
            st.sidebar.warning("⚠️ Text-to-speech module not available")
            st.session_state.tts_warning_shown = True
        tts_available = False
    
    # Sidebar for exercise selection
    exercise_type = st.sidebar.selectbox(
        "Select Exercise Type",
        ["Push-ups", "Squats", "Crunches", "Pull-ups", "Plank"]
    )
    
    # Voice assistant toggle (only if TTS is available and not on Streamlit Cloud)
    if tts_available and not is_streamlit_cloud:
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
    elif is_streamlit_cloud:
        st.session_state.voice_enabled = False
    else:
        st.sidebar.info("Voice assistant not available on this device.")
        st.session_state.voice_enabled = False
    
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
    
    # Camera handling with fallback options
    st.sidebar.markdown("### Camera Settings")
    
    # Option to use camera or not
    use_camera = st.sidebar.checkbox("Enable Camera", value=True)
    
    if not use_camera:
        st.warning("Camera is disabled. Enable it in the sidebar to track exercises.")
        # Display a static image instead
        st.image("https://img.freepik.com/free-vector/fitness-tracker-concept-illustration_114360-1525.jpg", 
                 caption="Enable camera to start exercise tracking")
        return
    
    # Add a mock mode option for testing without a camera
    # Default to mock mode on Streamlit Cloud as camera access may be limited
    default_mock = True if is_streamlit_cloud else False
    mock_mode = st.sidebar.checkbox("Use Demo Mode", value=default_mock, 
                                   help="Enable this if you don't have a working camera or are on mobile")
    
    if mock_mode:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("📷 Running in demo mode with simulated camera feed")
        with col2:
            if st.button("⟳ Refresh", help="Refresh the demo"):
                st.experimental_rerun()
        # Create a placeholder for the mock video
        video_placeholder = st.empty()
        feedback_placeholder = st.empty()
        count_placeholder = st.empty()
        
        # Create a stop button
        stop_button = st.button("Stop")
        
        # Create a more visually appealing mock frame
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add a gradient background
        for i in range(480):
            mock_frame[i, :] = [int(40 + i/8), int(10 + i/16), int(80 + i/6)]
            
        # Add text
        cv2.putText(mock_frame, f"FitFusion - {exercise_type}", (50, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(mock_frame, "DEMO MODE", (180, 240), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        cv2.putText(mock_frame, "No camera access required", (150, 300), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)
        
        # Initialize exercise tracker
        if 'tracker' not in st.session_state or st.session_state.exercise_type != exercise_type:
            st.session_state.tracker = ExerciseTracker(exercise_type)
            st.session_state.exercise_type = exercise_type
        
        # Use session state to track demo count and time
        if 'demo_count' not in st.session_state:
            st.session_state.demo_count = 0
            st.session_state.last_update = time.time()
            st.session_state.demo_feedback = ""
        
        # Update count based on time passed
        current_time = time.time()
        if current_time - st.session_state.last_update > 2:  # Update every 2 seconds
            st.session_state.demo_count = (st.session_state.demo_count + 1) % 30
            st.session_state.last_update = current_time
            
            # Generate different feedback messages based on count
            if st.session_state.demo_count % 5 == 0:
                st.session_state.demo_feedback = f"Great form! Keep going with {exercise_type}"
            elif st.session_state.demo_count % 5 == 2:
                st.session_state.demo_feedback = "Remember to maintain proper posture"
            elif st.session_state.demo_count % 5 == 4:
                st.session_state.demo_feedback = "Almost there! One more rep"
            else:
                st.session_state.demo_feedback = f"Continue your {exercise_type} routine"
        
        # Display the mock frame and stats
        video_placeholder.image(mock_frame, channels="RGB")
        
        # Use columns for a better mobile layout
        stat_col1, stat_col2 = st.columns(2)
        with stat_col1:
            count_placeholder.metric("Exercise Count", st.session_state.demo_count)
        with stat_col2:
            # Add a timer
            elapsed = int(time.time() - st.session_state.last_update + st.session_state.demo_count * 2)
            minutes, seconds = divmod(elapsed, 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            st.metric("Workout Time", time_str)
        
        feedback_placeholder.info(st.session_state.demo_feedback)
        
        # Check if stop button was pressed
        if stop_button:
            st.success("Workout complete! Great job!")
            # Reset demo state
            if 'demo_count' in st.session_state:
                del st.session_state.demo_count
                del st.session_state.last_update
            return
            
        # Auto-rerun to update the UI
        time.sleep(0.5)  # Short delay to prevent too many reruns
        st.experimental_rerun()
        return
    
    # Real camera mode
    # Try different camera indices with better error handling
    camera_options = ["Default Camera (0)", "Alternative Camera 1 (1)", "Alternative Camera 2 (2)", "Custom Camera Path"]
    camera_selection = st.sidebar.selectbox("Select Camera Source", camera_options)
    
    # Map selection to camera index
    if camera_selection == "Custom Camera Path":
        camera_path = st.sidebar.text_input("Enter camera path or URL", "/dev/video0")
        try:
            cap = cv2.VideoCapture(camera_path)
        except Exception as e:
            st.error(f"Error with custom camera path: {str(e)}")
            st.info("Try enabling 'Use Mock Camera' option above for a demo without a real camera.")
            return
    else:
        # Extract index from selection (0, 1, or 2)
        camera_index = 0 if "0" in camera_selection else 1 if "1" in camera_selection else 2
        try:
            cap = cv2.VideoCapture(camera_index)
        except Exception as e:
            st.error(f"Error accessing camera {camera_index}: {str(e)}")
            st.info("Try enabling 'Use Mock Camera' option above for a demo without a real camera.")
            return
    
    # Check if camera opened successfully
    if not cap.isOpened():
        st.error(f"""Failed to access camera {camera_selection}. Please try:
            1. Select a different camera from the sidebar
            2. Make sure your webcam is connected and not being used by another application
            3. Check if your webcam is enabled in system settings
            4. Try enabling 'Use Mock Camera' option above for a demo without a real camera
            5. If using Linux, you may need to grant camera permissions
        """)
        
        # Provide troubleshooting help
        with st.expander("Camera Troubleshooting"):
            st.markdown("""### Linux Camera Permissions
            If you're on Linux, try these commands in terminal to check and fix camera permissions:
            ```bash
            # List video devices
            ls -l /dev/video*
            
            # Check if your user has permission to access the camera
            groups $(whoami) | grep video
            
            # If not in video group, add yourself (may require restart)
            sudo usermod -a -G video $(whoami)
            ```
            
            ### Other Common Issues
            - Make sure no other application is using the camera
            - Check system settings to ensure camera is enabled
            - Try unplugging and reconnecting your webcam
            - Restart your computer
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