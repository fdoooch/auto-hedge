from urllib.request import urlopen

def get_external_ip():
    response = urlopen('https://api.ipify.org')
    return response.read().decode('utf-8')
