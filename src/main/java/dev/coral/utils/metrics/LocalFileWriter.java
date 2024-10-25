package dev.coral.utils.metrics;

import java.io.File;
import java.io.FileWriter;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

import com.fasterxml.jackson.databind.ObjectMapper;


import lombok.extern.slf4j.Slf4j;

@Slf4j
public class LocalFileWriter {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    public static void save(String fileName, Object content) {
        String userHome = System.getProperty("user.home");
        Path folderPath = Paths.get(userHome, ".coral");

        File directory = folderPath.toFile();
        if (!directory.exists()) {
            directory.mkdirs();
        }

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd_hh-mm-ss-a");
        String timestamp = LocalDateTime.now().format(formatter);
        fileName = fileName + "_" + timestamp + ".json";

        Path filePath = folderPath.resolve(fileName);

        try (FileWriter writer = new FileWriter(filePath.toFile())) {
            writer.write(getContentAsString(content));
        } catch (Exception e) {
            log.error("Error writing file {}", fileName, e);
        }
    }

    private static String getContentAsString(Object content) throws Exception {
        if (content instanceof String) {
            return (String) content;
        }
        return MAPPER.writerWithDefaultPrettyPrinter().writeValueAsString(content);
    }
}
