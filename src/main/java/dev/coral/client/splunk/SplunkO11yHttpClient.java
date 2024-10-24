package dev.coral.client.splunk;

import static io.micronaut.http.HttpHeaders.ACCEPT;

import dev.coral.service.Span;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Header;
import io.micronaut.http.annotation.Headers;
import io.micronaut.http.annotation.PathVariable;
import io.micronaut.http.annotation.QueryValue;
import io.micronaut.http.client.annotation.Client;
import java.util.List;

@Client("https://api.rc0.signalfx.com") // Base URL
public interface SplunkO11yHttpClient {

    @Get(value = "/v2/apm/trace/{traceId}/latest")
    @Headers(
        @Header(name = ACCEPT, value = "application/json")
    )
    List<Span> getTraceById(@Header("X-SF-Token") String sfxToken, @PathVariable String traceId);

    @Get(value = "/v2/metrictimeseries/")
    String getMts(@Header("X-SF-Token") String sfxToken, @QueryValue("query") String query);
}