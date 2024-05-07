# https://github.com/microsoft/BotBuilder-Samples/blob/main/samples/python/80.skills-simple-bot-to-bot/echo-skill-bot/bots/echo_bot.py
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# teams 관련 추가 내용이 필요한 경우 아래 링크 참조.
# https://github.com/OfficeDev/Microsoft-Teams-Samples/blob/main/samples/bot-conversation/python/bots/teams_conversation_bot.py

import re
import time
from botbuilder.core import ActivityHandler, MessageFactory, TurnContext, ConversationState, UserState
from botbuilder.schema import Activity, ActivityTypes, EndOfConversationCodes, ConversationParameters, ConversationAccount, ChannelAccount
from botbuilder.core.teams import TeamsActivityHandler, TeamsInfo
from config import DefaultConfig

# openai 필요 패키지
# import openai
from openai import AsyncAzureOpenAI
# from langchain.prompts import PromptTemplate
# from langchain.llms import OpenAI
# from langchain.llms.openai import AzureOpenAI

# 한글 맞춤법 교정
# from pykospacing import Spacing

# application insights
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace


class AoaiBot(ActivityHandler):
    def __init__(self, conversation_state: ConversationState, user_state: UserState, config: DefaultConfig):
        self.conversation_references = {}
        self.conversation_state = conversation_state
        self.user_state = user_state
        # self.ko_spacing = Spacing()
        
        self.openai_client = AsyncAzureOpenAI(
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_KEY,
            api_version=config.AZURE_OPENAI_VERSION
        )
        
        self.tracer = trace.get_tracer(__name__)
        
        # self.openai = openai
        # self.openai.api_key = config.AZURE_OPENAI_KEY
        # self.openai.azure_endpoint = config.AZURE_OPENAI_ENDPOINT
        # self.openai.api_type = 'azure'
        # self.openai.api_version = config.AZURE_OPENAI_VERSION
        
    
    async def on_message_activity(self, turn_context: TurnContext):
        
        with self.tracer.start_as_current_span("on_message_activity"):
            message_text = [{"role":"system", "content":"You are an AI assistant that helps people find information"},
                            {"role":"user", "content":turn_context.activity.text}]
            
            # https://cookbook.openai.com/examples/how_to_stream_completions
            
            start_time = time.time()
            completion = await self.openai_client.chat.completions.create(
                
                model = "gpt-35-turbo",
                messages = message_text,
                temperature=0.7,
                max_tokens=800,
                # top_p=0.95,
                # frequency_penalty=0,
                # presence_penalty=0,
                # stop=["\n"],
                stream=True
            )
            
            bot_message = ""
            new_activity_id = None
            is_first = False
            
            # create variables to collect the stream of chunks
            collected_chunks = []
            collected_messages = []
            
            chunk_size = 0
            # iterate through the stream of events
            
            with self.tracer.start_as_current_span("message_chunking") as span:
                async for chunk in completion:
                    if len(chunk.choices) == 0:
                        continue
                    
                    chunk_time = time.time() - start_time  # calculate the time delay of the chunk
                    collected_chunks.append(chunk)  # save the event response
                    chunk_message = chunk.choices[0].delta.content  # extract the message
                    
                    if chunk_message is None or chunk_message == "":
                        continue
                    
                    print(f"chunk_message: {chunk_message}")
                    
                    collected_messages.append(chunk_message)  # save the message
                    print(f"Message received {chunk_time:.2f} seconds after request: {chunk_message}") 
                    
                    # 한글의 경우 자소단위로 올수도 있기 때문에 띄어쓰기가 발생되므로...
                    if len(chunk_message) == 1 or chunk_message.isalpha():
                        bot_message += chunk_message
                    else:
                        bot_message += chunk_message if bot_message == "" else " " + chunk_message 
                    
                    # bot_message = bot_message.replace(" ", "")
                    # bot_message = self.ko_spacing(bot_message)
                    
                    # 특수 문자의 경우 공백을 주기 위함
                    bot_message = re.sub(r'(?<=[\.\!\?])(?=[^\s])', r' ', bot_message)
                    
                    span.add_event("message", { "bot_message":bot_message })
                    
                    if not is_first:
                        is_first = True
                        activity = await turn_context.send_activity(MessageFactory.text(bot_message))
                        new_activity_id = activity.id
                        turn_context.activity.id = new_activity_id
                    else:
                        activity = MessageFactory.text(bot_message)
                        activity.id = new_activity_id
                        await turn_context.update_activity(activity)
                
