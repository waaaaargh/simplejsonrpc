#!/usr/bin/python2

import json
import socket
import threading

class request_object:
    def __init__(self, id, method, params=None):
        self.d = {
            'jsonrpc': '2.0',
            'method': None,
            'id': None
        }
    
        if not isinstance(method, str):
            raise ValueError('method parameter must be string')
        else:
            self.d['method'] = method

        if not params == None:
            if isinstance(params, dict) or isinstance(params, list):
                self.d['params'] = params
        
        if isinstance(id, str) or isinstance(id, int):
            self.d['id'] = id
        else:
            raise ValueError('id must be str or int')

    def render_to_json(self):
        return json.dumps(self.d)

class error_object:
    def __init__(self, code, message, id=None):
        self.d = {
            'jsonrpc': '2.0',
            'error': {
                'code': None,
                'message': None
            },
            'id': None
        }

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
    def __init__(self, result, id):
        self.d = {
            'jsonrpc': '2.0',
            'result': None,
            'id': None
        }
    
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

        # check if d is a dict
        if not isinstance(d, dict):
            return error_object(-32600, "Invalid JSON-RPC request was received by the server.").render_to_json()

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

class rpc_server:
    """
    Quick JSON-RPC Server via TCP/IP
    
    >>> def hello(name="World"):
    ...   return "Hello, %s!" % (name,)
    ...
    >>> def add(x,y):
    ...   return x+y
    ...
    >>> s = rpc_server('', 1337)
    >>> s.add_endpoint('add', add)
    >>> s.add_endpoint('hello', hello)
    >>> s.start_server()
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.rpc_handler = rpc_handler()
   
    def add_endpoint(self, name, method):
        self.rpc_handler.add_endpoint(name, method)

    def start_server(self):
        def handle_request(conn, rpc_handler):
            data = conn.recv(1024)
            res = rpc_handler.handle_request(data)
            conn.send(res)
            conn.close()

        def serve(rpc_handler):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(1)
            while True:
                conn, addr = s.accept()
                threading.Thread(target=handle_request, args=(conn, rpc_handler)).start()
        
        self.server = threading.Thread(target=serve, args=(self.rpc_handler,))
        self.server.daemon=True
        self.server.start() 

class rpc_client:
    """
    Client for rpc_server.
    
    >>> def hello(name="World"):
    ...   return "Hello, %s!" % (name,)
    >>> def add(x,y):
    ...   return x+y
    >>> s = rpc_server('', 1337)
    >>> s.add_endpoint('hello', hello)
    >>> s.add_endpoint('add', add)
    >>> s.start_server()
    >>> c = rpc_client('localhost', 1337)
    >>> c.request('hello')
    u'Hello, World!'
    >>> c.request('hello', params=['Johannes'])
    u'Hello, Johannes!'
    >>> c.request('add', params={'x': 2,'y': 3})
    5
    >>> c.request('add', params=[2,3])
    5
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def request(self, method_name, params=None):
        r = request_object(1337, method_name, params=params)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(r.render_to_json())
        response_str = s.recv(1024)
        try:
            response_dict = json.loads(response_str)
        except:
            raise Exception('The response from the JSON-RPC Server was not valid JSON.')
        if 'result' in response_dict.keys():
            result = response_dict['result']
        else:
            if 'error' in response_dict.keys():
                error = response_dict['error']
                raise Exception('The JSON-RPC server encountered a problem executing the request: %s (Code %i)' % (error['message'], error['code']))
            else:
                raise Exception('The JSON-RPC error did not send a result back and also was not verbose at all about any errors.')

        return result

if __name__ == '__main__':
    import doctest
    doctest.testmod()
