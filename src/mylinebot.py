"""
オウム返し Line Bot
"""

import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage,
)

import boto3

handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))

client = boto3.client('rekognition')

def lambda_handler(event, context):
    headers = event["headers"]
    body = event["body"]

    # get X-Line-Signature header value
    signature = headers['x-line-signature']

    # handle webhook body
    handler.handle(body, signature)

    return {"statusCode": 200, "body": "OK"}


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """ TextMessage handler """
    input_text = event.message.text

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=input_text+'だみっ'))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    # ユーザから送られてきた画像を一時ファイルとして保存
    message_content = line_bot_api.get_message_content(event.message.id)
    file_path = "/tmp/send-image.jpg"
    with open(file_path, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)

    # Rekognition で感情分析する
    with open(file_path, 'rb') as fd:
        send_image_binary = fd.read()
        response = client.detect_faces(Image={"Bytes":send_image_binary},
                                      Attributes=["ALL"])
    print(response)


    # 返答を送信する
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=str(response)[:1000]))

    # file_pathの画像を削除
    os.remove(file_path)
