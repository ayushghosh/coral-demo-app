package dev.coral.model;

import java.util.List;
import java.util.Map;


import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Introspected
@Serdeable
public class SplunkMTS {

    private int count;
    private boolean partialCount;
    private List<Result> results;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Introspected
    @Serdeable
    public static class Result {
        private boolean active;
        private long created;
        private String creator;
        private Map<String, String> customProperties;
        private Dimensions dimensions;
        private String id;
        private long lastUpdated;
        private String lastUpdatedBy;
        private String metric;
        private String metricType;
        private String source;
        private List<String> tags;

        @Data
        @NoArgsConstructor
        @AllArgsConstructor
        @Introspected
        @Serdeable
        public static class Dimensions {
            private String endPoint;
            private String kubernetesNode;
            private String kubernetesPodUid;
            private String method;
            private String orgId;
            private String serviceName;
            private String sfMetric;
            private String sfSource;
            private String status;
            private String telemetrySdkLanguage;
            private String telemetrySdkName;
            private String telemetrySdkVersion;
        }
    }
}
