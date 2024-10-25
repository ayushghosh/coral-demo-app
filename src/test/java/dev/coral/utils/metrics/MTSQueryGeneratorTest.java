package dev.coral.utils.metrics;

import org.junit.jupiter.api.Test;

class MTSQueryGeneratorTest {

  @Test
  void testGenerateTimeRange() {
    String resp = MTSQueryGenerator.generateTimeRange(10);
    System.out.println(resp);
  }
}