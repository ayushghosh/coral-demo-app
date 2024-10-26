package dev.coral.controllers;

import java.io.IOException;
import java.util.Locale;
import java.util.concurrent.ThreadLocalRandom;


import dev.coral.config.EndpointConfig;
import dev.coral.model.SplunkAlert;
import dev.coral.model.SplunkMTS;
import dev.coral.model.SplunkTopology;
import dev.coral.service.Span;
import dev.coral.service.SplunkO11yDataFetcherService;
import dev.coral.utils.metrics.LocalFileWriter;
import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.PathVariable;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.scheduling.TaskExecutors;
import io.micronaut.scheduling.annotation.ExecuteOn;
import jakarta.inject.Inject;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Controller
@ExecuteOn(TaskExecutors.BLOCKING)
public class DynamicController {
    private final EndpointConfig endpointConfig;
    private final HttpClient httpClient;
    private final SplunkO11yDataFetcherService splunkO11yDataFetcherService;

    @Inject
    public DynamicController(EndpointConfig endpointConfig, @Client HttpClient httpClient,
                             SplunkO11yDataFetcherService splunkO11yDataFetcherService) {
        this.endpointConfig = endpointConfig;
        this.httpClient = httpClient;
        this.splunkO11yDataFetcherService = splunkO11yDataFetcherService;
    }

    @Get("/orders")
    public StringBuilder getSplunkMTS() {
        String serviceHostAddress = System.getenv("SERVICE_HOST_ADDRESS");
        log.info("Received order request, calling payment service and checkout service");
        StringBuilder responseBuilder = new StringBuilder();
        // service in splunk
        responseBuilder.append(httpClient.toBlocking().retrieve("http://" + serviceHostAddress + ":8082/checkout"));
        // service in appD
        responseBuilder.append(httpClient.toBlocking().retrieve("http://" + serviceHostAddress + ":8083/payments"));
        return responseBuilder;
    }

    @Get("/checkout")
    public void serveCheckout() {
    }

    @Get("/payments")
    public void servePayments() {
    }

    @Get("/splunk/trace/{traceId}/exitspan")
    public Span getSplunkTrace(String traceId) {
        log.info("Received request to fetch traceID: {}", traceId);
        Span resp = splunkO11yDataFetcherService.getExistSpanFromTraceAPI(traceId);
        log.info("Received exit span for Trace id {} - {}", traceId, resp);
        return resp;
    }

    @Get("/splunk/trace/local/exitspan")
    public Span getSplunkTraceFromLocal() throws IOException {
        return splunkO11yDataFetcherService.getExistSpanFromLocalTrace();
    }

    @Post("/splunk/alert/webhook")
    public void postAlertData(@Body SplunkAlert body) throws IOException {
        log.info("Splunk alert data: {}", body);
        LocalFileWriter.save(body.getDetector().trim() + "-" + body.getDetectorId() , body);
    }


    @Get("/splunk/metrics/{serviceName}")
    public SplunkMTS getSplunkMTS(@PathVariable("serviceName") String serviceName) {
        log.info("Received request to fetch mts for serviceName: {}", serviceName);
        SplunkMTS resp = splunkO11yDataFetcherService.getMTS(serviceName);
        log.info("Serialized MTS: {} ", resp);
        return resp;
    }

    @Get("/splunk/topology")
    public SplunkTopology getSplunkTopology() {
        SplunkTopology resp = splunkO11yDataFetcherService.getTopology();
        log.info("Topology data {}", resp);
        LocalFileWriter.save("topology", resp);
        return resp;
    }

    @Get("/splunk/metrics/timeseries/{serviceName}/{metricName}")
    public String getSplunkTimeSeriesWindow(@PathVariable("serviceName") String serviceName, @PathVariable("metricName") String metricName) {
        log.info("Received request to fetch Time Series for serviceName: {} and metric: {}", serviceName, metricName);
        String resp = splunkO11yDataFetcherService.getTimeSeriesWindow(serviceName, metricName);
        LocalFileWriter.save(serviceName + "-" + metricName, resp);
        log.info("Serialized MTS for service {} & metric name {} -- {} ",serviceName, metricName, resp);
        return resp;
    }

    @Get("/splunk/allMTS")
    public String getAllMTS() {
        return splunkO11yDataFetcherService.getAllMTS();
    }

    @Get("/splunk/allTimeSeries")
    public String getAllTimeSeries() {
        return splunkO11yDataFetcherService.getAllTimeSeries();
    }

    @Get("/{dynamicEndpoint}")
    public String handleRequest(String dynamicEndpoint) {
        log.info("===================================");
        log.info("Dynamic request: {}", dynamicEndpoint);
        EndpointConfig.Endpoint endpoint = endpointConfig.getEndpoints().stream()
            .filter(e -> e.getUrl().equalsIgnoreCase(dynamicEndpoint))
            .findFirst()
            .orElseThrow(() -> new IllegalArgumentException("Endpoint not found"));

        StringBuilder responseBuilder = new StringBuilder();
        for (String action : endpoint.getActions()) {
            log.info("-----------------------------------");
            String[] parts = action.split("\\|");
            String actionType = parts[0];
            String actionValue = parts[1];
            log.info("Action type: {} , Action value: {}", actionType, actionValue);
            switch (actionType) {
                case "request":
                    log.info("Making request to: {}", actionValue);
                    String response = httpClient.toBlocking().retrieve(actionValue);
                    responseBuilder.append(response);
                    break;
                case "wait_random":
                    try {
                        long waitTime = ThreadLocalRandom.current().nextLong(0, Long.parseLong(actionValue.replace("ms", "")));
                        log.info("Waiting for {} ms" , waitTime);
                        Thread.sleep(waitTime);
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    }
                    break;
                // Add more cases for other action types
            }
        }
        log.info("===================================");
        return responseBuilder.toString();
    }
}