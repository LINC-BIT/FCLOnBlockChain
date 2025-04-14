package com.example.server.service.scheduler;



import com.example.server.entity.Task;
import com.example.server.mapper.TaskInQueueMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
@Service
public class Scheduler {
    private String strategy;
    private final PriorityQueue priorityQueue = new PriorityQueue();
    private final MultiQueueQueue multiQueueQueue = new MultiQueueQueue(10);
    private final ShortestJobFirstQueue shortestJobFirstQueue = new ShortestJobFirstQueue();
    private final FIFOQueue fifoQueue = new FIFOQueue();
    private ThreadSafeQueue<Task> currentQueue;
    private final Lock lock = new ReentrantLock();
    private final Condition condition = lock.newCondition();
//    private final MysqlConnector dbConnector = new MysqlConnector();
    private final TaskInQueueMapper taskMapper;

    @Autowired
    public Scheduler(TaskInQueueMapper taskMapper) {
        // 默认使用优先级队列
        this.currentQueue = this.priorityQueue;
        this.taskMapper = taskMapper;
        try {
            List<Task> tasks = this.taskMapper.fetchInQueueTasks();
            if(tasks!=null){
                for(Task task: tasks){
                    this.currentQueue.enqueue(task);
                }
            }
        }
        catch (Exception e){
            System.out.println("读取数据库错误：");
            System.out.println(e);
        }
    }

    public void setStrategy(String strategy) {
        lock.lock();
        try {
            if (this.strategy.equals(strategy)) return;

            ArrayList<Task> tasks = currentQueue.getAllTasks();
            currentQueue.clear();

            switch (strategy) {
                case "priority":
                    currentQueue = priorityQueue;
                    break;
                case "multi":
                    currentQueue = multiQueueQueue;
                    break;
                case "sjf":
                    currentQueue = shortestJobFirstQueue;
                    break;
                case "fifo":
                    currentQueue = fifoQueue;
                    break;
                default:
                    throw new IllegalArgumentException("Unknown strategy: " + strategy);
            }

            for (Task task : tasks) {
                currentQueue.enqueue(task);
            }
            this.strategy = strategy;
        } finally {
            lock.unlock();
        }
    }

    public void enqueue(Task task) {
        lock.lock();
        try {
            // todo 先查询是否重复
            this.taskMapper.insertTask(task);
            currentQueue.enqueue(task);
        }
        catch (Exception e){
            System.out.println(e);
        }
        finally {
            lock.unlock();
        }
    }

    public Task dequeue() {
        lock.lock();
        try {
            Task task = currentQueue.dequeue();
            this.taskMapper.markTaskAsCompleted(task.getTaskId());
            return task;
        }
        catch (Exception e){
            System.out.println(e);
            // todo 失败是否重新入队？
        }
        finally {
            lock.unlock();
        }
        return null;
    }

    public boolean isEmpty() {
        lock.lock();
        try {
            return currentQueue.isEmpty();
        } finally {
            lock.unlock();
        }
    }

    public void close() {
        // TODO: Clear database
    }

    public void test(){
       System.out.println(this.taskMapper.fetchInQueueTasks());
       System.out.println("done");
    }
}
