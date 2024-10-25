import requests
import json

class AppDynamicsClient: 
    TIME_RANGE_TYPES = ('BEFORE_NOW', 'BEFORE_TIME', 'AFTER_TIME', 'BETWEEN_TIMES')    
    SNAPSHOT_REQUEST_PARAMS = ('guids', 'archived', 'deep-dive-policy', 'application-component-ids',
                               'application-component-node-ids', 'business-transaction-ids', 'user-experience',
                               'first-in-chain', 'need-props', 'need-exit-calls', 'execution-time-in-millis',
                               'session-id', 'user-principal-id', 'error-ids', 'error-occurred',
                               'bad-request', 'diagnostic-snapshot', 'diagnostic-session-guid',
                               'starting-request-id', 'ending-request-id',
                               'data-collector-name', 'data-collector-type', 'data-collector-value')

    SNAPSHOT_REQUEST_LISTS = ('business-transaction-ids', 'user-experience', 'error-ids', 'guids', 'deep-dive-policy',
                              'application-component-ids', 'application-component-node-ids', 'diagnostic-session-guid')

    def __init__(self, base_url, jsession):
        self._base_url = base_url 
        self._jsession = jsession
        self._base_headers = self._get_auth_headers()

    def _get_auth_headers(self): 
        # get auth token
        url = f"{self._base_url}/controller/rest/authtoken/v1/token"
        payload = ""
        headers = {'Cookie': self._jsession}
        response = requests.request("GET", url, headers=headers, data=payload)

        # get auth header
        headers = {} 
        headers["Authorization"] = "Bearer " + response.json()['access_token']
        return headers

    def ui_request(self, path): 
        headers = self._base_headers
        url = self._base_url + path
        r = requests.request("GET", url, headers=headers)
        return r

    def request(self, path, params=None, method='GET', use_json=True, query=True, headers=None):
        if not headers: 
            headers = self._base_headers
        else: 
            headers.update(self._base_headers)

        if not path.startswith('/'):
            path = '/' + path
        url = self._base_url + path

        params = params or {}
        if use_json and method == 'GET':
            params['output'] = 'JSON'
        for k in list(params.keys()):
            if params[k] is None:
                del params[k]

        r = requests.request(method, url, params=params, headers=headers)
        try: 
            return r.json() if use_json else r.text
        except: 
            return r

    def _app_path(self, app_id, path=None):
        app_id = app_id if isinstance(app_id, int) or isinstance(app_id, str) else self._app_id
        if not app_id:
            raise ValueError('application id is required')
        path = '/controller/rest/applications/%s' % app_id + (path or '')
        return path

    def _app_request(self, path, app_id=None, params=None, method='GET', query=True, use_json=True):
        path = self._app_path(app_id, path)
        return self.request(path, params, method=method, query=query, use_json=use_json)

    def _top_request(self, path, params=None, method='GET', query=True):
        return self.request('/controller/rest' + path, params, method, query=query)

    def get_applications(self):
        """
        Get a list of all business applications.

        :returns: List of applications visible to the user.
        :rtype: appd.model.Applications
        """
        return self._top_request('/applications')

    def get_metrics(self, metric_path, app_id=None, time_range_type='BEFORE_NOW',
                    duration_in_mins=15, start_time=None, end_time=None, rollup=True):
        """
        Retrieves metric data.

        :param str metric_path: Full metric path of the metric(s) to be retrieved. Wildcards are supported.
            See :ref:`metric-paths` for details.
        :param int app_id: Application ID to retrieve nodes for. If :const:`None`, the value stored in the
            `app_id` property will be used.
        :param str time_range_type: Must be one of :const:`BEFORE_NOW`, :const:`BEFORE_TIME`,
            :const:`AFTER_TIME`, or :const:`BETWEEN_TIMES`.
            See :ref:`time-range-types` for a full explanation.
        :param int duration_in_mins: Number of minutes before now. Only valid if the
            :attr:`time_range_type` is :const:`BEFORE_NOW`.
        :param long start_time: Start time, expressed in milliseconds since epoch. Only valid if the
            :attr:`time_range_type` is :const:`AFTER_TIME` or :const:`BETWEEN_TIMES`.
        :param long end_time: End time, expressed in milliseconds since epoch. Only valid if the
            :attr:`time_range_type` is :const:`BEFORE_TIME` or :const:`BETWEEN_TIMES`.
        :param bool rollup: If :const:`False`, return individual data points for each time slice in
            the given time range. If :const:`True`, aggregates the data and returns a single data point.
        :returns: A list of metric values.
        :rtype: appd.model.MetricData
        """

        params = self._validate_time_range(time_range_type, duration_in_mins, start_time, end_time)
        params.update({'metric-path': metric_path,
                       'rollup': rollup})

        return self._app_request('/metric-data', app_id, params)

    def _validate_time_range(self, time_range_type, duration_in_mins, start_time, end_time):

        """
        Validates the combination of parameters used to specify a time range in AppDynamics.

        :param str time_range_type: type of time range to search
        :param int duration_in_mins: duration to search, in minutes
        :param long start_time: starting time
        :param long end_time: ending time
        :returns: parameters to be sent to controller
        :rtype: dict
        """
        if time_range_type and time_range_type not in self.TIME_RANGE_TYPES:
            raise ValueError('time_range_time must be one of: ' + ', '.join(self.TIME_RANGE_TYPES))

        elif time_range_type == 'BEFORE_NOW' and not duration_in_mins:
            raise ValueError('when using BEFORE_NOW, you must specify duration_in_mins')

        elif time_range_type == 'BEFORE_TIME' and (not end_time or not duration_in_mins):
            raise ValueError('when using BEFORE_TIME, you must specify duration_in_mins and end_time')

        elif time_range_type == 'AFTER_TIME' and (not start_time or not duration_in_mins):
            raise ValueError('when using AFTER_TIME, you must specify duration_in_mins and start_time')

        elif time_range_type == 'BETWEEN_TIMES' and (not start_time or not end_time):
            raise ValueError('when using BETWEEN_TIMES, you must specify start_time and end_time')

        return {'time-range-type': time_range_type,
                'duration-in-mins': duration_in_mins,
                'start-time': start_time,
                'end-time': end_time}

    def get_bt_list(self, app_id=None, excluded=False):
        """
        Get the list of all registered business transactions in an application.

        :param int app_id: Application ID to retrieve the BT list for. If :const:`None`, the value stored in the
          `app_id` property will be used.
        :param bool excluded: If True, the function will return BT's that have been excluded in the AppDynamics
          UI. If False, the function will return all BT's that have not been excluded. The default is False.
        :returns: The list of registered business transactions.
        :rtype: appd.model.BusinessTransactions
        """
        return self._app_request('/business-transactions', app_id, {'exclude': excluded})

    def get_backends(self, app_id=None):
        """
        Get the list of all backends in an application.

        :param int app_id: Application ID to retrieve backends for. If :const:`None`, the value stored in the
          `app_id` property will be used.
        :return: A :class:`Backends <appd.model.Backends>` object, representing a collection of backends.
        :rtype: appd.model.Backends
        """
        return self._app_request('/backends', app_id)

    def get_tiers(self, app_id=None):
        """
        Get the list of all configured tiers in an application.

        :param int app_id: Application ID to retrieve tiers for. If :const:`None`, the value stored in the
          `app_id` property will be used.
        :return: A :class:`Tiers <appd.model.Tiers>` object, representing a collection of tiers.
        :rtype: appd.model.Tiers
        """
        return self._app_request('/tiers', app_id)

    def get_nodes(self, app_id=None, tier_id=None):
        """
        Retrieves the list of nodes in the application, optionally filtered by tier.

        :param int app_id: Application ID to retrieve nodes for. If :const:`None`, the value stored in the
          `app_id` property will be used.
        :param int tier_id: If set, retrieve only the nodes belonging to the specified tier. If :const:`None`,
          retrieve all nodes in the application.
        :return: A :class:`Nodes <appd.model.Nodes>` object, representing a collection of nodes.
        :rtype: appd.model.Nodes
        """

        path = ('/tiers/%s/nodes' % tier_id) if tier_id else '/nodes'
        return self._app_request(path, app_id)

    def get_node(self, node_id, app_id=None):
        """
        Retrieves details about a single node.

        :param node_id: ID or name of the node to retrieve.
        :param app_id: Application ID to search for the node.
        :return: A single Node object.
        :rtype: appd.model.Node
        """
        return self._app_request('/nodes/%s' % node_id, app_id)     

    def get_flowmap(self, app_num): 
        path = f'/controller/restui/applicationFlowMapUiService/application/{app_num}?time-range=last_1_hour.BEFORE_NOW.-1.-1.60&mapId=-1&baselineId=-1&forceFetch=false'
        return self.ui_request(path).json()

    def get_snapshots(self, app_id=None, time_range_type='BEFORE_NOW', duration_in_mins=15,
                      start_time=None, end_time=None, **kwargs):
        """
        Finds and returns any snapshots in the given time range that match a set of criteria. You must provide
        at least one condition to the search parameters in the :data:`kwargs` parameters. The list of valid
        conditions can be found `here <http://appd.ws/2>`_.

        :param int app_id: Application ID to retrieve nodes for. If :const:`None`, the value stored in the
            `app_id` property will be used.
        :param str time_range_type: Must be one of :const:`BEFORE_NOW`, :const:`BEFORE_TIME`,
            :const:`AFTER_TIME`, or :const:`BETWEEN_TIMES`.
            See :ref:`time-range-types` for a full explanation.
        :param int duration_in_mins: Number of minutes before now. Only valid if the
            :attr:`time_range_type` is :const:`BEFORE_NOW`.
        :param long start_time: Start time, expressed in milliseconds since epoch. Only valid if the
            :attr:`time_range_type` is :const:`AFTER_TIME` or :const:`BETWEEN_TIMES`.
        :param long end_time: End time, expressed in milliseconds since epoch. Only valid if the
            :attr:`time_range_type` is :const:`BEFORE_TIME` or :const:`BETWEEN_TIMES`.
        :param kwargs: Additional key/value pairs to pass to the controller as search parameters.
        :returns: A list of snapshots.
        :rtype: appd.model.Snapshots
        """

        params = {} 
        for qs_name in self.SNAPSHOT_REQUEST_PARAMS:
            arg_name = qs_name.replace('-', '_')
            params[qs_name] = kwargs.get(arg_name, None)
            if qs_name in self.SNAPSHOT_REQUEST_LISTS and qs_name in kwargs:
                params[qs_name] = ','.join(params[qs_name])
        params.update(self._validate_time_range(time_range_type, duration_in_mins, start_time, end_time))
        print(params)
        return self._app_request('/request-snapshots', app_id, params)

    def get_healthrule_violations(self, app_id=None, time_range_type='BEFORE_NOW', duration_in_mins=15,
                                  start_time=None, end_time=None):
        """
        Retrieves a list of health rule violations during the specified time range. Compatible with
        controller version 3.7 and later.

        :param int app_id: Application ID to retrieve nodes for. If :const:`None`, the value stored in the
            `app_id` property will be used.
        :param str time_range_type: Must be one of :const:`BEFORE_NOW`, :const:`BEFORE_TIME`,
            :const:`AFTER_TIME`, or :const:`BETWEEN_TIMES`.
            See :ref:`time-range-types` for a full explanation.
        :param int duration_in_mins: Number of minutes before now. Only valid if the
            :attr:`time_range_type` is :const:`BEFORE_NOW`.
        :param long start_time: Start time, expressed in milliseconds since epoch. Only valid if the
            :attr:`time_range_type` is :const:`AFTER_TIME` or :const:`BETWEEN_TIMES`.
        :param long end_time: End time, expressed in milliseconds since epoch. Only valid if the
            :attr:`time_range_type` is :const:`BEFORE_TIME` or :const:`BETWEEN_TIMES`.
        :returns: A list of policy violations.
        :rtype: appd.model.PolicyViolations
        """

        params = self._validate_time_range(time_range_type, duration_in_mins, start_time, end_time)

        return self._app_request('/problems/healthrule-violations', app_id, params)

    def get_metric_tree(self, app_id=None, metric_path=None):
        params = {} 
        if metric_path: 
            params['metric-path'] = metric_path
        return self._app_request('/metrics', app_id, params)