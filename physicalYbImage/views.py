import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageChops
import requests
from io import BytesIO
import numpy as np
import os

# Function to download image asynchronously
def download_image_async(url):
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    return None

# Function to compare images using Mean Squared Error (MSE)
def compare_images(image1, image2, similarity_threshold=1):
    if image1.size != image2.size:
        return False

    image1 = image1.convert('L')  # Convert to grayscale
    image2 = image2.convert('L')  # Convert to grayscale

    image1_np = np.array(image1)
    image2_np = np.array(image2)

    mse = np.square(image1_np - image2_np).mean()
    similarity_percentage = 100.0 - (mse / float(image1_np.size)) * 100.0
    return similarity_percentage >= similarity_threshold

# Function to resize image
def resize_image(image, max_size=100):
    if max(image.size) > max_size:
        aspect_ratio = float(image.size[0]) / float(image.size[1])
        new_width = max_size if aspect_ratio >= 1 else int(max_size * aspect_ratio)
        new_height = max_size if aspect_ratio <= 1 else int(max_size / aspect_ratio)
        image = image.resize((new_width, new_height), Image.LANCZOS)
    return image

# Main function to process posts
def process_post(post):
    if not post['is_anonymous']:
        
        comparisonImageUrl = "https://yearbook.sarc-iitb.org/api/Impression_Images/user_1128/profile.jpg"
        
        comparisonImage = resize_image(download_image_async(comparisonImageUrl))

        image_url = f'https://yearbook.sarc-iitb.org{post["written_by_profile"]["profile_image"]}'

        image = resize_image(download_image_async(image_url))

        if compare_images(comparisonImage, image):
            post['written_by_profile']['profile_image'] = ""
        else:
            post['written_by_profile']['profile_image'] = f'https://yearbook.sarc-iitb.org{post["written_by_profile"]["profile_image"]}'

    return post

@csrf_exempt
def index(request):
    data = json.loads(request.body)
    posts = data.get("posts")

    if posts:
        new_posts = [process_post(post) for post in posts]

        json_response = json.dumps(new_posts)
        return HttpResponse(json_response, content_type="application/json")

    return HttpResponse("No posts provided.", status=400)
