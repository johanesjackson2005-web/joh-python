import os
import requests

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

def send_otp_email(email, otp):

    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "personalizations": [
                    {
                        "to": [{"email": email}]
                    }
                ],
                "from": {
                    "email": "johanesjackson2005@gmail.com"
                },
                "subject": "Password Reset OTP",
                "content": [
                    {
                        "type": "text/plain",
                        "value": f"Your OTP is: {otp}"
                    }
                ]
            },
            timeout=10
        )

        print("SendGrid Status:", response.status_code)
        print("SendGrid Response:", response.text)

        return response.status_code == 202

    except Exception as e:
        print("SendGrid Error:", str(e))
        return False