package dev.coral.service;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import io.micronaut.core.annotation.Introspected;
import io.micronaut.serde.annotation.Serdeable;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@ToString
@Introspected
@Serdeable
@JsonIgnoreProperties(ignoreUnknown = true)
public class Span {
    private String traceId;
    private String spanId;
    private Object parentId;
    private String serviceName;
    private String operationName;
    private String startTime;
    private Integer durationMicros;
    private String objectType;
}
