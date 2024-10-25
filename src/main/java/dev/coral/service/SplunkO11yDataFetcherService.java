package dev.coral.service;

import java.io.File;
import java.io.IOException;
import java.util.*;

import com.fasterxml.jackson.databind.ObjectMapper;


import dev.coral.client.splunk.SplunkO11yHttpClient;
import dev.coral.model.SplunkMTS;
import dev.coral.model.SplunkTopology;
import dev.coral.utils.metrics.MTSQueryGenerator;
import dev.coral.utils.metrics.TimeSeriesWindowQueryGenerator;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Singleton
public class SplunkO11yDataFetcherService {

    private final SplunkO11yHttpClient splunkO11yHttpClient;
    private final String SFX_TOKEN;
    private SplunkTopology.SplunkTopologyData splunkTopologyData;
    private Map<String, Set<String>> allMTSs; // Service to MetricName map
    private Map<String, Map<String, String>> allSplunkData; //Service to metricName to Data map

    @Inject
    public SplunkO11yDataFetcherService(SplunkO11yHttpClient splunkO11yHttpClient) {
        this.splunkO11yHttpClient = splunkO11yHttpClient;
        this.SFX_TOKEN = System.getenv("SIGNALFX_API_TOKEN");
        this.allMTSs = new HashMap<>();
        this.allSplunkData = new HashMap<>();
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
    }

    public SplunkMTS getMTS(String serviceName) {
        String query = MTSQueryGenerator.generateQueryForService(serviceName);
        log.info("Query: {}", query);
        SplunkMTS resp = splunkO11yHttpClient.getMts(SFX_TOKEN, query, 1);
        return splunkO11yHttpClient.getMts(SFX_TOKEN, query, resp.getCount());
    }

    public SplunkTopology getTopology() {
        String body = String.format("{ \"timeRange\": \"%s\"}", MTSQueryGenerator.generateTimeRange(15));
        SplunkTopology resp = splunkO11yHttpClient.getSplunkTopology(SFX_TOKEN, body);
        splunkTopologyData = resp.getData();
        return resp;
    }

    public String getTimeSeriesWindow(String serviceName, String metricName) {
        String query = TimeSeriesWindowQueryGenerator.generateQueryForService(serviceName, metricName);
        long to = System.currentTimeMillis();
        long from = to - (60 * 15 * 1000);
        long resolution = 1000;
        log.info("Query: {}", query);
        String resp = splunkO11yHttpClient.getTimeSeriesWindow(SFX_TOKEN, query, from, to, resolution);
        log.info("Response: {}", resp);
        return resp;
    }

    public String getAllMTS() {
        if (splunkTopologyData == null) {
            return "Fetch topology data first";
        }

        for (SplunkTopology.Node node: splunkTopologyData.getNodes()) {
            String serviceName = node.getServiceName();
            try {
                SplunkMTS splunkMTS = getMTS(serviceName);
                Set<String> metricsForAService = allMTSs.getOrDefault(serviceName, new HashSet<>());
                for (SplunkMTS.Result singleMTS: splunkMTS.getResults()) {
                    metricsForAService.add(singleMTS.getMetric());
                }
                allMTSs.put(serviceName, metricsForAService);
            } catch (Exception e) {
                log.warn("Continuing while getting exception finding metrics for service {}", serviceName);
            }
        }

        log.info("All MTSs: {}", allMTSs);
        return allMTSs.keySet().toString();
    }

    public String getAllTimeSeries() {
        if (allMTSs.isEmpty()) {
            return "Fetch all MTSs first";
        }

        for (String serviceName: allMTSs.keySet()) {
            Map<String, String> metricToData = allSplunkData.getOrDefault(serviceName, new HashMap<>());
            for (String metricName: allMTSs.get(serviceName)) {
                String timeSeriesData = getTimeSeriesWindow(serviceName, metricName);

                metricToData.put(metricName, timeSeriesData);
            }
            allSplunkData.put(serviceName, metricToData);
        }

        log.info(allSplunkData.toString());
        return "All Time Series Data Fetched";
    }

    public Map<String, Map<String, String>> fetchAllSplunkData() {
        getTopology();
        getAllMTS();
        getAllTimeSeries();
        return allSplunkData;
    }
}