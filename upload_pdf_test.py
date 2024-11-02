import requests

# Define the URL endpoint
url = 'http://127.0.0.1:8000/upload-pdf/'  # Replace with your actual endpoint

# Define the file path
file_path = './Mandip_Cv.pdf'

# Open the file in binary mode and send it in a POST request
with open(file_path, 'rb') as file:
    response = requests.post(url, files={'file': file})

# Print the response from the server
print('Status Code:', response.status_code)
print('Response Body:', response.text)
