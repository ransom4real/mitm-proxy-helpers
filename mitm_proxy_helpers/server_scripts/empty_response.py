"""
Alter http reponse to be empty response for all requests
that match a partial_url

arguments:
partial_url: all http requests that match this partial url will be modified

example command line invocation:
mitmdump -s ./empty_response.py --set partial_url=/some/partial/url/

"""
from __future__ import print_function
from mitmproxy import ctx


def load(loader):

    loader.add_option(
        "partial_url", str, "",
        "partial url to match upon"
    )


def response(flow):
    if ctx.options.partial_url in flow.request.pretty_url:
        print('Setting empty response for {}'.format(flow.request.pretty_url))
        flow.response.text = ''
