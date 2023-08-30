import asyncio
import base64
import json

import pyaudio
import streamlit as st
import websockets
from rapidfuzz import fuzz
from configure import auth_key, openai_api_key
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.text_splitter import CharacterTextSplitter

# Constants
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

# Audio setup
p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER
)


def start_listening():
    """Activate the listening state."""
    st.session_state['run'] = True
    st.session_state['all'] = []

def stop_listening():
    """Deactivate the listening state."""
    st.session_state['run'] = False


def init_session_state():
    """Initialize Streamlit's session state variables."""
    if 'text' not in st.session_state:
        st.session_state['text'] = 'Listening...'
        st.session_state['run'] = False
        st.session_state['all'] = []


def check_end_problem_definition(text):
    """Check if the user has ended the problem definition based on fuzzy matching."""
    return fuzz.partial_ratio(text.lower(), "let me think")


def summary_last_question_into_topics(dialogs):
    """Summarize the last question into topics based on the dialogue."""
    prompt_template = """Write a summary of all points (in topics) to solve last question (including the problem description) in the following dialogue:
    "{text}"
    TOPICS SUMMARY:"""
    text_splitter = CharacterTextSplitter(        
                    separator="- ",
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len,
                    is_separator_regex=False
    )
    docs = text_splitter.create_documents([" - ".join(dialogs)])
    prompt = PromptTemplate.from_template(prompt_template)
    llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key, model_name="gpt-3.5-turbo-16k")
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    stuff_chain = StuffDocumentsChain(llm_chain=llm_chain)
    return stuff_chain.run(docs)


def code_solving_in_python(description):
    """Generate Python code to solve a problem based on its description."""
    prompt_template = """Given the following high level leetcode problem description, write a short Python code snippet that solves the problem. 
    Also explain the code after. Make the code easier to understand and modulable using PEP8. Problem Description: "{description}" 
    PYTHON CODE IN MARKDOWN:"""
    llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key, model_name="gpt-4")
    code_template = PromptTemplate.from_template(template=prompt_template)
    code_chain = LLMChain(llm=llm, prompt=code_template)
    return code_chain.run({"description": description})


async def send(ws):
    while st.session_state['run']:
        try:
            data = stream.read(FRAMES_PER_BUFFER)
            data_encoded = base64.b64encode(data).decode("utf-8")
            await ws.send(json.dumps({"audio_data": str(data_encoded)}))
            await asyncio.sleep(0.01)
        except (websockets.exceptions.ConnectionClosedError, Exception) as e:
            handle_websocket_exceptions(e)


async def receive(ws):
    while st.session_state['run']:
        try:
            result_str = await ws.recv()
            result = json.loads(result_str)['text']
            if json.loads(result_str)['message_type'] == 'FinalTranscript':
                st.session_state['text'] = result
                if len(result) > 0:
                    st.session_state['all'].append(result)
                if check_end_problem_definition(result) > 90:
                    st.markdown(result)
                    text_question = summary_last_question_into_topics(st.session_state['all'][:-1])
                    st.markdown(code_solving_in_python(text_question))
        except (websockets.exceptions.ConnectionClosedError, Exception) as e:
            handle_websocket_exceptions(e)


def handle_websocket_exceptions(e):
    """Handle exceptions raised during WebSocket communication."""
    if isinstance(e, websockets.exceptions.ConnectionClosedError):
        assert e.code == 4008
    elif isinstance(e, Exception) and hasattr(e, 'errno'):
        if e.errno in [-9981, -9988]:
            asyncio.sleep(0.01)
        else:
            raise


async def main():
    init_session_state()
    st.title('Voice-Driven Code Problem Solver')
    start, stop = st.columns(2)
    start.button('Start listening', on_click=start_listening)
    stop.button('Stop listening', on_click=stop_listening)

    async with websockets.connect(
        URL,
        extra_headers=(("Authorization", auth_key),),
        ping_interval=5,
        ping_timeout=20
    ) as ws:
        await ws.recv()  # Waiting for session to begin
        await asyncio.gather(send(ws), receive(ws))


if __name__ == "__main__":
    asyncio.run(main())

