package dev.coral.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import dev.coral.client.splunk.SplunkO11yHttpClient;
import dev.coral.utils.metrics.MTSQueryGenerator;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

@Singleton
public class SplunkO11yDataFetcherService {

    private final SplunkO11yHttpClient splunkO11yHttpClient;
    private final String SFX_TOKEN;

    @Inject
    public SplunkO11yDataFetcherService(SplunkO11yHttpClient splunkO11yHttpClient) {
        this.splunkO11yHttpClient = splunkO11yHttpClient;
        this.SFX_TOKEN = System.getenv("SIGNALFX_API_TOKEN");
    }

    public Span getExistSpanFromTraceAPI(String traceId) {
        List<Span> trace = this.getTrace(traceId);
        return findExitSpanInTrace(trace);
    }

    private List<Span> getTrace(String traceID) {
        return splunkO11yHttpClient.getTraceById(SFX_TOKEN, traceID);
    }

    public Span getExistSpanFromLocalTrace() throws IOException {
        ObjectMapper objectMapper = new ObjectMapper();
        File file = new File("src/main/resources/json/trace.json");
        List<Span> traceFromLocal = Arrays.asList(objectMapper.readValue(file, Span[].class));
        return findExitSpanInTrace(traceFromLocal);
    }

    private Span findExitSpanInTrace(List<Span> trace) {
        return trace.stream().max(Comparator.comparing(Span::getStartTime)).get();

    public String getMTS(String serviceName) {
        String query = MTSQueryGenerator.generateQueryForService("signalboost");
        return splunkO11yHttpClient.getMts(SFX_TOKEN, query);
    }
}