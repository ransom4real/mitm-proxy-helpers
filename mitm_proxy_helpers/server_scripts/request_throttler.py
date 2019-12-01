"""
Simulate request throttling by adding a delay before streaming the response
body
"""
from time import sleep
from mitmproxy import ctx


def load(loader):

    loader.add_option(
        "partial_url", str, "",
        "partial url to match upon"
    )
    loader.add_option(
        "latency", str, "",
        "Number of seconds latency to add to matching response"
    )

def delay_before_streaming_response(flow):
    if ctx.options.partial_url in flow.request.pretty_url:
        return int(ctx.options.latency)
    return 0

def responseheaders(flow):
    def modify(chunks):
        sleep(delay_before_streaming_response(flow))
        # continue to stream original response
        yield from chunks
    flow.response.stream = modify
