#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

""" Bot Configuration """

class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
    
    ALLOWED_CALLERS = os.environ.get("AllowedCallers", ["*"])
    
    # openai 관련 설정
    # https://github.com/Azure-Samples/function-python-ai-langchain/blob/main/function_app.py
    AZURE_OPENAI_KEY  = os.environ.get("AZURE_OPENAI_KEY", "")
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_VERSION = os.environ.get("AZURE_OPENAI_VERSION", "")
    
    APPLICATIONINSIGHTS_CONNECTION_STRING = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    