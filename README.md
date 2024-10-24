Demo App

### Access Tokens
Set `SIGNALFX_API_TOKEN` variable in your IntelliJ run configuration under env variables

### Test endpoints
```
GET http://localhost:8080/splunk/trace/{{traceId}}}/exitspan
GET http://localhost:8080/splunk/trace/local/exitspan
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