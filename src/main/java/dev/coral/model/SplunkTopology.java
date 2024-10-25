package dev.coral.model;

import java.util.List;


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
public class SplunkTopology {
  private SplunkTopologyData data;

  @Data
  @Introspected
  @AllArgsConstructor
  @NoArgsConstructor
  @ToString
  @Serdeable
  public static class SplunkTopologyData {
    private List<Node> nodes;
    private List<Edge> edges;
  }

  @Data
  @Introspected
  @AllArgsConstructor
  @NoArgsConstructor
  @ToString
  @Serdeable
  public static class Node {
    private String serviceName;
    private boolean inferred;
    private String type;
  }

  @Data
  @Introspected
  @AllArgsConstructor
  @NoArgsConstructor
  @ToString
  @Serdeable
  public static class Edge {
    private String fromNode;
    private String toNode;
  }
}
