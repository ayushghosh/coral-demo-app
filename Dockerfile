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
EXPOSE 8080

# Conditional entrypoint script based on the AGENT_TYPE environment variable
ENTRYPOINT ["/bin/sh", "-c", "\
  if [ \"$AGENT_TYPE\" = 'splunk' ]; then \
    java -javaagent:/app/splunk-otel-javaagent.jar -jar /app/myapp.jar; \
  elif [ \"$AGENT_TYPE\" = 'appdynamics' ]; then \
    java -javaagent:/app/appd-javaagent/javaagent.jar -jar /app/myapp.jar; \
  else \
    java -jar /app/myapp.jar; \
  fi"]
