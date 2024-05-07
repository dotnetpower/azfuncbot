import azure.functions as func
import logging

# bot 을 위한 참조 패키지 - 시작
import json
from http import HTTPStatus

import aiohttp
from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    ConversationState,
    MemoryStorage,
    UserState,
    MessageFactory,
    TurnContext
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity
from botframework.connector.auth import AuthenticationConfiguration

from authentication import AllowedCallersClaimsValidator
from bots import AoaiBot
from config import DefaultConfig

# from dialogs import ActivityRouterDialog, DialogSkillBotRecognizer
from skill_adapter_with_error_handler import AdapterWithErrorHandler
# bot 을 위한 참조 패키지 - 끝

# application insights 를 위한 코드 - 시작
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.context import attach, detach
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
configure_azure_monitor()
OpenAIInstrumentor().instrument()
# application insights 를 위한 코드 - 끝

# bot 관련 코드 - 시작

CONFIG = DefaultConfig()


# Create MemoryStorage, UserState and ConversationState
MEMORY = MemoryStorage()
USER_STATE = UserState(MEMORY)
CONVERSATION_STATE = ConversationState(MEMORY)

# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
VALIDATOR = AllowedCallersClaimsValidator(CONFIG).claims_validator

SETTINGS = ConfigurationBotFrameworkAuthentication(
    CONFIG,
    auth_configuration=AuthenticationConfiguration(claims_validator=VALIDATOR),
)
ADAPTER = AdapterWithErrorHandler(SETTINGS, CONVERSATION_STATE)

# Create the Bot
BOT = AoaiBot(conversation_state=CONVERSATION_STATE, user_state=USER_STATE, config=CONFIG)
# bot 관련 코드 - 끝



app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="messages")
async def http_trigger(req: func.HttpRequest, context) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # name = req.params.get('name')
    # if not name:
    #     try:
    #         req_body = req.get_json()
    #     except ValueError:
    #         pass
    #     else:
    #         name = req_body.get('name')

    # if name:
    #     return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    # else:
    #     return func.HttpResponse(
    #          "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
    #          status_code=200
    #     )
    
    functions_current_context = {
        "traceparent": context.trace_context.Traceparent,
        "tracestate": context.trace_context.Tracestate
    }
    parent_context = TraceContextTextMapPropagator().extract(
        carrier=functions_current_context
    )
    token = attach(parent_context)
    
    
    # Main bot message handler.
    if "application/json" in req.headers["Content-Type"]:
        body = req.get_json()
    else:
        return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    print(json.dumps(body, indent=4))
    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    invoke_response = await ADAPTER.process_activity(auth_header, activity, BOT.on_turn)
    if invoke_response:
        return json_response(data=invoke_response.body, status=invoke_response.status)
    
    detach(token)
    # return Response(status=HTTPStatus.OK)
    return func.HttpResponse(status_code=HTTPStatus.OK)




# 다른 예제
@app.route(route="messages_inner")
async def messages_inner(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # inner function 으로 처리 할 경우 예제
    async def on_message_activity(turn_context: TurnContext):
        await turn_context.send_activity(MessageFactory.text("test"))
        return Response(body="success", status=HTTPStatus.OK)
        
    # Main bot message handler.
    if "application/json" in req.headers["Content-Type"]:
        body = req.get_json()
    else:
        return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    print(json.dumps(body, indent=4))
    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    invoke_response = await ADAPTER.process_activity(auth_header, activity, on_message_activity)
    if invoke_response:
        return json_response(data=invoke_response.body, status=invoke_response.status)
    
    return func.HttpResponse(status_code=HTTPStatus.OK)