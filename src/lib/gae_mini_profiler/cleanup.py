import StringIO

def cleanup(request, response):
    '''
    Convert request and response dicts to a human readable format where
    possible.
    '''
    request_short = None
    response_short = None
    miss = 0

    if "MemcacheGetRequest" in request:
        request = request["MemcacheGetRequest"]
        response = response["MemcacheGetResponse"]
        if request:
            request_short = memcache_get(request)
        if response:
            response_short, miss = memcache_get_response(response)
    elif "MemcacheSetRequest" in request and request["MemcacheSetRequest"]:
        request_short = memcache_set(request["MemcacheSetRequest"])
    elif "Query" in request and request["Query"]:
        request_short = datastore_query(request["Query"])
    elif "GetRequest" in request and request["GetRequest"]:
        request_short = datastore_get(request["GetRequest"])
    elif "PutRequest" in request and request["PutRequest"]:
        request_short = datastore_put(request["PutRequest"])
    # todo:
    # TaskQueueBulkAddRequest
    # BeginTransaction
    # Transaction

    return request_short, response_short, miss

def memcache_get_response(response):
    """Pretty-format a memcache.get() response.

    Arguments:
      response - The memcache.get() response object, e.g.
        {'item': [{'Item': {'flags': '0L', 'key': 'memcache_key', ...

    Returns:
      The tuple (value, miss) where the "value" is the value of the
      memcache.get() response as a string. If there are multiple response
      values, as when multiple keys are passed in, the values are separated by
      newline characters. "miss" is 1 if there were no items returned from
      memcache and 0 otherwise.
    """
    if 'item' not in response or not response['item']:
        return None, 1

    items = response['item']
    for i, item in enumerate(items):
        if type(item) == dict:
            if 'MemcacheGetResponse_Item' in item:
                # This key exists in dev and in the 'python' production runtime.
                item = item['MemcacheGetResponse_Item']['value']
            else:
                # But it's a different key in the 'python27' production runtime.
                item = item['Item']['value']
            item = truncate(repr(item))
            items[i] = item
    response_short = "\n".join(items)
    return response_short, 0

def memcache_get(request):
    """Pretty-format a memcache.get() request.

    Arguments:
      request - The memcache.get() request object, i.e.
        {'key': ['memcache_key']}

    Returns:
      The keys of the memcache.get() response as a string. If there are
      multiple keys, they are separated by newline characters.
    """
    keys = request['key']
    request_short = "\n".join([truncate(k) for k in keys])
    namespace = ''
    if 'name_space' in request:
        namespace = request['name_space']
        if len(keys) > 1:
            request_short += '\n'
        else:
            request_short += ' '
        request_short += '(ns:%s)' % truncate(namespace)
    return request_short

def memcache_set(request):
    """Pretty-format a memcache.set() request.

    Arguments:
      request - The memcache.set() request object, e.g.,
        {'item': [{'Item': {'flags': '0L', 'key': 'memcache_key' ...

    Returns:
      The keys of the memcache.get() response as a string. If there are
      multiple keys, they are separated by newline characters.
    """
    keys = []
    for i in request["item"]:
        if "MemcacheSetRequest_Item" in i:
            # This key exists in dev and in the 'python' production runtime.
            key = i["MemcacheSetRequest_Item"]["key"]
        else:
            # But it's a different key in the 'python27' production runtime.
            key = i["Item"]["key"]
        keys.append(truncate(key))
    return "\n".join(keys)

def datastore_query(query):
    kind = query.get('kind', 'UnknownKind')
    count = query.get('count', '')

    filters_clean = datastore_query_filter(query)
    orders_clean = datastore_query_order(query)

    s = StringIO.StringIO()
    s.write("SELECT FROM %s\n" % kind)
    if filters_clean:
        s.write("WHERE\n")
        for name, op, value in filters_clean:
            s.write("%s %s %s\n" % (name, op, value))
    if orders_clean:
        s.write("ORDER BY\n")
        for prop, direction in orders_clean:
            s.write("%s %s\n" % (prop, direction))
    if count:
        s.write("LIMIT %s\n" % count)

    result = s.getvalue()
    s.close()
    return result

