#!/usr/bin/python2

import json

class error_object:
    d = {
        'jsonrpc': '2.0',
        'error': {
            'code': None,
            'message': None
        },
        'id': None
    }

    def __init__(self, code, message, id=None):
        if not id == None:
            if isinstance(id, int) or isinstance(id, str) or isinstance(id, unicode):
                self.d['id'] = id
            else:
                raise Exception('id field must be integer, string or NULL')
                
        if isinstance(code, int):
            self.d['error']['code'] = code
        else:
            raise Exception('code field must be integer')

        if isinstance(message, str):
            self.d['error']['message'] = message
        else:
            raise Exception('message field must be string')

    def render_to_json(self):
        return json.dumps(self.d) 

class response_object:
    d = {
        'jsonrpc': '2.0',
        'result': None,
        'id': None
    }
    
    def __init__(self, result, id):
        if not id == None:
            if isinstance(id, int) or isinstance(id, str) or isinstance(id, unicode):
                self.d['id'] = id
            else:
                raise Exception('id field must be integer, string or NULL')
        
        self.d['result'] = result

    def render_to_json(self):
        return json.dumps(self.d) 
 
        
class rpc_handler:
    endpoints = {}

    def __init__(self):
        pass

    def add_endpoint(self, name, endpoint):
        """
        adds endpoint function as "name" to rpc_handler object

        >>> r = rpc_handler()
        >>> r.add_endpoint('hello', lambda:"Hello, World!")
        >>> r.endpoints['hello']()
        'Hello, World!'
        """
        if name not in self.endpoints.keys():
            self.endpoints[name] = endpoint

    def handle_request(self, request):
        """
        handles a jsonrpc request

        >>> rpc_handler().handle_request('')
        '{"jsonrpc": "2.0", "id": null, "error": {"message": "Invalid JSON was received by the server.", "code": -32700}}'
        >>> rpc_handler().handle_request('{ "am i evil": "Yes I am!" }')
        '{"jsonrpc": "2.0", "id": null, "error": {"message": "Invalid JSON-RPC request was received by the server.", "code": -32600}}'
        >>> r = rpc_handler()
        >>> r.add_endpoint('hello', lambda:"Hello, World!")
        >>> r.handle_request('{"jsonrpc": "2.0", "method": "not_actually_there", "id": "1"}')
        '{"jsonrpc": "2.0", "id": "1", "error": {"message": "Method not found.", "code": -32601}}'
        >>> r.handle_request('{"jsonrpc": "2.0", "method": "hello", "id": "1"}')
        '{"jsonrpc": "2.0", "result": "Hello, World!", "id": "1"}'
        >>> def paramtest(x, y):
        ...     return x+y
        >>> r.add_endpoint('paramtest', paramtest)
        >>> r.handle_request('{"jsonrpc": "2.0", "method": "paramtest", "params": [2,3], "id": "1"}')
        '{"jsonrpc": "2.0", "result": 5, "id": "1"}'
        >>> r.handle_request('{"jsonrpc": "2.0", "method": "paramtest", "params": {"x": 2, "y": 3}, "id": "1"}')
        '{"jsonrpc": "2.0", "result": 5, "id": "1"}'
        """
        # parse json string
        try:
            d = json.loads(request)        
        except ValueError, e:
            return error_object(-32700, "Invalid JSON was received by the server.").render_to_json()

        # check for mandatory fields
        available_fields = d.keys()
        required_fields = ['jsonrpc', 'method', 'id']
        
        for field in required_fields:
            if field not in available_fields:
                return error_object(-32600, "Invalid JSON-RPC request was received by the server.").render_to_json()

        # check if json endpoint is available
        if d['method'] in self.endpoints.keys():
            method = self.endpoints[d['method']]
        else:
            return error_object(-32601, "Method not found.", id=d['id']).render_to_json()            

        # execute endpoint function
        try:
            # check if params field is list or dict or not present at all
            if 'params' not in d.keys(): 
                result = method()
            elif isinstance(d['params'], list):
                result = method(*d['params'])
            elif isinstance(d['params'], dict):
                result = method(**d['params'])
            else:
                return  error_object(-32602, 'Invalid method parameter(s)', id=d['id']).render_to_json()
        except Exception, e:
            return error_object(-32603, 'There was an error in the executed method.', id=d['id']).render_to_json()        

        # create dictionary with result
        response = response_object(result, id=d['id'])

        # jsonify dict and return 
        return response.render_to_json()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
