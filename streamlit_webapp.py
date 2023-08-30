import streamlit as st
import websockets
import asyncio
import base64
import json
from configure import auth_key, openai_api_key
from rapidfuzz import fuzz
import pyaudio
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.text_splitter import CharacterTextSplitter


if 'text' not in st.session_state:
	st.session_state['text'] = 'Listening...'
	st.session_state['run'] = False

 
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()
 
# starts recording
stream = p.open(
   format=FORMAT,
   channels=CHANNELS,
   rate=RATE,
   input=True,
   frames_per_buffer=FRAMES_PER_BUFFER
)

def start_listening():
	st.session_state['run'] = True
	st.session_state['all'] = list()

def stop_listening():
	st.session_state['run'] = False

def check_end_problem_definition(text):
	return fuzz.partial_ratio(text.lower(), "let me think")

def summary_last_question_into_topics(dialogs):
	# Define prompt
	prompt_template = """Write a summary of all points (in topics) to solve last question (including the problem description) in the following dialogue:
	"{text}"
	TOPICS SUMMARY:"""
	text_splitter = CharacterTextSplitter(        
    				separator = "- ",
    				chunk_size = 1000,
    				chunk_overlap  = 200,
    				length_function = len,
    				is_separator_regex = False,
	)
	docs = text_splitter.create_documents([" - ".join(dialogs)])
	prompt = PromptTemplate.from_template(prompt_template)
	# Define LLM chain
	llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key,
		model_name="gpt-3.5-turbo-16k")
	llm_chain = LLMChain(llm=llm, prompt=prompt)

	# Define StuffDocumentsChain
	stuff_chain = StuffDocumentsChain(
    	llm_chain=llm_chain,
	)
	return stuff_chain.run(docs)

def code_solving_in_python(description):
	prompt_template = """Given the following high level leetcode problem description, write a short Python code snippet that solves the problem. 
	Also explain the code after. Make the code easier to understand and modulable using PEP8. Problem Description: "{description}" 
	PYTHON CODE IN MARKDOWN: """
	# Create a chain that generates the code
	llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key,
		model_name="gpt-4")
	code_template = PromptTemplate.from_template(template=prompt_template)
	code_chain = LLMChain(llm=llm, prompt=code_template)
	return code_chain.run({"description": description})

st.title('Get real-time transcription')

start, stop = st.columns(2)
start.button('Start listening', on_click=start_listening)

stop.button('Stop listening', on_click=stop_listening)

URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"
 

async def send_receive():
	
	print(f'Connecting websocket to url ${URL}')

	async with websockets.connect(
		URL,
		extra_headers=(("Authorization", auth_key),),
		ping_interval=5,
		ping_timeout=20
	) as _ws:

		r = await asyncio.sleep(0.1)
		print("Receiving SessionBegins ...")

		session_begins = await _ws.recv()
		print(session_begins)
		print("Sending messages ...")


		async def send():
			while st.session_state['run']:
				try:
					data = stream.read(FRAMES_PER_BUFFER)
					data = base64.b64encode(data).decode("utf-8")
					json_data = json.dumps({"audio_data":str(data)})
					r = await _ws.send(json_data)

				except websockets.exceptions.ConnectionClosedError as e:
					assert e.code == 4008
					break

				except Exception as e:
					if e.errno == -9981 or e.errno == -9988:
						await asyncio.sleep(0.01)
						continue
					else:
						raise  # If it's a different OSError, raise it
						assert False, "Not a websocket 4008 error"

				r = await asyncio.sleep(0.01)


		async def receive():
			while st.session_state['run']:
				try:
					result_str = await _ws.recv()
					result = json.loads(result_str)['text']

					if json.loads(result_str)['message_type']=='FinalTranscript':
						print(result)
						st.session_state['text'] = result
						if len(result) > 0:
							st.session_state['all'].append(result)
							print(check_end_problem_definition(result))
						if check_end_problem_definition(result)>90:
							st.markdown(result)
							text_question = summary_last_question_into_topics(st.session_state['all'][:-1])
							st.markdown(code_solving_in_python(text_question))

				except websockets.exceptions.ConnectionClosedError as e:
					print(e)
					assert e.code == 4008
					break

				except Exception as e:
					if e.errno == -9981:
						print("Audio input overflowed. Skipping this chunk.")
						await asyncio.sleep(0.01)
						continue
					raise
					assert False, "Not a websocket 4008 error"
			
		send_result, receive_result = await asyncio.gather(send(), receive())


asyncio.run(send_receive())