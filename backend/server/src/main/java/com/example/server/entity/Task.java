package com.example.server.entity;

import com.example.server.constant.TaskStatus;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.sql.Timestamp;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
public class Task implements Comparable<Task> {
    private long id;
    private int taskId;
    private int priority;
    private Timestamp submitTime;
    private int estimatedDuration;
    private String status = TaskStatus.UNKNOWN.toString();
    private String taskType = "";
    private String submitter = "";
    private Timestamp deadline;
    private String description;


    public Task(int taskId, int priority, int estimatedDuration) {
        this.priority = priority;
        this.estimatedDuration = estimatedDuration;
        this.taskId = taskId;
        this.submitTime = Timestamp.valueOf(LocalDateTime.now());
    }

    public Task(int taskId, int priority, int estimatedDuration, String status) {
        this.priority = priority;
        this.estimatedDuration = estimatedDuration;
        this.taskId = taskId;
        this.submitTime = Timestamp.valueOf(LocalDateTime.now());
        this.status = TaskStatus.fromString(status).toString();
    }

    @Override
    public int compareTo(Task other) {
        return Integer.compare(this.priority, other.priority);
    }

}