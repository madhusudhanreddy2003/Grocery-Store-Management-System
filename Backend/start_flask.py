import subprocess
import os

# Set the environment for your Flask app
os.environ['FLASK_APP'] = r"E:\\mini project new [Final Draft]\\mini project new\\backend\\server.py"  # Full path to server.py

# Start the Flask server
subprocess.run(["flask", "run", "--host=0.0.0.0", "--port=3000"])
