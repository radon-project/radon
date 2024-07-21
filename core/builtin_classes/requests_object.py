import json
import urllib.parse
import urllib.request

from core.builtin_classes.base_classes import (BuiltInObject, check, method,
                                               operator)
from core.builtin_funcs import args
from core.datatypes import *
from core.datatypes import deradonify, radonify
from core.errors import *
from core.parser import RTResult


class RequestsObject(BuiltInObject):
    @operator("__constructor__")
    @check([], [])
    def constructor(self) -> RTResult[Value]:
        return RTResult[Value]().success(Null.null())

    @args(["url", "headers"], [None, HashMap({})])
    @method
    def get(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        url = ctx.symbol_table.get("url")
        assert url is not None
        if not isinstance(url, String):
            return res.failure(RTError(url.pos_start, url.pos_end, "Expected String", ctx))
        headers = ctx.symbol_table.get("headers")
        assert headers is not None
        if not isinstance(headers, HashMap):
            return res.failure(RTError(headers.pos_start, headers.pos_end, "Expected HashMap", ctx))
        try:
            req = urllib.request.Request(url.value, headers=deradonify(headers))  # type: ignore
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
            return res.success(radonify(response_data, url.pos_start, url.pos_end, url.context))
        except Exception as e:
            return res.failure(RTError(url.pos_start, url.pos_end, f"Error sending GET request: {str(e)}", ctx))

    @args(["url", "data", "headers"], [None, HashMap({}), HashMap({})])
    @method
    def post(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        url = ctx.symbol_table.get("url")
        assert url is not None
        if not isinstance(url, String):
            return res.failure(RTError(url.pos_start, url.pos_end, "Expected String", ctx))
        data = ctx.symbol_table.get("data")
        assert data is not None
        headers = ctx.symbol_table.get("headers")
        assert headers is not None
        if not isinstance(data, HashMap):
            return res.failure(RTError(data.pos_start, data.pos_end, "Expected HashMap", ctx))
        if not isinstance(headers, HashMap):
            return res.failure(RTError(headers.pos_start, headers.pos_end, "Expected HashMap", ctx))
        try:
            req = urllib.request.Request(
                url.value,
                data=json.dumps(deradonify(data)).encode("utf-8"),
                headers=deradonify(headers),  # type: ignore
            )
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
            return res.success(radonify(response_data, url.pos_start, url.pos_end, url.context))
        except Exception as e:
            return res.failure(RTError(url.pos_start, url.pos_end, f"Error sending POST request: {str(e)}", ctx))

    @args(["url", "data", "headers"], [None, HashMap({}), HashMap({})])
    @method
    def put(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        url = ctx.symbol_table.get("url")
        assert url is not None
        if not isinstance(url, String):
            return res.failure(RTError(url.pos_start, url.pos_end, "Expected String", ctx))
        data = ctx.symbol_table.get("data")
        assert data is not None
        headers = ctx.symbol_table.get("headers")
        assert headers is not None
        if not isinstance(headers, HashMap):
            return res.failure(RTError(headers.pos_start, headers.pos_end, "Expected HashMap", ctx))
        try:
            req = urllib.request.Request(
                url.value,
                data=json.dumps(deradonify(data)).encode("utf-8"),
                headers=deradonify(headers),  # type: ignore
                method="PUT",
            )
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
            return res.success(radonify(response_data, url.pos_start, url.pos_end, url.context))
        except Exception as e:
            return res.failure(RTError(url.pos_start, url.pos_end, f"Error sending PUT request: {str(e)}", ctx))

    @args(["url", "headers"], [None, HashMap({})])
    @method
    def delete(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        url = ctx.symbol_table.get("url")
        assert url is not None
        if not isinstance(url, String):
            return res.failure(RTError(url.pos_start, url.pos_end, "Expected String", ctx))
        headers = ctx.symbol_table.get("headers")
        assert headers is not None
        if not isinstance(headers, HashMap):
            return res.failure(RTError(headers.pos_start, headers.pos_end, "Expected HashMap", ctx))
        try:
            req = urllib.request.Request(url.value, headers=deradonify(headers), method="DELETE")  # type: ignore
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
            return res.success(radonify(response_data, url.pos_start, url.pos_end, url.context))
        except Exception as e:
            return res.failure(RTError(url.pos_start, url.pos_end, f"Error sending DELETE request: {str(e)}", ctx))

    @args(["url", "data", "headers"], [None, HashMap({}), HashMap({})])
    @method
    def patch(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        url = ctx.symbol_table.get("url")
        assert url is not None
        if not isinstance(url, String):
            return res.failure(RTError(url.pos_start, url.pos_end, "Expected String", ctx))
        data = ctx.symbol_table.get("data")
        assert data is not None
        headers = ctx.symbol_table.get("headers")
        assert headers is not None
        if not isinstance(headers, HashMap):
            return res.failure(RTError(headers.pos_start, headers.pos_end, "Expected HashMap", ctx))
        try:
            req = urllib.request.Request(
                url.value,
                data=json.dumps(deradonify(data)).encode("utf-8"),
                headers=deradonify(headers),  # type: ignore
                method="PATCH",
            )
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode("utf-8")
            return res.success(radonify(response_data, url.pos_start, url.pos_end, url.context))
        except Exception as e:
            return res.failure(RTError(url.pos_start, url.pos_end, f"Error sending PATCH request: {str(e)}", ctx))
