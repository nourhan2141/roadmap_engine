import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from groq import Groq
from roadmap_engine.config import settings

sys.stdout.reconfigure(encoding='utf-8')

def main():
    if not settings.groq_api_key or settings.groq_api_key == "placeholder_key" or settings.groq_api_key == "your_key_here":
        print("Please set your GROQ_API_KEY in the .env file")
        return
        
    client = Groq(api_key=settings.groq_api_key)
    
    schema = {
        "type": "object", 
        "properties": {
            "greeting": {"type": "string"}
        },
        "required": ["greeting"], 
        "additionalProperties": False
    }

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": "Please greet me."
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "test",
                    "strict": True,
                    "schema": schema
                }
            }
        )
        
        print("RAW RESPONSE:")
        print(completion.choices[0].message.content)
        
    except Exception as e:
        print("API Call failed:", str(e))

if __name__ == "__main__":
    main()
