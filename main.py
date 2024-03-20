from fastapi import FastAPI, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from chatbot import initialize_chatbot, convert_to_langchain_messages
from update_table import (
    store_message,
    get_all_messages_for_chat,
    current_epoch_time,
    decimal_to_float,
)
import logging
import os
import json
from api.audio import (
    get_elevenlabs_audio,
    generate_mp3_file_name,
    upload_audio_bytes_to_s3,
    get_s3_link,
)
from fastapi.encoders import jsonable_encoder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(funcName)s - Line: %(lineno)d",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("my-logger")


class ChatMessagesRequest(BaseModel):
    chat_id: str


class ChatRequest(BaseModel):
    # NOTE: show that if you pass a messagee, it will give a 422 error
    # NOTE: this should match the parameters in the frontned request body.
    chat_id: str
    timestamp: int
    message: str
    model: str
    prompt_template: str
    temperature: float = 0.2  # default value if not provided


app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    # vercel
    "https://kitsune-ai.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow access from origins defined in the list
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/chat")
def get_chat_response(chat_request: ChatRequest):
    try:
        store_message(
            chat_id=chat_request.chat_id,
            timestamp=chat_request.timestamp,
            message=chat_request.message,
            message_type="user",
            audio_file_url=None,
        )

        messages = get_all_messages_for_chat(chat_request.chat_id)

        langchain_messages = convert_to_langchain_messages(messages)

        logging.info("DynamoDB Chat History %s", messages)
        logging.info("LangChain Messages %s", langchain_messages)

        chatbot = initialize_chatbot(
            model_name=chat_request.model,
            temperature=chat_request.temperature,
            prompt_template=chat_request.prompt_template,
            message_history=langchain_messages,
        )
        logging.info(f"Received request: {chat_request}")

        logging.info(f"INVOKING CHATBOT")
        result = chatbot.invoke(
            {"history": langchain_messages, "input": chat_request.message}
        )

        bot_response = result.get("response")

        logging.info(bot_response)

        if bot_response:
            # pass the message back immediately
            bot_timestamp = current_epoch_time()
            store_message(
                chat_id=chat_request.chat_id,
                timestamp=bot_timestamp,
                message=bot_response,
                message_type="ai",
                audio_file_url=None,
            )

            bot_audio = get_elevenlabs_audio(bot_response)
            print(f"Type of audio: {type(bot_audio)}")
            if bot_audio and isinstance(bot_audio, bytes):
                # Proceed with uploading to S3
                s3_file_name = generate_mp3_file_name()
                print(f"s3 file name: {s3_file_name}")
                # ChatID
                upload_status = upload_audio_bytes_to_s3(
                    audio_content=bot_audio,
                    bucket="hippo-ai-audio",
                    object_name=s3_file_name,
                    metadata={
                        "ContentType": "audio/mpeg",
                        "x-amz-meta-chatid": chat_request.chat_id,
                        # TROUBLESHOOTING: this has to be a string
                        "x-amz-meta-timestamp": str(bot_timestamp),
                    },
                )
                # TODO - create a new bucket for this project.
                if upload_status:
                    bot_response_audio = get_s3_link(
                        file_name=s3_file_name, bucket_name="hippo-ai-audio"
                    )
                else:
                    bot_response_audio = None

                response_content = {
                    "data": result,
                    "audio_s3_upload": upload_status,
                    "audio_link": bot_response_audio,
                    "audio_file_name": s3_file_name,
                }
            else:
                print("The response content is not bytes.")
                response_content = {
                    "data": result,
                }

        response = JSONResponse(
            content=response_content, status_code=status.HTTP_200_OK
        )

        logging.info(response)

        return response
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return JSONResponse(
            content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.post("/chat/messages")
def get_chat_messages(messages_request: ChatMessagesRequest):
    print(f" received messages request: {messages_request}")
    messages = get_all_messages_for_chat(messages_request.chat_id)
    # Convert messages to JSON serializable format using jsonable_encoder
    messages_json = jsonable_encoder(messages)
    logging.info(f"messages: {messages_json}")
    return JSONResponse(content={"data": messages_json}, status_code=status.HTTP_200_OK)


"""
Start the app using:
```
uvicorn main:app --reload
```
"""
