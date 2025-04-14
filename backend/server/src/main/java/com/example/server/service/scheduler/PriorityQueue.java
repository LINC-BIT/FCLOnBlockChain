package com.example.server.service.scheduler;


import com.example.server.entity.Task;

public class PriorityQueue extends ThreadSafeQueue<Task> {
    private java.util.PriorityQueue<Task> queue = new java.util.PriorityQueue<>();

    @Override
    public void enqueue(Task task) {
        queue.offer(task);
    }

    @Override
    public Task dequeue() {
        return queue.poll();
    }

    @Override
    public boolean isEmpty() {
        return queue.isEmpty();
    }
}