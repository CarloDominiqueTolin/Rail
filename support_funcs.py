import random
import math
import socket
import qrcode
import base64
from io import BytesIO

def generate_qr_code(link):
    qr = qrcode.QRCode(box_size=10, border=5)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    encoded_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded_img}"


def get_local_wlan_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Doesn't need to connect to a real server, just needs an accessible IP
        s.connect(("8.8.8.8", 80))
        
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Error: {e}")
        return None
    

def getCurentLoc(
        center_lat=14.621565284493693, 
        center_lon=121.05015539180206, 
        radius_km=0.5
    ):
    """
    Generate a random GPS location around a given central point within a specified radius.

    Parameters:
        center_lat (float): Latitude of the central point.
        center_lon (float): Longitude of the central point.
        radius_km (float): Radius around the central point in kilometers.

    Returns:
        tuple: A tuple containing random latitude and longitude (lat, lon).
    """
    # Convert radius from kilometers to degrees
    radius_deg = radius_km / 111  # Approximation (1 degree latitude ~ 111 km)

    # Generate random angle and distance
    angle = random.uniform(0, 2 * math.pi)  # Random angle in radians
    distance = random.uniform(0, radius_deg)  # Random distance within radius

    # Calculate random latitude and longitude
    delta_lat = distance * math.cos(angle)
    delta_lon = distance * math.sin(angle) / math.cos(math.radians(center_lat))  # Adjust for longitude convergence

    random_lat = center_lat + delta_lat
    random_lon = center_lon + delta_lon

    return (random_lat, random_lon)

if __name__ == "__main__":
    random_location = getCurentLoc()
    print(f"Random GPS Location: Latitude={random_location[0]}, Longitude={random_location[1]}")
    print(get_local_wlan_address())