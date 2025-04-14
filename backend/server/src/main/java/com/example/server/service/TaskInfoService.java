package com.example.server.service;

import com.example.server.entity.TaskInfo;
import com.example.server.mapper.TaskInfoMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class TaskInfoService {

    @Autowired
    private TaskInfoMapper taskInfoMapper;

    public Long addTaskInfo(TaskInfo task) {
        taskInfoMapper.insertTask(task);
        return task.getId();
    }

    public void updateTaskStatusById(TaskInfo task) {
        taskInfoMapper.updateTaskStatusById(task);
    }

    public List<TaskInfo> getAllTaskInfo() {
        return taskInfoMapper.getAllTasks();
    }

    public List<TaskInfo> getTaskInfoByName(String taskName) {
        return taskInfoMapper.getTasksByTaskName(taskName);
    }

}
