import requests


def get_ec2_hostname():
    ipconfig = "http://169.254.169.254/latest/meta-data/local-ipv4"
    try:
        return requests.get(ipconfig, timeout=10).text
    except requests.RequestException:
        print("Could not establish EC2 host name.")
        return None
