package dev.coral.controllers.democontrollers;

import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.scheduling.TaskExecutors;
import io.micronaut.scheduling.annotation.ExecuteOn;
import jakarta.inject.Inject;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Controller
@ExecuteOn(TaskExecutors.BLOCKING)
public class DemoServiceController {
    private final HttpClient httpClient;

    @Inject
    public DemoServiceController(@Client HttpClient httpClient) {
        this.httpClient = httpClient;
    }

    @Get("/orders")
    public StringBuilder getSplunkMTS() {
        log.info("Received order request, calling payment service and checkout service");
        StringBuilder responseBuilder = new StringBuilder();
        responseBuilder.append(httpClient.toBlocking().retrieve("http://localhost:8082/payments"));
        responseBuilder.append(httpClient.toBlocking().retrieve("http://localhost:8083/checkout"));
        return responseBuilder;
    }
}