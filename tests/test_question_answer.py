import asyncio
import json
import pytest
from websockets.client import connect
from fastapi.testclient import TestClient
import pytest_asyncio

from main import app  # Adjust if needed to point to your FastAPI app

# Test data structure
test_questions = [
    {
        "question": "give small summary of pdf content",
        "expected_length": 10  # Minimum expected answer length
    },
    {
        "question": "What is unique about the pdf content?",
        "expected_length": 10
    },
    {
        "question": "List the work experience.",
        "expected_length": 10
    }
]

@pytest.mark.asyncio
async def test_question_answer_websocket():
    async with connect("ws://127.0.0.1:8000/ws/question-answer?user_id=10") as websocket:
            responses = []
            for test_cases in test_questions:
                # Test data for user-specific PDF content (mocked)
                question = test_cases['question']
                print("first phase")
                
                # Send a question to the WebSocket
                await websocket.send(
                    json.dumps({
                        "type": "question",
                        "content": question
                    })
                )
                print("second phase")
                # Receive the response
                response = await websocket.recv()
                response_data = json.loads(response)
                print(response_data)
                responses.append(response_data['content'])
                # Check if response contains actual content or error message
                assert response_data['type'] == 'answer'
                assert isinstance(response_data['content'], str)
                assert len(response_data['content']) > 0
                assert not response_data['content'].startswith('Error generating response')
                await asyncio.sleep(0.5)
                
            # validate responses length
            assert len(responses) == len(test_questions)



# @pytest.mark.asyncio
# async def test_connection_with_invalid_user_id():
#     # Test connection with invalid user_id
#     with pytest.raises(Exception):
#         async with connect("ws://127.0.0.1:8000/ws/question-answer?user_id=invalid") as websocket:
#             pass


# Test timeout scenario
# @pytest.mark.asyncio
# async def test_timeout_handling(websocket_url):
#     async with connect(f"{websocket_url}?user_id=1") as websocket:
#         # Send a question that might take long to process
#         await websocket.send(json.dumps({
#             "type": "question",
#             "content": "Generate a detailed analysis"
#         }))
        
#         try:
#             response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
#             response_data = json.loads(response)
#             assert "answer" in response_data
#         except asyncio.TimeoutError:
#             pytest.fail("Response took too long")