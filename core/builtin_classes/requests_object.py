from core.errors import *
from core.datatypes import *
from core.parser import RTResult
from core.builtin_funcs import args
from core.builtin_classes.base_classes import BuiltInObject, operator, check, method
from core.datatypes import radonify, deradonify

import json
import urllib.request
import urllib.parse


class RequestsObject(BuiltInObject):
    @operator("__constructor__")
    @check([], [])
    def constructor(self):
        return RTResult().success(None)

    @args(["url", "headers"], [None, HashMap({})])
    @method
    def get(ctx):
        res = RTResult()
        url = ctx.symbol_table.get("url")
        headers = ctx.symbol_table.get("headers")
        try:
            req = urllib.request.Request(url.value, headers=deradonify(headers))
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
            return res.success(radonify(response_data, url.pos_start, url.pos_end, url.context))
        except Exception as e:
            return res.failure(RTError(url.pos_start, url.pos_end, f"Error sending GET request: {str(e)}", ctx))

    @args(["url", "data", "headers"], [None, HashMap({}), HashMap({})])
    @method
    def post(ctx):
        res = RTResult()
        url = ctx.symbol_table.get("url")
        data = ctx.symbol_table.get("data")
        headers = ctx.symbol_table.get("headers")
        try:
            req = urllib.request.Request(
                url.value, data=json.dumps(deradonify(data)).encode("utf-8"), headers=deradonify(headers)
            )
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
            return res.success(radonify(response_data, url.pos_start, url.pos_end, url.context))
        except Exception as e:
            return res.failure(RTError(url.pos_start, url.pos_end, f"Error sending POST request: {str(e)}", ctx))

    @args(["url", "data", "headers"], [None, HashMap({}), HashMap({})])
    @method
    def put(ctx):
        res = RTResult()
        url = ctx.symbol_table.get("url")
        data = ctx.symbol_table.get("data")
        headers = ctx.symbol_table.get("headers")
        try:
            req = urllib.request.Request(
                url.value, data=json.dumps(deradonify(data)).encode("utf-8"), headers=deradonify(headers), method="PUT"
            )
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
            return res.success(radonify(response_data, url.pos_start, url.pos_end, url.context))
        except Exception as e:
            return res.failure(RTError(url.pos_start, url.pos_end, f"Error sending PUT request: {str(e)}", ctx))

    @args(["url", "headers"], [None, HashMap({})])
    @method
    def delete(ctx):
        res = RTResult()
        url = ctx.symbol_table.get("url")
        headers = ctx.symbol_table.get("headers")
        try:
            req = urllib.request.Request(url.value, headers=deradonify(headers), method="DELETE")
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
            return res.success(radonify(response_data, url.pos_start, url.pos_end, url.context))
        except Exception as e:
            return res.failure(RTError(url.pos_start, url.pos_end, f"Error sending DELETE request: {str(e)}", ctx))

    @args(["url", "data", "headers"], [None, HashMap({}), HashMap({})])
    @method
    def patch(ctx):
        res = RTResult()
        url = ctx.symbol_table.get("url")
        data = ctx.symbol_table.get("data")
        headers = ctx.symbol_table.get("headers")
        try:
            req = urllib.request.Request(
                url.value,
                data=json.dumps(deradonify(data)).encode("utf-8"),
                headers=deradonify(headers),
                method="PATCH",
            )
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
            return res.success(radonify(response_data, url.pos_start, url.pos_end, url.context))
        except Exception as e:
            return res.failure(RTError(url.pos_start, url.pos_end, f"Error sending PATCH request: {str(e)}", ctx))
