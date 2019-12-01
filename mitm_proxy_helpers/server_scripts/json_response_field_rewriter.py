"""
Re-write an arbitrary field on a HTTP JSON Response
Does not yet support nested json fields

arguments:
partial_url: all http requests that match this partial url will be modified
field_name: JSON field to look up
field_value: JSON field value to modify

example command line invocation:
./mitmdump -s json_response_field_rewriter.py --set field_name=Rating
--set field_value=R --set partial_url=Service.svc/details/media/
--mode transparent --listen-port 8081

"""
from __future__ import print_function
import json
from mitmproxy import ctx


def load(loader):

    loader.add_option(
        "partial_url", str, "",
        "partial url to match upon"
    )
    loader.add_option(
        "field_name", str, "",
        "JSON field name to target"
    )
    loader.add_option(
        "field_value", str, "",
        "Value to set for the JSON field"
    )


def response(flow):
    if ctx.options.partial_url in flow.request.pretty_url:
        json_resp = json.loads(flow.response.text)
        if not (json_resp and isinstance(json_resp, dict)):
            print('Error: Invalid json response, leaving response unchanged')
            return
        if ctx.options.field_name in json_resp:
            print("Setting {0} to {1} in {2}".format(
                ctx.options.field_name, ctx.options.field_value,
                flow.request.pretty_url))
            json_resp[ctx.options.field_name] = ctx.options.field_value
            print("Replacing field value in JSON")
            json_str = json.dumps(json_resp)
            flow.response.text = json_str
