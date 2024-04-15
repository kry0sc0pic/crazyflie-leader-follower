import requests

def send_reqs():
    # Takeoff
    height = 1.7
    response = requests.post("http://localhost:8000/takeoff", json={
        "height": height
    }

    )
    print(response.json())

    # Set position
    position = {
        "x": 0,
        "y": 0,
        "z": 0,
        "yaw": 0
    }
    response = requests.post("http://localhost:8000/setpos", json=position)
    print(response.json())

    # Land
    response = requests.post("http://localhost:8000/land")
    print(response.json())


    # Shutdown
    response = requests.post("http://localhost:8000/shutdown")
    print(response.json())

if __name__ == "__main__":
    send_reqs()