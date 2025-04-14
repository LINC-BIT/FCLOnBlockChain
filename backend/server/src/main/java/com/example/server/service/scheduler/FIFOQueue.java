package com.example.server.service.scheduler;


import com.example.server.entity.Task;

class FIFOQueue extends ThreadSafeQueue<Task> {}
