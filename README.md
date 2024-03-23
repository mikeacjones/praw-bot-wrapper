# Simple PRAW Bot Wrapper

Simplel wrapper that handles managing streams in PRAW. Designed to help keep a stream infinitely iterating even when the Reddit APIs have outages.

## Example Bot

```python
import os
import json
import boto3
import praw
import sys


def secrets(subreddit):
    if os.getenv("DEV"):
        secrets = os.getenv("SECRETS")
    else:
        secrets_manager = boto3.client("secretsmanager")
        secrets_response = secrets_manager.get_secret_value(
            SecretId=f"reddit-bot/{subreddit}"
        )
        secrets = secrets_response["SecretString"]
    return json.loads(secrets)


SUBREDDIT_NAME = os.environ["SUBREDDIT_NAME"]
SECRETS = secrets(SUBREDDIT_NAME)
BOT = Bot(
    SECRETS["REDDIT_CLIENT_ID"],
    SECRETS["REDDIT_CLIENT_SECRET"],
    SECRETS["REDDIT_USER_AGENT"],
    SECRETS["REDDIT_USERNAME"],
    SECRETS["REDDIT_PASSWORD"],
    outage_threshold=10, # number of failed cycles before triggering outage notification handler
    # each failed cycle triggers a sleep for total_failures * 60 seconds
    # 10 outages represents roughly 1 hour
)
CURRENT_MODS = [str(mod) for mod in BOT.subreddit(SUBREDDIT_NAME).moderator()]


@BOT.stream_handler(BOT.subreddit(SUBREDDIT_NAME).stream.comments)
def handle_new_comments(comment: praw.models.Comment):
    print(f"New comment: https://reddit.com{comment.permalink}")


@BOT.stream_handler(BOT.subreddit(SUBREDDIT_NAME).stream.submissions)
def handle_new_posts(post: praw.models.Submission):
    print(f"New submission https://reddit.com{post.permalink}")


@BOT.stream_handler(BOT.inbox.stream)
def handle_inbox(message):
    message.mark_read()
    if (
        not isinstance(message, praw.models.Message)
        or message.author not in CURRENT_MODS
    ):
        return
    print(f"Message from a moderator: {message.body}")
    message.mark_read()


@BOT.outage_recovery_handler()
def notify_outage_recovery(started_at):
    print(f"An outage that started at {started_at} has recovered")


BOT.run()
```