def datastore_query_filter(query):
    _Operator_NAMES = {
        0: "?",
        1: "<",
        2: "<=",
        3: ">",
        4: ">=",
        5: "=",
        6: "IN",
        7: "EXISTS",
    }
    filters = query.get('filter', [])
    filters_clean = []
    for f in filters:
        if 'Query_Filter' in f:
            # This key exists in dev and in the 'python' production runtime.
            f = f["Query_Filter"]
        elif 'Filter' in f:
            # But it's a different key in the 'python27' production runtime.
            f = f["Filter"]
        else:
            # Filters are optional, so there might be no filter at all.
            continue
        op = _Operator_NAMES[int(f.get('op', 0))]
        props = f["property"]
        for p in props:
            p = p["Property"]
            name = p["name"] if "name" in p else "UnknownName"

            if 'value' in p:

                propval = p['value']['PropertyValue']

                if 'stringvalue' in propval:
                    value = propval["stringvalue"]
                elif 'referencevalue' in propval:
                    if 'PropertyValue_ReferenceValue' in propval['referencevalue']:
                        # This key exists in dev and in the 'python' production runtime.
                        ref = propval['referencevalue']['PropertyValue_ReferenceValue']
                    else:
                        # But it's a different key in the 'python27' production runtime.
                        ref = propval['referencevalue']['ReferenceValue']
                    els = ref['pathelement']
                    paths = []
                    for el in els:
                        if 'PropertyValue_ReferenceValuePathElement' in el:
                            # This key exists in dev and in the 'python' production runtime.
                            path = el['PropertyValue_ReferenceValuePathElement']
                        else:
                            # But it's a different key in the 'python27' production runtime.
                            path = el['ReferenceValuePathElement']
                        paths.append("%s(%s)" % (path['type'], id_or_name(path)))
                    value = "->".join(paths)
                elif 'booleanvalue' in propval:
                    value = propval["booleanvalue"]
                elif 'uservalue' in propval:
                    if 'PropertyValue_UserValue' in propval['uservalue']:
                        # This key exists in dev and in the 'python' production runtime.
                        email = propval['uservalue']['PropertyValue_UserValue']['email']
                    else:
                        # But it's a different key in the 'python27' production runtime.
                        email = propval['uservalue']['UserValue']['email']
                    value = 'User(%s)' % email
                elif '...' in propval:
                    value = '...'
                elif 'int64value' in propval:
                    value = propval["int64value"]
                else:
                    raise Exception(propval)
            else:
                value = ''
            filters_clean.append((name, op, value))
    return filters_clean

def datastore_query_order(query):
    orders = query.get('order', [])
    _Direction_NAMES = {
        0: "?DIR",
        1: "ASC",
        2: "DESC",
    }
    orders_clean = []
    for order in orders:
        if 'Query_Order' in order:
            # This key exists in dev and in the 'python' production runtime.
            order = order['Query_Order']
        else:
            # But it's a different key in the 'python27' production runtime.
            order = order['Order']
        direction = _Direction_NAMES[int(order.get('direction', 0))]
        prop = order.get('property', 'UnknownProperty')
        orders_clean.append((prop, direction))
    return orders_clean

def id_or_name(path):
    if 'name' in path:
        return path['name']
    else:
        return path['id']

def datastore_get(request):
    keys = request["key"]
    if len(keys) > 1:
        keylist = cleanup_key(keys.pop(0))
        for key in keys:
            keylist += ", " + cleanup_key(key)
        return keylist
    elif keys:
        return cleanup_key(keys[0])

def cleanup_key(key):
    if 'Reference' not in key: 
        #sometimes key is passed in as '...'
        return key
    els = key['Reference']['path']['Path']['element']
    paths = []
    for el in els:
        if 'Path_Element' in el:
            # This key exists in dev and in the 'python' production runtime.
            path = el['Path_Element']
        else:
            # But it's a different key in the 'python27' production runtime.
            path = el['Element']
        paths.append("%s(%s)" % (path['type'] if 'type' in path 
                     else 'UnknownType', id_or_name(path)))
    return "->".join(paths)

def datastore_put(request):
    entities = request["entity"]
    keys = []
    for entity in entities:
        keys.append(cleanup_key(entity["EntityProto"]["key"]))
    return "\n".join(keys)

def truncate(value, limit=100):
    if len(value) > limit:
        return value[:limit - 3] + "..."
    else:
        return value
