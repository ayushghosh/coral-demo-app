package dev.coral.utils.metrics;

import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

public class MTSQueryGenerator {

    public static String generateQueryForService(String serviceName) {
        Long currentTime = System.currentTimeMillis();
        Long anHourAgoTime = currentTime - 60 * 15 * 1000;
        return String.format("service.name:%s AND created:[%d TO %d]", serviceName, anHourAgoTime, currentTime);
    }

    public static String generateQueryForService(String serviceName, Long secondsInPast) {
        Long currentTime = System.currentTimeMillis();
        Long anHourAgoTime = currentTime - (secondsInPast * 1000);
        return String.format("service.name:%s AND created:[%d TO %d]", serviceName, anHourAgoTime, currentTime);
    }

    public static String appendCountToQuery(String query, int count) {
        return String.format(query+"&limit=%d", count);
    }

    public static String generateTimeRange(long minutesInPast) {
        long currentTime = System.currentTimeMillis();

      // Format to the desired output
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'")
            .withZone(ZoneOffset.UTC);

        String to = formatter.format(Instant.ofEpochMilli(currentTime));
        String from = formatter.format(Instant.ofEpochMilli(currentTime - (minutesInPast * 60000)));

        return String.format("%s/%s", from, to);
    }
}
