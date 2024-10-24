package dev.coral.controllers;

import dev.coral.config.EndpointConfig;
import dev.coral.service.SplunkO11yDataFetcherService;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.PathVariable;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.scheduling.TaskExecutors;
import io.micronaut.scheduling.annotation.ExecuteOn;
import jakarta.inject.Inject;
import java.io.IOException;
import lombok.extern.slf4j.Slf4j;
import java.util.concurrent.ThreadLocalRandom;

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

    @Get("/splunk/trace/{traceId}/exitspan")
    public void getSplunkTrace(String traceId) {
        System.out.println("Received request to fetch traceID: " + traceId);
        System.out.println("Received Trace for service: " + splunkO11yDataFetcherService.getExistSpanFromTraceAPI(traceId));
    }

    @Get("/splunk/trace/local/exitspan")
    public void getSplunkTraceFromLocal() throws IOException {
        System.out.println("Received Trace for service: " + splunkO11yDataFetcherService.getExistSpanFromLocalTrace());

    @Get("/splunk/metrics/{serviceName}")
    public void getSplunkMTS(@PathVariable("serviceName") String serviceName) {
        log.info("Received request to fetch mts for serviceName: {}", serviceName);
        log.info("Serialized MTS: {} ", splunkO11yDataFetcherService.getMTS(serviceName));
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