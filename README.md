# FitFusion Exercise Tracker

FitFusion is a real-time exercise tracking application powered by computer vision. It uses your webcam to track and count exercises, providing feedback on your form and performance.

## Features

- Track multiple exercise types: Push-ups, Squats, Crunches, Pull-ups, and Plank
- Real-time pose detection and exercise counting
- Form feedback to improve your workout
- Voice assistant for audio feedback (local deployment only)
- Mobile-friendly interface
- Demo mode for when camera access isn't available

## Deployment

### Streamlit Cloud Deployment

To deploy this app to Streamlit Cloud:

1. Fork or push this repository to GitHub
2. Sign in to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create a new app and select your repository
4. Set the main file path to `app.py`
5. Deploy!

The app will automatically run in demo mode on Streamlit Cloud, as camera access may be limited in the cloud environment.

### Local Deployment

To run the app locally:

1. Clone the repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

## Requirements

- Python 3.8+
- Streamlit
- OpenCV
- MediaPipe
- NumPy
- Pillow
- pyttsx3 (optional, for voice feedback)

## Usage

1. Select an exercise type from the sidebar
2. Choose between using your camera or demo mode
3. Follow the on-screen instructions and feedback
4. The app will count your repetitions and provide form guidance

## Mobile Access

The app is optimized for mobile devices. When deployed to Streamlit Cloud, you can access it from any device with a web browser.

## License

MIT License
