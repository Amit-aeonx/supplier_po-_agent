"""
LangChain LLM Configuration for AWS Bedrock
"""
import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrock

load_dotenv()

def get_llm():
    """Initialize and return ChatBedrock LLM"""
    return ChatBedrock(
        model_id=os.getenv("CLAUDE_SONNET_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        credentials_profile_name=None,  # Uses default credentials
        model_kwargs={
            "max_tokens": 4096,
            "temperature": 0.1
        }
    )

def get_llm_with_credentials():
    """Initialize ChatBedrock with explicit AWS credentials"""
    import boto3
    
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY")
    )
    
    # Use the base model ID without ARN for LangChain
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    return ChatBedrock(
        model_id=model_id,
        client=bedrock_client,
        model_kwargs={
            "max_tokens": 4096,
            "temperature": 0.1
        }
    )
