"""
オウム返し Line Bot
"""

import os


from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage
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
        TextSendMessage(text=input_text+'だみっ')
    )

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

    # メッセージを決める。
    if all_happy(response):
        message = "嬉しそうだみっ！"
    else:
        message = "んーーみ！"

    # 返答を送信する
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)
    )

    # file_pathの画像を削除
    os.remove(file_path)


# 以下、定義
def all_happy(result):
    """ 検出した顔がすべてHAPPYなら、Trueを返す"""
    for detail in result["FaceDetails"]:
        if most_confident_emotion(detail["Emotions"]) != "HAPPY":
            return False
    return True


def most_confident_emotion(emotions):
    """
    もっとも確信度が高い感情を返す
    :param emotions:
    :return:
    """
    max_conf = 0
    result = ""
    for e in emotions:
        if max_conf < e["Confidence"]:
            max_conf = e["Confidence"]
            result = e["Type"]
    return result

