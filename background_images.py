import os
import subprocess
import requests
import signal
from PIL import Image
from dotenv import load_dotenv
import argparse

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
    photos = response.json()["photos"]

else:
    print(f"Error: {response.status_code}, {response.text}")

for index, photo in enumerate(photos):
    image_url = photo["src"]["medium"]
    response = requests.get(image_url)
    if response.status_code == 200:
        temp_image_path = f"temp_photo_{photo['id']}.jpg"

        with open(temp_image_path, "wb") as f:
            f.write(response.content)

        if os.name == "posix":  # For Linux or macOS
            viewer_process = subprocess.Popen(
                [
                    "xdg-open",
                    temp_image_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,  # Ensures the process runs in its own process group
            )
        elif os.name == "nt":  # For Windows
            viewer_process = subprocess.Popen(
                ["start", temp_image_path],
                shell=True,  # Required for the "start" command to work on Windows
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

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
            os.killpg(os.getpgid(viewer_process.pid), signal.SIGTERM)
            break

        else:
            print(f"Photo {photo['id']} not saved.")

        os.killpg(os.getpgid(viewer_process.pid), signal.SIGTERM)
        os.remove(temp_image_path)

    else:
        print(f"Failed to download image {photo['id']}.")

print("Finished processing all images.")
