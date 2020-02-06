"""
Rewrite a HTTP response by replacing it with arbitrary fixture file

arguments:
partial_url: all http requests that match this partial url will be modified
fixture_path: path to the chosen fixture file
check_json: (Boolean) if True, checks that the response is valid JSON first

example command line invocation:
./mitmdump -s json_response_replace.py
--set fixture__path='/path/to/fixtures/some_fixture.json'
--set partial_url='Service.svc/recommendation/content/media'
--mode transparent --listen-port 8081

"""
from __future__ import print_function
import json
from mitmproxy import ctx


def load(loader):

    loader.add_option(
        "partial_url", str, "",
        "partial url 1 to match upon"
    )
    loader.add_option(
        "fixture_path", str, "",
        "absolute path to fixture file 1"
    )
    loader.add_option(
        "check_json", bool, True,
        "specifies if we want to check that the http response is JSON"
    )


def response(flow):
    data = {
        ctx.options.partial_url : ctx.options.fixture_path,
    }

    if any(url in flow.request.pretty_url for url in data):
        for (partial_url, fixture_path) in data.items():
            if not partial_url or not fixture_path:
                continue
            if partial_url in flow.request.pretty_url:
                # Verify the response is JSON if we expect it
                if ctx.options.check_json:
                    json_resp = json.loads(flow.response.text)
                    if not (json_resp and isinstance(json_resp, dict)):
                        print('Error: Invalid json response, '
                              'leaving response unchanged')
                        return

                # Load the fixture into memory
                fixture = None
                with open(fixture_path) as fixturejson:
                    fixture = json.load(fixturejson)
                fixture = json.dumps(fixture)

                # Rewrite the HTTP response
                print("Rewriting HTTP response matching partial url: '{0}' "
                      "with fixture: '{1}'".format(partial_url, fixture_path))
                flow.response.text = fixture
                break
