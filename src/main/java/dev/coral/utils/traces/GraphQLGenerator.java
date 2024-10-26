package dev.coral.utils.traces;

public class GraphQLGenerator {

    public static String generateGetTraceIdQuery(String jobId) {
        String jsonString = "{"
                + "\"operationName\": \"GetExemplarTraceSearchJob\","
                + "\"variables\": {"
                + "\"jobID\": \"" + jobId + "\""
                + "},"
                + "\"query\": \"fragment CompactTraceIdSearchResponseFragment on ExemplarTraceSearchQueryResults {\\n  jobID\\n  completedProcessingItems\\n  totalItemsToProcess\\n  results {\\n    startOffset\\n    totalItems\\n    items {\\n      item {\\n        traceId\\n        initiatingService\\n        initiatingOperation\\n        initiatingHttpMethod\\n        initiatingSpanWasError\\n        startTimeMicros\\n        durationMicros\\n        serviceSpanCounts {\\n          service\\n          spanCount\\n          errors {\\n            spanID\\n            isRootCause\\n            error {\\n              code\\n              message\\n              __typename\\n            }\\n            __typename\\n          }\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n  __typename\\n}\\n\\nquery GetExemplarTraceSearchJob($jobID: ID!, $offset: Int, $limit: Int) {\\n  getExemplarSearch(jobID: $jobID, offset: $offset, limit: $limit) {\\n    ...CompactTraceIdSearchResponseFragment\\n    __typename\\n  }\\n}\\n\""
                + "}";
        return jsonString;
    }

    public static String generateTraceSearchQuery(String serviceName) {
        Long currentTime = System.currentTimeMillis();
        Long anHourAgoTime = currentTime - 60 * 15 * 1000;

        String jsonString = "{"
                + "\"operationName\":\"StartExemplarTraceSearchJob\","
                + "\"variables\":{"
                + "\"filters\":[{"
                + "\"traceFilter\":{\"tags\":[]},"
                + "\"spanFilters\":[{"
                + "\"tags\":[{"
                + "\"tag\":\"sf_service\",\"operation\":\"IN\",\"values\":[\"" + serviceName + "\"]},{"
                + "\"tag\":\"_sf_serviceRoot\",\"operation\":\"IN\",\"values\":[\"true\"]}]}]}"
                + "],"
                + "\"timeRangeMillis\":{\"gte\":" + anHourAgoTime + ".6636,\"lte\":" + currentTime + ".6636},"
                + "\"exemplar\":{\"exemplarType\":\"err\"},"
                + "\"source\":\"mms\","
                + "\"limit\":5"
                + "},"
                + "\"query\":\"fragment CompactTraceIdSearchResponseFragment on ExemplarTraceSearchQueryResults {\\n  jobID\\n  completedProcessingItems\\n  totalItemsToProcess\\n  results {\\n    startOffset\\n    totalItems\\n    items {\\n      item {\\n        traceId\\n        initiatingService\\n        initiatingOperation\\n        initiatingHttpMethod\\n        initiatingSpanWasError\\n        startTimeMicros\\n        durationMicros\\n        serviceSpanCounts {\\n          service\\n          spanCount\\n          errors {\\n            spanID\\n            isRootCause\\n            error {\\n              code\\n              message\\n              __typename\\n            }\\n            __typename\\n          }\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n  __typename\\n}\\n\\nquery StartExemplarTraceSearchJob($timeRangeMillis: RangeInput!, $filters: [TraceFilterInput!]!, $source: String, $limit: Int, $exemplar: ExemplarInput) {\\n  startExemplarSearch(\\n    timeRangeMillis: $timeRangeMillis\\n    filters: $filters\\n    limit: $limit\\n    exemplar: $exemplar\\n    source: $source\\n  ) {\\n    ...CompactTraceIdSearchResponseFragment\\n    __typename\\n  }\\n}\""
                + "}";

       return jsonString;
    }
}
