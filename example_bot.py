import os
import json
import boto3
import praw
import praw_bot_wrapper


def secrets(subreddit):
    if os.getenv("DEV"):
        secrets = os.getenv("SECRETS")
    else:
        secrets_manager = boto3.client("secretsmanager")
        secrets_response = secrets_manager.get_secret_value(
            SecretId=f"penpal-confirmation-bot/{subreddit}"
        )
        secrets = secrets_response["SecretString"]
    return json.loads(secrets)


SUBREDDIT_NAME = os.environ["SUBREDDIT_NAME"]
SECRETS = secrets(SUBREDDIT_NAME)
BOT = praw.Reddit(
    client_id=SECRETS["REDDIT_CLIENT_ID"],
    client_secret=SECRETS["REDDIT_CLIENT_SECRET"],
    user_agent=SECRETS["REDDIT_USER_AGENT"],
    username=SECRETS["REDDIT_USERNAME"],
    password=SECRETS["REDDIT_PASSWORD"],
)
CURRENT_MODS = [str(mod) for mod in BOT.subreddit(SUBREDDIT_NAME).moderator()]


@praw_bot_wrapper.stream_handler(BOT.subreddit(SUBREDDIT_NAME).stream.comments)
def handle_new_comments(comment: praw.models.Comment):
    print(f"New comment: https://reddit.com{comment.permalink}")


@praw_bot_wrapper.stream_handler(BOT.subreddit(SUBREDDIT_NAME).stream.submissions)
def handle_new_posts(post: praw.models.Submission):
    print(f"New submission https://reddit.com{post.permalink}")


@praw_bot_wrapper.stream_handler(BOT.inbox.stream)
def handle_inbox(message):
    message.mark_read()
    if (
        not isinstance(message, praw.models.Message)
        or message.author not in CURRENT_MODS
    ):
        return
    print(f"Message from a moderator: {message.body}")
    message.mark_read()


@praw_bot_wrapper.outage_recovery_handler(outage_threshold=10)
def notify_outage_recovery(started_at):
    print(f"An outage that started at {started_at} has recovered")
    send_message_to_mods(
        subject="Bot Recovered from Extended Outage",
        message="test",
    )


def send_message_to_mods(subject, message):
    # changed how we send the modmail so that it because an archivable message
    # mod discussions can't be archived which is annoying
    return BOT.subreddit(SUBREDDIT_NAME).modmail.create(
        subject=subject, body=message, recipient=BOT.user.me()
    )


praw_bot_wrapper.run()
