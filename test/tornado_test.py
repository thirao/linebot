#!/usr/bin/env python
import os.path
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpclient

import json

# import and define tornado-y things
from tornado.options import define
define("port", default=5000, help="run on the given port", type=int)


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


# line message handler
context = None
class LineMsgHandler(tornado.web.RequestHandler):
    def post(self):
        global context
        docomo_api_endpoint = 'https://api.apigw.smt.docomo.ne.jp/dialogue/v1/dialogue' + '?APIKEY=' + docomo_api_key

        req_body = {
            "utt": self.request.body.decode('utf-8')
        }
        # check context id is exist
        if context is not None:
            req_body.update({"context": context})

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

        # set new context_id
        if context is None:
            res = json.loads(response.body.decode('utf-8'))
            context = res.get('context', None)

        self.write(response.body)

    def docomo_dialog(self, message):
        global context
        docomo_api_endpoint = 'https://api.apigw.smt.docomo.ne.jp/dialogue/v1/dialogue' + '?APIKEY=' + docomo_api_key

        req_body = {
            "utt": message
        }
        # check context id is exist
        if context is not None:
            req_body.update({"context": context})

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
        if context is None:
            context = res.get('context', None)

        return res.get('utt', 'ファッ!?')



def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(tornado.options.options.port)

    # start it up
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
