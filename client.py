# client.py
import requests

def call_typescript_service():
    """
    Sends an HTTP POST request to the local TypeScript microservice 
    and returns the final API response.
    """
    url = "http://localhost:5000/api/completions"
    
    try:
        # Sending an empty post because the payload logic is handled inside TS
        response = requests.post(url, json={})
        
        # Raise an exception if the TS server returned an error code (e.g., 500)
        response.raise_for_status() 
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to communicate with TypeScript server: {e}")
        return None

# --- Example Usage ---
if __name__ == "__main__":
    print("Sending request to local TypeScript service...")
    data = call_typescript_service()
    
    if data:
        print("Successfully received data from TypeScript!")
        # Access elements just like regular Python dictionaries
        print(data)