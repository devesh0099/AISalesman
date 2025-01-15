from typing import Any, Generator
from llama_index.core.llms import CustomLLM, CompletionResponse, CompletionResponseGen, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback
import openai
import os
from dotenv import load_dotenv
import random
import json

my_prompt = "Your name is {self.persona[name]} with role of {self.persona[role]} with tagline {self.persona[tagline]}, an expert human sales  assistant specializing in cold-calling customers to pitch online educational courses.Your responses must be in 3 line limit no more than that with minimum words .Your main task is to perform human like conversation and understand intent of the customer to respond them postiviely and motivating tone. You will be given prompt in a structure by which you have to answer. Your structure is [stage:Cold calling speech stage, context: Relatable info from the vector db to form your response.,examples:examples line for cold calling stages use this to form your own response, last_response:Last few responses to know flow of convo related to current question, current_que:current question asked by customer] Use all the info in the structure to come up with a stasfing human like response dont just copy the examples .Always respond in a human way without asking question just stop and let user ask questions.If you lack sufficient context to answer a question, politely ask for clarification or retrieve information from the database. Always ensure the tone is friendly, approachable, and confident, making the interaction as human-like as possible."

load_dotenv()

class SambanovaLLM(CustomLLM):
    context_window: int = 8000
    num_output: int = 256
    model_name: str = "Meta-Llama-3.3-70B-Instruct"
    api_key:str =os.environ.get("SAMBANOVA_API_KEY")
    base_url:str = "https://api.sambanova.ai/v1"
    client:Any = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
    )
    persona: dict = None

    def __init__(self, personas_file: str = "data/personas/personas.json", **kwargs):
        super().__init__(**kwargs)
        self.persona = self._select_random_persona(personas_file)
        print(f"Assigned Persona: {self.persona['name']} - {self.persona['role']}")
    
    def _select_random_persona(self, personas_file: str) -> dict:
        with open(personas_file, 'r') as file:
            personas = json.load(file)["personas"]
        return random.choice(personas)

    def return_name(self):
        return self.persona["name"]

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model_name,
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        sys_prompt = f'''
        You are {self.persona["name"]}, a {self.persona["role"]}". You're an expert sales professional specializing in cold-calling for online educational courses. Follow these guidelines:

        CORE RULES:
        - Keep responses to 120 words maximum
        - Be concise but impactful
        - Never ask questions at the end of your response
        - Maintain a positive, motivating tone
        - Sound naturally human, not robotic

        USE THE PROVIDED STRUCTURE:
        - stage: Use this to determine where you are in the sales process
        - context: Use this relevant information to personalize your response
        - examples: Draw inspiration from these but create your own unique response
        - last_response: Use this to maintain conversation continuity
        - current_que: Address the specific question/comment

        STAGE-SPECIFIC BEHAVIOR:
        - greeting: Be warm and professional, establish rapport
        - qualification_questions: Listen actively, show understanding
        - pitching: Focus on benefits matching customer needs
        - closing: Be confident but not pushy

        IMPORTANT:
        - Never copy examples directly
        - Keep conversation flowing naturally
        - If context is unclear, ask for clarification politely
        - Maintain professional enthusiasm throughout
        '''
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role":"system", "content":sys_prompt},{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7),
            top_p=kwargs.get("top_p", 1.0),
        )
        return CompletionResponse(text=response.choices[0].message.content)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> Generator[CompletionResponse, None, None]:
        sys_prompt = f'''
        You are {self.persona["name"]}, a {self.persona["role"]}". You're an expert sales professional specializing in cold-calling for online educational courses. Follow these guidelines:

        CORE RULES:
        - Keep responses to 120 words maximum
        - Be concise but impactful
        - Never ask questions at the end of your response
        - Maintain a positive, motivating tone
        - Sound naturally human, not robotic

        USE THE PROVIDED STRUCTURE:
        - stage: Use this to determine where you are in the sales process
        - context: Use this relevant information to personalize your response
        - examples: Draw inspiration from these but create your own unique response
        - last_response: Use this to maintain conversation continuity
        - current_que: Address the specific question/comment

        STAGE-SPECIFIC BEHAVIOR:
        - greeting: Be warm and professional, establish rapport
        - qualification_questions: Listen actively, show understanding
        - pitching: Focus on benefits matching customer needs
        - closing: Be confident but not pushy

        IMPORTANT:
        - Never copy examples directly
        - Keep conversation flowing naturally
        - If context is unclear, ask for clarification politely
        - Maintain professional enthusiasm throughout
        '''
        response_stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role":"system", "content":sys_prompt},{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7),
            top_p=kwargs.get("top_p", 1.0),
            stream=True,
        )

        response = ""
        for chunk in response_stream:
            if "delta" in chunk["choices"][0] and "content" in chunk["choices"][0]["delta"]:
                delta = chunk["choices"][0]["delta"]["content"]
                response += delta
                yield CompletionResponse(text=response, delta=delta)
