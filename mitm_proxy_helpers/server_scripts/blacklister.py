"""
Simulate URL blacklisting by dropping http requests that match
a given URL pattern

arguments:
partial_url: all http requests that match this partial url will be modified
status_code: modify the response with this status code if present

example command line invocation:
mitmdump -s ./blacklister.py --set partial_url=/some/partial/url/
--set status_code=403

"""
from __future__ import print_function
from mitmproxy import ctx


def load(loader):
    loader.add_option(
        "status_code", str, "",
        "Status code to use for matching response."
    )
    loader.add_option(
        "partial_url", str, "",
        "partial url to match upon"
    )


def response(flow):
    if (len(ctx.options.status_code) == 3 and
            ctx.options.partial_url in flow.request.pretty_url):
        print('Blacklisting url: {}'.format(flow.request.pretty_url))
        flow.response.status_code = int(ctx.options.status_code)
        flow.response.reason = "URL Blacklisted at mitmproxy"
