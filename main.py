#    Sample main.py Tornado file
#    (for Tornado on Heroku)
#
#    Author: Mike Dory | dory.me
#    Created: 11.12.11 | Updated: 06.02.13
#    Contributions by Tedb0t, gregory80
#
# ------------------------------------------

#!/usr/bin/env python
import os.path
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpclient
import json

from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

import sys

import kvs

# import and define tornado-y things
from tornado.options import define
define("port", default=5000, help="run on the given port", type=int)


# define line_bot token
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


# define docomo_dialog api token
docomo_api_key = os.getenv(
    'API_KEY', "374e544e6e585643347776797a794650524579705a62706754696b6c31717a553867615957465850784843")


# application settings and handle mapping info
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/callback", LineMsgHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


# the main page
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        if 'GOOGLEANALYTICSID' in os.environ:
            google_analytics_id = os.environ['GOOGLEANALYTICSID']
        else:
            google_analytics_id = False

        self.render(
            "main.html",
            page_title='Heroku Funtimes',
            page_heading='fuga!',
            google_analytics_id=google_analytics_id,
        )

context = None


# line message handler
class LineMsgHandler(tornado.web.RequestHandler):
    def post(self):
        # check header
        try:
            signature = self.request.headers['X-Line-Signature']
        except KeyError:
            self.send_error(status_code=400)
            raise

        # get request body as text
        body = self.request.body.decode('utf-8')

        # parse webhook body
        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            self.send_error(status_code=400)
            raise

        # if enent is MessageEvent and message is TextMessage, then echo text
        for event in events:
            if not isinstance(event, MessageEvent):
                continue

            if not isinstance(event.message, TextMessage):
                continue

            message = self.docomo_dialog(event.message.text, event.source.user_id)

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
            )

        self.write("OK")

    def docomo_dialog(self, message: str, line_user_id) -> str:
        db = kvs.KVS()
        docomo_api_endpoint = 'https://api.apigw.smt.docomo.ne.jp/dialogue/v1/dialogue' + '?APIKEY=' + docomo_api_key

        req_body = {
            "utt": message
        }
        # check context id is exist
        if db.get_value(line_user_id) is not None:
            req_body.update({"context": db.get_value(line_user_id)})

        # fetching dialog api
        http_client = tornado.httpclient.HTTPClient()
        try:
            request = tornado.httpclient.HTTPRequest(
                url=docomo_api_endpoint,
                method='POST',
                headers={
                    'Content-Type': 'application/json'
                },
                body=json.dumps(req_body)
            )
            response = http_client.fetch(request)
        except:
            raise
        http_client.close()

        # parse response json
        res = json.loads(response.body.decode('utf-8'))

        # set context_id
        if db.get_value(line_user_id) is None:
            db.set_value(line_user_id, res.get('context'))

        return res.get('utt', 'ファッ!?')


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(tornado.options.options.port)

    # start it up
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
