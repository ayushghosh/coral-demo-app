Demo App

### JSON Files
Output of certain endpoints will be stored under `/**${user.home}**/.coral/*.json`

### Access Tokens
Set `SIGNALFX_API_TOKEN` variable in your IntelliJ run configuration under env variables

### Test endpoints
```
GET http://localhost:8080/splunk/trace/{{traceId}}}/exitspan
GET http://localhost:8080/splunk/trace/local/exitspan

GET http://localhost:8080/splunk/metrics/{serviceName}
GET http://localhost:8080/splunk/topology

```

```yaml
coral:
  endpoints:
    - name: health
      url: myhealth
      actions:
        - "request|http://localhost:8080/health"
        - "wait_random|1000"
    - name: info
      url: myinfo
      actions:
        - "request|http://localhost:8080/health"
        - "wait_random|1000"
```