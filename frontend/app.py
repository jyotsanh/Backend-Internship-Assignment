import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import requests
import websockets
import json
import asyncio

# deployed
url = 'https://backend-internship-assignment.onrender.com' 
WS_URL = "wss://backend-internship-assignment.onrender.com/ws/question-answer"

# local
local_URL = "http://127.0.0.1:8000"
local_WS_URL = "ws://127.0.0.1:8000/ws/question-answer"

with st.sidebar:
    st.title('PDF Reader')
    st.markdown('''
                ## LLM powered chatbot
                ''')
    
    add_vertical_space(5)
    st.write("made for backend assignment project")

def main():
    st.header("Chat with your PDF")
    st.subheader('Upload your PDF here')

    # Initialize session state for chat
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'ws_connected' not in st.session_state:
        st.session_state.ws_connected = False
    
    pdf_file = st.file_uploader("Choose a file", type="pdf")
    
    # Add upload button
    if pdf_file is not None:
        if st.button("Upload PDF"):
            response = requests.post(f"{local_URL}/upload-pdf/", files={"file": pdf_file})
            # Print the response from the server
            if response.status_code == 200:
                st.write("Successfully completed")
                st.session_state.ws_connected = True
                # Clear previous messages when new PDF is uploaded
                st.session_state.messages = []
            else:
                st.write("Upload Failed")

    # Show chat interface after successful PDF upload
    if st.session_state.ws_connected:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask a question about your PDF"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Create a placeholder for the assistant's response
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                with st.spinner("Thinking..."):  # Add a spinner while waiting
                    # Send message to WebSocket and get response
                    async def send_message():
                        try:
                            async with websockets.connect(
                                f"{local_WS_URL}?user_id=101",
                                ping_interval=None,  # Disable ping to prevent timeouts
                                ping_timeout=None,   # Disable ping timeout
                                close_timeout=300,   # 5 minutes timeout for closing
                                max_size=None,      # No limit on message size
                            ) as websocket:
                                # Set the timeout for receiving messages
                                websocket.max_size = 2 ** 27  # Increase max message size if needed
                                
                                await websocket.send(json.dumps({
                                    "type": "question",
                                    "content": prompt
                                }))
                                
                                # Use asyncio.wait_for to set a timeout
                                response = await asyncio.wait_for(
                                    websocket.recv(),
                                    timeout=300  # 5 minutes timeout
                                )
                                return json.loads(response)
                        except asyncio.TimeoutError:
                            return {"content": "Response timed out. Please try again."}
                        except Exception as e:
                            return {"content": f"An error occurred: {str(e)}"}

                    # Run the async function
                    response = asyncio.run(send_message())
                    
                    # Display assistant response
                    response_placeholder.markdown(response["content"])
                    
            st.session_state.messages.append({"role": "assistant", "content": response["content"]})

if __name__ == '__main__':
    main()