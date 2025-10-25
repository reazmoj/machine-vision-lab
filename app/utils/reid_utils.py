import torch 
import numpy as np
import cv2
import matplotlib.pyplot as plt
import os


def rgba_to_rgb_blend_image(image, background_color=(255, 255, 255)):
    """
    Convert an RGBA image to an RGB image by blending with a background color.
    
    Parameters:
        image (numpy.ndarray): The RGBA image array.
        background_color (tuple): The RGB background color as a tuple (R, G, B).
    
    Returns:
        numpy.ndarray: The blended RGB image array.
    """
    # Normalize background color to range [0, 1] if the image is normalized
    if image.dtype == np.float32 or image.max() <= 1.0:
        background_color = [c / 255.0 for c in background_color]
    
    # Extract color and alpha channels
    rgb = image[..., :3]  # RGB channels
    alpha = image[..., 3:]  # Alpha channel
    
    # Blend the image with the background color
    # blended_rgb = (rgb * alpha) + (np.array(background_color) * (1 - alpha))
    
    return rgb


def read_image(image_path, image_size=(100, 100)):
    """
    Load and preprocess an image for model inference.

    Args:
        image_path (str): Path to the image file.
        image_size (tuple): Target size for resizing the image (width, height).

    Returns:
        torch.Tensor: Preprocessed image tensor of shape (1, C, H, W).
    """
    image = plt.imread(image_path)

    image = cv2.resize(image, 
                       dsize=image_size, 
                       interpolation=cv2.INTER_CUBIC)
    print("====================")
    print(image.shape)
    print("====================")
    image = image.transpose(2, 0, 1) / 255.0
    
    image_tensor = torch.tensor(image, dtype=torch.float32).unsqueeze(0)
    return image_tensor


def normalize_and_flatten(features):
    """
    Normalize a tensor using L2 norm and flatten it for further processing.

    Args:
        features (torch.Tensor): Input tensor of shape (batch_size, channels, height, width).

    Returns:
        torch.Tensor: Flattened and normalized tensor of shape (batch_size, -1).
    """
    # Compute L2 norm along the specified dimension and scale by sqrt of the last dimension
    fnorm = torch.norm(features, p=2, dim=1, keepdim=True) * np.sqrt(features.size(-1))
    
    # Normalize the tensor by dividing with the computed norm
    normalized_features = features / fnorm.expand_as(features)
    
    # Flatten the tensor into (batch_size, -1)
    flattened_features = normalized_features.view(features.size(0), -1)
    
    return flattened_features

def process_buildings(buildings, base_features, metadata, image, model):
    distance = []
    for _count, building in enumerate(buildings):
        # bx = building

        building = cv2.resize(building, 
                        dsize=(100,100), 
                        interpolation=cv2.INTER_CUBIC)
        
        building = building.transpose(2, 0, 1) / 255.0

        building_tensor = torch.tensor(building, dtype=torch.float32).unsqueeze(0)  # Shape (1, C, H, W)
    

        with torch.no_grad():
            _, side_out = model(None,building_tensor)
        side_out_feature_vector = normalize_and_flatten(side_out)
        dist = []
        for i in base_features:
            dist.append(torch.mm(side_out_feature_vector,i))
            
        distance.append(max(dist))
        # distance.append(torch.mean(torch.stack(dist)))

        # Draw rectangle around building
        # x1, y1, x2, y2, m = metadata[_count]
        # cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        # if float(dist>0.70):
        #     name = os.path.join(str(dist)+".png")
        #     cv2.imwrite(name, bx) 

        
    return distance

def extract_buildings(detection_results, image, frame_shape):
    """
    Extract cropped building images and their metadata from YOLO detection results.
    
    Args:
        detection_results: YOLO detection results containing bounding box information.
        image: Input image as a NumPy array (H, W, C).
        frame_shape: Tuple representing the frame dimensions (height, width).
    
    Returns:
        buildings: List of cropped building images as NumPy arrays.
        metadata: List of bounding box details (x1, y1, x2, y2, center).
    """
    buildings = []
    metadata = []
    
    for bbox in detection_results[0].boxes.xyxy:
        x1, y1, x2, y2 = map(int, bbox)  # Convert bounding box values to integers
        width, height = x2 - x1, y2 - y1
        center = (x1 + width // 2, y1 + height // 2)
        padding = max(width, height) * .6
        
        # Adjust coordinates with padding while ensuring they stay within the image frame
        crop_x1 = max(0, int(center[0] - padding))
        crop_y1 = max(0, int(center[1] - padding))
        crop_x2 = min(frame_shape[1], int(center[0] + padding))
        crop_y2 = min(frame_shape[0], int(center[1] + padding))
        
        # Crop the image and save
        cropped_image = image[crop_y1:crop_y2, crop_x1:crop_x2]
        buildings.append(cropped_image)
        metadata.append({
                "coordinates": [crop_x1, crop_y1, crop_x2, crop_y2],
                "center": center
            })    
    return buildings, metadata

def calculate_dis(metric, base_features, query_features, print_dist=True):
    """
    Calculate the distance or similarity between two feature vectors using a specified metric.

    Args:
        metric (str): Metric to use for calculation ('eq' for Euclidean, 'cos' for Cosine similarity).
        base_features (np.ndarray): Base feature vector.
        query_features (np.ndarray): Query feature vector.
        print_dist (bool): Whether to print the calculated distance or similarity.

    Returns:
        float: Calculated distance or similarity.
    """
    
    # Handle Euclidean distance
    if metric == "eq":
        dist = np.linalg.norm(base_features - query_features)
    
    # Handle Cosine similarity
    elif metric == "cos":
        base_norm = np.linalg.norm(base_features)
        query_norm = np.linalg.norm(query_features)
        
        # Avoid division by zero for zero vectors
        if base_norm == 0 or query_norm == 0:
            dist = 0.0
        else:
            dist = np.dot(base_features, query_features) / (base_norm * query_norm)
    
    # Raise an error if an unsupported metric is used
    else:
        raise ValueError(f"Unsupported metric '{metric}'. Supported metrics are 'eq' (Euclidean) and 'cos' (Cosine).")

    # Print similarity if required
    if print_dist:
        print(f"Similarity ({metric}): {dist:.4f}")

    return dist

def add_distance_to_image(image,metadata):
    """
    Annotates the given image with bounding boxes and distances from metadata.
    
    Parameters:
        image (numpy.ndarray): The image to annotate.
        metadata (list of dict): List containing metadata dictionaries with 'coordinates', 'center', and 'distance'.
    
    Returns:
        numpy.ndarray: Annotated image.
    """
    if metadata:
        max_distance = max(metadata, key=lambda x: x['distance'])["distance"]*100
        for i in metadata:
            x1, y1, x2, y2 = i["coordinates"]
            center = i["center"]
            distance = i["distance"]*100
            
            cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
            if distance== max_distance:
                cv2.rectangle(image, (x1, y1), (x2, y2), (255, 255, 0), 4)


            
            image = cv2.putText(image,
                                str(int(distance)),
                                (center),
                                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                fontScale=1,
                                color=(0,0,255),
                                thickness=2)
    return image