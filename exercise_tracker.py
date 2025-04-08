import mediapipe as mp
import numpy as np
import time

class ExerciseTracker:
    def __init__(self, exercise_type):
        self.exercise_type = exercise_type
        self.count = 0
        self.state = "down"  # Initial state for push-ups and squats
        self.last_count_time = time.time()
        self.feedback = ""
        self.rep_start_time = None
        
    def calculate_angle(self, a, b, c):
        """Calculate the angle between three points"""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle > 180.0:
            angle = 360-angle
            
        return angle
    
    def track_pushup(self, landmarks):
        """Track push-up exercise"""
        if landmarks:
            # Get relevant landmarks
            left_shoulder = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value].x,
                           landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value].y]
            left_elbow = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value].x,
                         landmarks[mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value].y]
            left_wrist = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST.value].x,
                         landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST.value].y]
            
            # Calculate angle
            angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
            
            # Count logic
            if angle < 90 and self.state == "down":
                self.state = "up"
                self.feedback = "Good form! Keep going up"
            elif angle > 160 and self.state == "up":
                self.state = "down"
                self.count += 1
                self.last_count_time = time.time()
                self.feedback = f"Rep {self.count} completed!"
            elif self.state == "up" and angle < 160:
                self.feedback = "Go all the way up!"
            elif self.state == "down" and angle > 90:
                self.feedback = "Go lower for a proper push-up"
                
        return self.count, self.feedback
    
    def track_squat(self, landmarks):
        """Track squat exercise"""
        if landmarks:
            # Get relevant landmarks
            left_hip = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP.value].x,
                       landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP.value].y]
            left_knee = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value].x,
                        landmarks[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value].y]
            left_ankle = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_ANKLE.value].x,
                         landmarks[mp.solutions.pose.PoseLandmark.LEFT_ANKLE.value].y]
            
            # Calculate angle
            angle = self.calculate_angle(left_hip, left_knee, left_ankle)
            
            # Count logic
            if angle < 90 and self.state == "down":
                self.state = "up"
                self.feedback = "Good depth! Now stand up"
            elif angle > 160 and self.state == "up":
                self.state = "down"
                self.count += 1
                self.last_count_time = time.time()
                self.feedback = f"Rep {self.count} completed!"
            elif self.state == "up" and angle < 160:
                self.feedback = "Stand up straight!"
            elif self.state == "down" and angle > 90:
                self.feedback = "Go lower for a proper squat"
                
        return self.count, self.feedback
    
    def track_crunch(self, landmarks):
        """Track crunch exercise"""
        if landmarks:
            # Get relevant landmarks
            left_shoulder = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value].x,
                           landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value].y]
            left_hip = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP.value].x,
                       landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP.value].y]
            left_knee = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value].x,
                        landmarks[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value].y]
            
            # Calculate angle between shoulder, hip, and knee
            angle = self.calculate_angle(left_shoulder, left_hip, left_knee)
            
            # Count logic
            if angle < 60 and self.state == "down":
                self.state = "up"
                self.feedback = "Good crunch! Now lower down"
            elif angle > 120 and self.state == "up":
                self.state = "down"
                self.count += 1
                self.last_count_time = time.time()
                self.feedback = f"Rep {self.count} completed!"
            elif self.state == "up" and angle > 60:
                self.feedback = "Keep your core engaged!"
            elif self.state == "down" and angle < 120:
                self.feedback = "Lower down completely"
                
        return self.count, self.feedback
    
    def track_pullup(self, landmarks):
        """Track pull-up exercise"""
        if landmarks:
            # Get relevant landmarks
            left_shoulder = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value].x,
                           landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value].y]
            left_elbow = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value].x,
                         landmarks[mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value].y]
            left_wrist = [landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST.value].x,
                         landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST.value].y]
            
            # Calculate angle
            angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
            
            # Count logic
            if angle > 160 and self.state == "down":
                self.state = "up"
                self.feedback = "Good form! Keep pulling up"
            elif angle < 90 and self.state == "up":
                self.state = "down"
                self.count += 1
                self.last_count_time = time.time()
                self.feedback = f"Rep {self.count} completed!"
            elif self.state == "up" and angle > 90:
                self.feedback = "Pull up higher!"
            elif self.state == "down" and angle < 160:
                self.feedback = "Lower down completely"
                
        return self.count, self.feedback
    
    def track_plank(self, landmarks):
        """Track plank exercise duration"""
        if landmarks:
            # For plank, we track duration in seconds
            if self.rep_start_time is None:
                self.rep_start_time = time.time()
            
            duration = int(time.time() - self.rep_start_time)
            self.count = duration
            self.feedback = f"Hold for {duration} seconds"
        return self.count, self.feedback
    
    def update(self, landmarks):
        """Update exercise count based on exercise type"""
        if self.exercise_type == "Push-ups":
            return self.track_pushup(landmarks)
        elif self.exercise_type == "Squats":
            return self.track_squat(landmarks)
        elif self.exercise_type == "Crunches":
            return self.track_crunch(landmarks)
        elif self.exercise_type == "Pull-ups":
            return self.track_pullup(landmarks)
        elif self.exercise_type == "Plank":
            return self.track_plank(landmarks)
        return self.count, self.feedback 