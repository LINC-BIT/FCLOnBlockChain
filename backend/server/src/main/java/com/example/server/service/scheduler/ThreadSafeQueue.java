package com.example.server.service.scheduler;


import java.util.ArrayList;
import java.util.Queue;
import java.util.concurrent.ConcurrentLinkedQueue;

public class ThreadSafeQueue<T> {
    private Queue<T> queue = new ConcurrentLinkedQueue<>();

    public void enqueue(T item) {
        queue.offer(item);
    }

    public T dequeue() {
        return queue.poll();
    }

    public boolean isEmpty() {
        return queue.isEmpty();
    }

    public void clear() {
        queue.clear();
    }

    public ArrayList<T> getAllTasks() {
        return new ArrayList<>(queue);
    }
}