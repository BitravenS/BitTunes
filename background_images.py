import os
import subprocess
import requests
import signal
from PIL import Image
from dotenv import load_dotenv
import argparse
import platform  # For OS-specific checks

# Load environment variables
load_dotenv()

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description="Download images from Pexels based on search query."
)
parser.add_argument("query", type=str, help="Search query for the images")
args = parser.parse_args()

# Get the search query from the CLI argument
search_query = args.query

# Set up the Pexels API
pexels_api = os.getenv("PEXELS_API_KEY")
pexels_api_url = "https://api.pexels.com/v1/search"

headers = {"Authorization": pexels_api}
params = {"query": search_query, "orientation": "landscape"}
response = requests.get(pexels_api_url, headers=headers, params=params)

if response.status_code == 200:
    photos = response.json().get("photos", [])
else:
    print(f"Error: {response.status_code}, {response.text}")
    exit(1)

# Process each photo
for index, photo in enumerate(photos):
    image_url = photo["src"]["medium"]
    response = requests.get(image_url)
    if response.status_code == 200:
        temp_image_path = f"temp_photo_{photo['id']}.jpg"

        with open(temp_image_path, "wb") as f:
            f.write(response.content)

        # Open the image viewer based on the OS
        if platform.system() == "Windows":
            viewer_process = subprocess.Popen(
                ["start", temp_image_path],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        else:  # For Unix-like systems (Linux/macOS)
            viewer_process = subprocess.Popen(
                ["xdg-open", temp_image_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )

        # Prompt the user
        user_input = (
            input(f"Do you want to save photo {index + 1} (ID: {photo['id']})? (y/n): ")
            .strip()
            .lower()
        )

        if user_input == "y":
            with open(temp_image_path, "rb") as f:
                img = Image.open(f)
                img.save(f"photo_{photo['id']}.jpg")
            print(f"Photo {photo['id']} saved as 'photo_{photo['id']}.jpg'")
        else:
            print(f"Photo {photo['id']} not saved.")

        # Close the viewer
        if platform.system() == "Windows":
            viewer_process.terminate()  # Terminate process on Windows
        else:
            os.killpg(
                os.getpgid(viewer_process.pid), signal.SIGTERM
            )  # Terminate process group on Unix-like systems

        # Remove the temporary image
        os.remove(temp_image_path)

    else:
        print(f"Failed to download image {photo['id']}.")

print("Finished processing all images.")
