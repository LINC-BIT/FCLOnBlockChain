package com.example.server.entity.dto;

import com.example.server.constant.TaskStatus;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.sql.Timestamp;

@Data
@NoArgsConstructor
public class TaskInQueueDto {
    private int priority;
    private int taskId;
    private Timestamp submitTime;
    private int estimatedDuration;
    private String status = TaskStatus.UNKNOWN.toString();
    private String taskType = "";
    private String submitter = "";
    private Timestamp deadline = Timestamp.valueOf("9999-12-31 23:59:59");
    private String description = "";
}