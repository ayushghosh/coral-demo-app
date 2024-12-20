FROM openjdk:17-jdk-slim
COPY . /app

WORKDIR /app
RUN ./gradlew clean build

# Environment variable to choose the agent: 'splunk' or 'appdynamics'
# ENV AGENT_TYPE=splunk

# Download the Splunk OTEL agent
ADD https://github.com/signalfx/splunk-otel-java/releases/latest/download/splunk-otel-javaagent.jar splunk-otel-javaagent.jar

COPY build/libs/coral-demo-app-0.1-all.jar myapp.jar

# Expose the port the application runs on (example: 8080)
ENV SERVICE_NAME=coral-docker-app
ENV SERVICE_HOST_ADDRESS=localhost
ENV SERVICE_PORT=8080

EXPOSE $SERVICE_PORT

# Conditional entrypoint script based on the AGENT_TYPE environment variable
ENTRYPOINT ["/bin/sh", "-c", " \
  if [ \"$AGENT_TYPE\" = 'splunk' ]; then \
    java -javaagent:/app/splunk-otel-javaagent.jar \
    -Dsplunk.profiler.enabled=true \
    -Dsplunk.profiler.memory.enabled=true \
    -Dexporters.profiling.log_data_enabled=false \
    -jar /app/myapp.jar; \
  elif [ \"$AGENT_TYPE\" = 'appdynamics' ]; then \
    java -javaagent:/app/appd-javaagent/javaagent.jar -jar /app/myapp.jar; \
  else \
    java -jar /app/myapp.jar; \
  fi"]
