from groq import Groq
from openai import OpenAI
from app.config import settings
from typing import Generator


groq_client = Groq(api_key=settings.GROQ_API_KEY)
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None


def get_response(prompt: str, system_prompt: str = None, model: str = None) -> str:

    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    try:
        response = groq_client.chat.completions.create(
            model=model or "llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content

    except Exception as groq_error:
        print(f"Groq failed: {groq_error}")

        if openai_client:
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2048
                )
                return response.choices[0].message.content

            except Exception as openai_error:
                print(f"OpenAI also failed: {openai_error}")
                return "I apologize, but I'm unable to generate a response at this time. Both LLM providers are currently unavailable."

        return "I apologize, but I'm unable to generate a response at this time. The LLM service is currently unavailable."


def get_response_stream(prompt: str, system_prompt: str = None, model: str = None) -> Generator[str, None, None]:

    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    try:
        stream = groq_client.chat.completions.create(
            model=model or "llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as groq_error:
        print(f"Groq streaming failed: {groq_error}")

        if openai_client:
            try:
                stream = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2048,
                    stream=True
                )

                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

            except Exception as openai_error:
                print(f"OpenAI streaming also failed: {openai_error}")
                yield "I apologize, but I'm unable to generate a response at this time."

        else:
            yield "I apologize, but I'm unable to generate a response at this time. The LLM service is currently unavailable."


def count_tokens_approx(text: str) -> int:

    return len(text) // 4
