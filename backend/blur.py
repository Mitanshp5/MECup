import cv2

def is_blurry(image_path, threshold=100):
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Image not found")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Compute Laplacian variance
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    # Decide blur
    blurry = lap_var < threshold

    return blurry, lap_var


# Example usage
image_path = "test.jpg"
blurry, score = is_blurry(image_path)

print("Blur score:", score)
print("Blurry?" , blurry)