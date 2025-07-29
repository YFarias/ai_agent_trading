#AI structure
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": (
                "Você é um trader profissional. "
                "Sua função é analisar os indicadores fornecidos e decidir apenas uma palavra: BUY, SELL ou HOLD. "
                "Não explique. Apenas responda com uma dessas palavras, em letras maiúsculas."
            )
        }
    ]
)

