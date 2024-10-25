package dev.coral.utils.metrics;

import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

public class TimeSeriesWindowQueryGenerator {

    public static String generateQueryForService(String serviceName, String metricName) {
        return String.format("(sf_metric:%s AND sf_service:%s)", metricName, serviceName);
    }
}
