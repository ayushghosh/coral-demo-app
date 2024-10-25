package dev.coral.model;

import java.util.Map;


import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.ToString;

@Data
@Introspected
@AllArgsConstructor
@NoArgsConstructor
@ToString
@Serdeable
public class SplunkAlert {

    private String severity;
    private String originatingMetric;
    private String detectOnCondition;
    private String detectOffCondition;
    private String messageBody;
    private String src;
    private Map<String, InputData> inputs;
    private String rule;
    private String description;
    private String messageTitle;
    private int sfSchema;
    private String eventType;
    private String runbookUrl;
    private String orgId;
    private String detectorId;
    private String imageUrl;
    private String tip;
    private String statusExtended;
    private String incidentId;
    private String detector;
    private String detectorUrl;
    private String status;
    private String timestamp;
    private Map<String, String> dimensions;

    @Data
    @Introspected
    @AllArgsConstructor
    @NoArgsConstructor
    @ToString
    @Serdeable
    public static class InputData {
        private String value;
        private String fragment;
        private Key key;
    }

    @Data
    @Introspected
    @AllArgsConstructor
    @NoArgsConstructor
    @ToString
    @Serdeable
    public static class Key {
        private String endPoint;
        private String kubernetesNode;
        private String kubernetesPodUid;
        private String method;
        private String serviceName;
        private String sfMetric;
        private String sfSource;
        private String telemetrySdkLanguage;
        private String telemetrySdkName;
        private String telemetrySdkVersion;
    }
}

