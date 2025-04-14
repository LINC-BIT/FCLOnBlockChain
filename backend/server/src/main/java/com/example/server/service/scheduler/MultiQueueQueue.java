package com.example.server.service.scheduler;


import com.example.server.entity.Task;

import java.util.ArrayList;
import java.util.Queue;
import java.util.concurrent.ConcurrentLinkedQueue;

public class MultiQueueQueue extends ThreadSafeQueue<Task> {
    private Queue<Task> shortQueue = new ConcurrentLinkedQueue<>();
    private Queue<Task> longQueue = new ConcurrentLinkedQueue<>();
    private final int shortThreshold;

    public MultiQueueQueue(int shortThreshold) {
        this.shortThreshold = shortThreshold;
    }

    public void enqueue(Task task) {
        if (task.getEstimatedDuration() <= shortThreshold) {
            shortQueue.offer(task);
        } else {
            longQueue.offer(task);
        }
    }

    public Task dequeue() {
        if (!shortQueue.isEmpty()) {
            return shortQueue.poll();
        } else if (!longQueue.isEmpty()) {
            return longQueue.poll();
        }
        return null;
    }

    public boolean isEmpty() {
        return shortQueue.isEmpty() && longQueue.isEmpty();
    }

    public void clear() {
        shortQueue.clear();
        longQueue.clear();
    }

    public ArrayList<Task> getAllTasks() {
        ArrayList<Task> allTasks = new ArrayList<>(shortQueue);
        allTasks.addAll(longQueue);
        return allTasks;
    }
}