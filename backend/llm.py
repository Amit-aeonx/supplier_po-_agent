import os
import boto3
import json
from dotenv import load_dotenv

load_dotenv()

class BedrockLLM:
    def __init__(self):
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("AWS_SECRET_KEY")
        )
        self.model_id = os.getenv("CLAUDE_SONNET_MODEL_ID")

    def invoke(self, prompt: str) -> str:
        """Invoke Claude Sonnet with a prompt"""
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1
        }
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload)
            )
            
            result = json.loads(response.get("body").read())
            return result.get("content")[0].get("text")
            
        except Exception as e:
            print(f"❌ Bedrock Error: {e}")
            return f"Error: {str(e)}"

def get_llm():
    return BedrockLLM()

if __name__ == "__main__":
    llm = get_llm()
    print(llm.invoke("Hello! Say 'Bedrock is working'"))
