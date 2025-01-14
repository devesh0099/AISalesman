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

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")
Settings.llm = sambanova.SambanovaLLM()

pc = pinecone.Pinecone(api_key=os.environ.get("PINECONE_API"))

coaching_index = pc.Index("short")
conversation_index = pc.Index("customers")

coaching_store = PineconeVectorStore(coaching_index)
conversation_store = PineconeVectorStore(conversation_index)

coaching_query_engine = VectorStoreIndex.from_vector_store(coaching_store).as_query_engine(similarity_top_k=3)


def load_json(file_path: str):
    with open(file_path, 'r') as file:
        return json.load(file)


def store_conversation(customer_id, message, is_user=True):
    doc = Document(
        text=message,
        metadata={
            "customer_id": customer_id,
            "timestamp": str(time.time()),
            "type": "user" if is_user else "agent"
        }
    )
    conversation_index = VectorStoreIndex.from_vector_store(conversation_store)
    conversation_index.insert(doc)

def get_conversation_context(customer_id, query):
    # Create an embedding for the current query
    query_embedding = Settings.embed_model._embed(query)
    
    # Query the conversation index with the embedding
    query_response = conversation_index.query(
        vector=query_embedding,
        filter={"customer_id": {"$eq": customer_id}},
        top_k=8,  # Fetch more to filter later
        include_metadata=True
    )
    
    # Sort matches based on relevance (similarity score)
    relevant_conversations = sorted(query_response.matches, key=lambda x: x.score, reverse=True)
    
    # Select top N relevant conversations
    top_relevant_conversations = relevant_conversations[:6]
    
    return " ".join(json.loads(m.metadata['_node_content'])["text"] for m in top_relevant_conversations)


def get_examples(stage) -> str:
    match(stage):
        case "greeting":
            greetings = load_json("data/examples_of_stages/greetings.json")
            greeting_texts = [greeting['text'] for greeting in greetings['greetings']]
            array = random.sample(greeting_texts, 2)
            result = f"[{array[0]} or {array[1]}]"
            return result
        case "pitching":
            pitching = load_json("data/examples_of_stages/pitch.json")
            pitching_texts = [pitching_text['text'] for pitching_text in pitching["pitching"]]
            array = random.sample(pitching_texts,2)
            result = f"[{array[0]} or {array[1]}]"
            return result
        case "qualification_questions":
            qualification_questions = load_json("data/examples_of_stages/qualification.json")
            qualification_texts =  [questions['question'] for questions in qualification_questions["qualification"]]
            array = random.sample(qualification_texts,4)
            result = f"[{array[0]} or {array[1]} or {array[2]} or {array[3]}]"
            return result
        case "objection_handling":
            objection_handling = load_json("data/examples_of_stages/objection_handling.json")
            #Skipped for now
        case "closing":
            closing = load_json("data/examples_of_stages/closing.json")
            closing_texts =  [texts['text'] for texts in closing["closing"]]
            array = random.sample(closing_texts,2)
            result = f"[{array[0]} or {array[1]}]"
            return result


def get_coaching_context(query: str):
    response = coaching_index.query(
        vector=Settings.embed_model._embed(query),
        top_k=2,
        include_metadata=True
    )
    
    relevant_docs = sorted(response.matches, key=lambda x: x.score, reverse=True)
    return " ".join(json.loads(m.metadata['_node_content'])["text"] for m in relevant_docs)


def structure_forming(customer_id, query):
    # Initialize stage manager if not already done
    if not hasattr(structure_forming, 'stage_manager'):
        structure_forming.stage_manager = StageManager()

    stage = structure_forming.stage_manager.get_current_stage()

    # GET EXAMPLES
    examples = get_examples(stage)

    # GET LAST RESPONSES
    last_responses = get_conversation_context(customer_id, query)
    store_conversation(customer_id, query, is_user=True)

    # NOW RETRIEVE CONTEXT
    context = get_coaching_context(query)

    s = f"[stage:{stage}, context:{context}, examples:{examples}, last_response:{last_responses}, current_que:{query}]"

    # Get current stage and update based on query
    stage = structure_forming.stage_manager.update_stage(query)

    print("")
    # print(s)
    print("")

    response = Settings.llm.complete(prompt=s)
    store_conversation(customer_id, str(response), is_user=False)
    return response



customer_id = "12312211451234412123454321"
while True:
    query = input("Customer: ")
    response = structure_forming(customer_id, query)
    print("System: " + str(response))


# def main(query):

#     customer_id = str(random.randint(1,1000000000))
#     # print("Customer: "+ query)
#     response = structure_forming(customer_id, query)
#     return response
#     # print("System: " + str(response))