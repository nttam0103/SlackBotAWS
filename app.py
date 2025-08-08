import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from handlers import register_all_handlers

load_dotenv()

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

@app.command("/hello-bot")
def handle_hello_bot_command(ack, respond, command, logger):
    ack() 
    logger.info(f"Received /hello-bot command: {command}") 

    user_name = command["text"] if command["text"] else 'bạn' #
    respond(f"Xin chào {user_name}! Tôi là bot của bạn. Rất vui được gặp!")


register_all_handlers(app)

if __name__ == "__main__":
    app_token = os.environ.get("SLACK_APP_TOKEN")
    if not app_token:
        print("Warning: SLACK_APP_TOKEN is not set.")
        app.start(port=int(os.environ.get("PORT", 3000)))
    else:
        SocketModeHandler(app, app_token).start()
        print("⚡️ AWS SlackBot started!")
