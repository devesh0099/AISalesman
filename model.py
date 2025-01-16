from dotenv import load_dotenv
import pinecone
import os
from llama_index.core import VectorStoreIndex, Document
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
import sambanova
import json
import random
import time
from stage_manager import StageManager

load_dotenv()
'''
structure:[stage:,context:,examples:,last_response:,current_que:]
'''

class ConversationState:
    def __init__(self):
        load_dotenv()
        
        # Initialize all the existing components
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")
        Settings.llm = sambanova.SambanovaLLM()
        
        self.pc = pinecone.Pinecone(api_key=os.environ.get("PINECONE_API"))
        self.coaching_index = self.pc.Index("short")
        self.conversation_index = self.pc.Index("customers")
        self.coaching_store = PineconeVectorStore(self.coaching_index)
        self.conversation_store = PineconeVectorStore(self.conversation_index)
        self.coaching_query_engine = VectorStoreIndex.from_vector_store(self.coaching_store).as_query_engine(similarity_top_k=3)
        self.stage_manager = StageManager()
        self.customer_id = str(random.randint(1, 10000000000))

    def load_json(self, file_path: str):
        with open(file_path, 'r') as file:
            return json.load(file)

    def store_conversation(self, message, is_user=True):
        doc = Document(
            text=message,
            metadata={
                "customer_id": self.customer_id,
                "timestamp": str(time.time()),
                "type": "user" if is_user else "agent"
            }
        )
        conversation_index = VectorStoreIndex.from_vector_store(self.conversation_store)
        conversation_index.insert(doc)

    def get_conversation_context(self, query):
        # Create an embedding for the current query
        query_embedding = Settings.embed_model._embed(query)
        
        # Query the conversation index with the embedding
        query_response = self.conversation_index.query(
            vector=query_embedding,
            filter={"customer_id": {"$eq": self.customer_id}},
            top_k=8,  
            include_metadata=True
        )
        
        # Sort matches based on relevance (similarity score)
        relevant_conversations = sorted(query_response.matches, key=lambda x: x.score, reverse=True)
        
        # Select top N relevant conversations
        top_relevant_conversations = relevant_conversations[:6]
        
        return " ".join(json.loads(m.metadata['_node_content'])["text"] for m in top_relevant_conversations)


    def get_examples(self, stage) -> str:
        match(stage):
            case "greeting":
                greetings = self.load_json("data/examples_of_stages/greetings.json")
                greeting_texts = [greeting['text'] for greeting in greetings['greetings']]
                array = random.sample(greeting_texts, 2)
                result = f"[{array[0]} or {array[1]}]"
                return result
            case "pitching":
                pitching = self.load_json("data/examples_of_stages/pitch.json")
                pitching_texts = [pitching_text['text'] for pitching_text in pitching["pitching"]]
                array = random.sample(pitching_texts,2)
                result = f"[{array[0]} or {array[1]}]"
                return result
            case "qualification_questions":
                qualification_questions = self.load_json("data/examples_of_stages/qualification.json")
                qualification_texts =  [questions['question'] for questions in qualification_questions["qualification"]]
                array = random.sample(qualification_texts,4)
                result = f"[{array[0]} or {array[1]} or {array[2]} or {array[3]}]"
                return result
            case "closing":
                closing = self.load_json("data/examples_of_stages/closing.json")
                closing_texts =  [texts['text'] for texts in closing["closing"]]
                array = random.sample(closing_texts,2)
                result = f"[{array[0]} or {array[1]}]"
                return result


    def get_coaching_context(self, query: str):
        response = self.coaching_index.query(
            vector=Settings.embed_model._embed(query),
            top_k=2,
            include_metadata=True
        )
        
        relevant_docs = sorted(response.matches, key=lambda x: x.score, reverse=True)
        return " ".join(json.loads(m.metadata['_node_content'])["text"] for m in relevant_docs)


    def structure_forming(self, query):
        stage = self.stage_manager.get_current_stage()
        examples = self.get_examples(stage)
        last_responses = self.get_conversation_context(query)
        self.store_conversation(query, is_user=True)
        context = self.get_coaching_context(query)
        s = f"[stage:{stage}, context:{context}, examples:{examples}, last_response:{last_responses}, current_que:{query}]"

        # Get current stage and update based on query
        stage = self.stage_manager.update_stage(query)

        print("")
        print(s + " " + self.customer_id)
        print("")

        response = Settings.llm.complete(prompt=s)
        self.store_conversation(str(response), is_user=False)
        return response
    
    def fake_greeting(self):
        self.store_conversation("Hello, who is this speaking?", is_user=True)
        self.name = Settings.llm.return_name()
        self.store_conversation(f"Hello, This is {self.name} speaking from study centre.Do you have a moment?", is_user=True)
        return self.name