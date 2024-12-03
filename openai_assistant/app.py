import os
import time
import chromadb
import streamlit as st
from Ingestion.ingestion import Ingestion
from assistant_manager import AssistantManager

from dotenv import load_dotenv

load_dotenv()
model="gpt-4o-mini"

#Initialize all the session
st.session_state.assistant_id = "asst_G3npumdDzA4B6Dg5ZMwmNa66"
st.session_state.thread_id = "thread_VoQR9qv6D3c4HPSZQXhGXJ4i"
manager = AssistantManager(model, assistant_id=st.session_state.assistant_id, thread_id=st.session_state.thread_id)
if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "file_path" not in st.session_state:
    st.session_state.file_path = None

if "index_name" not in st.session_state:
    st.session_state.index_name = "RISK_AND_POLICY"
# Set up our front end page
st.set_page_config(page_title="Knowledgebase OpenAI Assistant", page_icon=":books:")

# === Sidebar - where users can upload files
file_uploaded = st.sidebar.file_uploader(
    "Upload a zip file along with meta to be transformed into embeddings", key="file_upload", type=["zip"]
)

# Upload file button - store the file ID
if st.sidebar.button("Upload File"):
    if file_uploaded:

        # Create a file path to store the uploaded zip
        file_path = os.path.join("Dataset", file_uploaded.name)

        with open(f"{file_path}", "wb") as f:
            f.write(file_uploaded.getbuffer())
       
        st.session_state.file_path = file_path
        # call the ingestion/vecor store
        collection_name = st.session_state.index_name
        chroma_path = "Chroma_Path"
        ingestion = Ingestion(file_path, collection_name, chroma_path)
        ingestion.run()

        st.write("Ingested succesfull")

        

# Button to initiate the chat session
if st.sidebar.button("Start Chatting..."):

    client = chromadb.PersistentClient(path="Chroma_Path")
    collection_name = st.session_state.index_name
    collection = client.get_collection(name=collection_name)
    print(collection)
    if collection:
        st.session_state.file_path = "Dataset"
    
    if st.session_state.file_path:
        st.session_state.start_chat = True

        
        # Create a new assistant for this chat session

        if not st.session_state.assistant_id:
            assistant_id = manager.create_assistant( 
                name="Policy Assistant",
                instructions="""You are a helpful Policies assistant who knows a lot about understanding Policies and instructions.
                Your role is to summarize polices, clarify terminology within context, and extract key figures and data.
                Cross-reference information for additional insights and answer related questions comprehensively.
                Respond to queries effectively, incorporating feedback to enhance your accuracy.
                Your ultimate goal is to facilitate a deeper understanding of policies and instructions, making it more accessible and comprehensible.""",
                tools=
                [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_relevant_chunks",
                            "description": "Gets the list of policies and instructions.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "User query to required fetch the policies and instructions"
                                    }
                                },
                                "required": ["query"]
                            }
                        }
                    }
                ],
            )

            st.session_state.assistant_id = assistant_id

            print("Assistant id:", assistant_id)

        # Create a new thread for this chat session

        if not st.session_state.thread_id:
            thread_id = manager.create_thread()
            st.session_state.thread_id = thread_id
            print("Thread ID:", thread_id)
    else:
        st.sidebar.warning(
            "No files found. Please upload at least one file to get started."
        )

# the main interface ...
st.title("Knowledgebase OpenAI Assistant")
st.write("Learn fast by chatting with your documents")

# Check sessions
if st.session_state.start_chat:
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4o-mini"
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show existing messages if any...
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # chat input for the user
    if prompt := st.chat_input("What's new?"):
        # Add user message to the state and display on the screen
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # add the user's message to the existing thread

        manager.add_message_to_thread(role="user", content=prompt)
        
        # # Create a run with additioal instructions
        manager.run_assistant(instructions= """Please answer the questions using the knowledge provided in the files.
                              when adding additional information, make sure to distinguish it with bold or underlined text.""")
        

        # Show a spinner while the assistant is thinking...
        with st.spinner("Wait... Generating response..."):

            response = manager.wait_for_completion()

            st.session_state.messages.append(
                {"role": "assistant", "content": response}
                )
            with st.chat_message("assistant"):
                st.markdown(response, unsafe_allow_html=True)

    else:
        # Promopt users to start chat
        st.write(
            "Please upload at least a file to get started by clicking on the 'Start Chat' button"
        )