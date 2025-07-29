import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import json # Import thư viện json để xử lý Block Kit UI

# Load environment variables from .env file
load_dotenv()

# Initialize the Bolt app with tokens and signing secret
# socket_mode=True allows the bot to run locally without a public URL
# app_token is required when socket_mode=True
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"), # Bot Token (xoxb-...)
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET") # Secret for verifying requests from Slack
)

# --- Bot Event Handlers ---

# 1. Handle app_mention event (@MyFirstSlackBot hello)
# 'app_mention' is the event type when the bot is mentioned in a channel or group message
@app.event("app_mention")
def handle_app_mentions(body, say, logger):
    # body: Dictionary containing detailed information about the event (message, sender, channel, etc.)
    # say: Utility function to send a message back to the channel/DM where the event occurred
    # logger: Logger object for logging (useful for debugging)

    logger.info(f"Received app_mention event: {body}") # Log the entire event for debugging
    user = body["event"]["user"] # ID of the user who mentioned the bot
    message_text = body["event"]["text"] # Message content

    # Send a response message
    say(f"Chào <@{user}>! Bạn đã nhắc đến tôi với nội dung: \"{message_text}\".")

# 2. Handle specific messages (when the message contains the keyword "xin chào")
# 'message' is the event type for new messages
# "xin chào" is the keyword the bot will listen for
@app.message("xin chào")
def message_hello(message, say):
    # message: Dictionary containing detailed information about the message
    # say: Utility function to send a response message

    user = message["user"] # ID of the message sender
    say(f"Chào <@{user}>! Rất vui được gặp bạn.")

# 3. Handle Slash Command
# To use this command, you need to configure it in your Slack app
# (Slack App Settings -> Features -> Slash Commands -> Create New Command)
# - Command: /hello-bot
# - Request URL: (Leave empty if using Socket Mode)
# - Short description: Say hello to the bot
# - Usage hint: <your_name>
@app.command("/hello-bot")
def handle_hello_bot_command(ack, respond, command, logger):
    # ack(): Acknowledge to Slack that the bot has received the command and is processing it
    # respond(): Send a response back to the user who typed the command (can be public or private)
    # command: Dictionary containing detailed information about the command (command name, accompanying text)

    ack() # Always call ack() first to prevent Slack from reporting a "timeout" error

    logger.info(f"Received /hello-bot command: {command}") # Log the command for debugging

    user_name = command["text"] if command["text"] else 'bạn' # Get the accompanying text, or default to 'bạn'
    respond(f"Xin chào {user_name}! Tôi là bot của bạn. Rất vui được gặp!")

# 4. Handle user interaction (e.g., button click)
# We need an action_id to identify which button was clicked
# action_id: "my_button_click"
@app.action("my_button_click")
def handle_button_click(ack, body, say, logger):
    # ack(): Acknowledge to Slack that the bot has received the interaction and is processing it
    # body: Dictionary containing detailed information about the interaction (user, original message, button value)

    ack() # Always call ack() first

    logger.info(f"Received button interaction: {body}") # Log the interaction for debugging

    user = body["user"]["id"] # ID of the user who clicked the button
    button_value = body["actions"][0]["value"] # Value of the button defined

    say(f"Cảm ơn <@{user}> đã nhấp vào nút! Giá trị nút là: `{button_value}`")

# Example of sending a message with a button
@app.message("hiển thị nút")
def show_button(say):
    say(
        text='Đây là tin nhắn fallback nếu client không hỗ trợ blocks.', # Fallback text
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Nhấp vào nút bên dưới để tương tác với tôi:"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Nhấp vào đây!",
                            "emoji": True
                        },
                        "style": "primary", # Button style (primary/danger)
                        "value": "button_was_clicked", # Value to be sent when the button is clicked
                        "action_id": "my_button_click" # Unique ID to identify this action
                    }
                ]
            }
        ]
    )

# 5. Handle message to show the new request UI
# Thay thế hàm show_new_request_ui
@app.message("hiển thị yêu cầu mới")
def show_new_request_ui(say):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Bạn có một yêu cầu mới:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*<https://example.com/request/123|Fred Enriquez - Yêu cầu thiết bị mới>*"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Loại:*\nMáy tính (laptop)"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Khi nào:*\nĐã gửi ngày 10 tháng 8"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Cập nhật cuối cùng:*\nNgày 10 tháng 3, 2015"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Lý do:*\nTất cả các phím nguyên âm không hoạt động."
                },
                {
                    "type": "mrkdwn",
                    "text": "*Thông số kỹ thuật:*\nCheetah Pro 15 - Nhanh, thực sự nhanh"
                }
            ]
        },
        {"type": "divider"},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Phê duyệt",
                        "emoji": True
                    },
                    "style": "primary",
                    "value": "approve_request_123",
                    "action_id": "approve_request"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Từ chối",
                        "emoji": True
                    },
                    "style": "danger",
                    "value": "deny_request_123",
                    "action_id": "deny_request"
                }
            ]
        }
    ]
    
    say(text="Đây là tin nhắn yêu cầu mới.", blocks=blocks)

# Thêm handler cho message events
@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

# Listeners for the buttons in the new request UI
@app.action("approve_request")
def handle_approve_request(ack, body, say):
    ack()
    user = body["user"]["id"]
    say(f"Yêu cầu của <@{user}> đã được phê duyệt!")

@app.action("deny_request")
def handle_deny_request(ack, body, say):
    ack()
    user = body["user"]["id"]
    say(f"Yêu cầu của <@{user}> đã bị từ chối.")


# --- Start the application ---

# This block ensures the app starts when the script is executed
if __name__ == "__main__":
    # app_token is required for Socket Mode
    app_token = os.environ.get("SLACK_APP_TOKEN")
    if not app_token:
        print("Warning: SLACK_APP_TOKEN is not set. Socket Mode will not work.")
        print("To run Socket Mode, you need to create an App-Level Token and add 'connections:write' scope.")
        print("Please refer to: https://api.slack.com/apis/connections/socket")
        print("Attempting to start in Web/HTTP mode (requires a public URL for Event Subscriptions and Interactivity).")
        # If no app_token, try to start in HTTP mode (requires public URL setup in Slack App settings)
        app.start(port=int(os.environ.get("PORT", 3000)))
    else:
        # Start the app in Socket Mode
        SocketModeHandler(app, app_token).start()
