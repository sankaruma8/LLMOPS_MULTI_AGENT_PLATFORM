from groq import Groq
from app.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

def get_response(user_message: str):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    return response.choices[0].message.content