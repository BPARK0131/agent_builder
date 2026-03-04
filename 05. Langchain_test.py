import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

load_dotenv()
MODEL_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT")
API_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

llm = AzureChatOpenAI(
    azure_deployment=MODEL_DEPLOYMENT_NAME,
    api_key=API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    api_version=API_VERSION,
    temperature=0,
)
messages = [
         SystemMessage(content='당신은 업무 계획을 세워주는 업무 플래너 머신입니다. 사용자의 업무를 입력 받으면 이를 위한 계획을 작성합니다.'),     
         HumanMessage(content='신입사원 교육을 해야됩니다.') 
]  
#response = llm.invoke(messages)
#print(response.content)


from langchain_community.document_loaders import PyPDFLoader

_script_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(_script_dir, "Owners_Manual.pdf")
loader = PyPDFLoader(pdf_path) 
pages = loader.load_and_split()
print(pages[103].page_content)