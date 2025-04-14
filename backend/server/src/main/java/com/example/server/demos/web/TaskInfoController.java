package com.example.server.demos.web;

import com.example.server.entity.TaskInfo;
import com.example.server.service.TaskInfoService;
import com.example.server.tools.AjaxResult;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/task-info")
public class TaskInfoController {

    @Autowired
    private TaskInfoService taskService;

    @PostMapping
    public AjaxResult createTaskInfo(@RequestBody TaskInfo task) {
        Long taskId = taskService.addTaskInfo(task);
        Map<String, Object> data = new HashMap<>(1);
        data.put("taskId", taskId);
        return AjaxResult.success("任务已上传成功",data);
    }

    @PostMapping("/update")
    public String updateTaskInfo(@RequestBody TaskInfo task) {
        taskService.updateTaskStatusById(task);
        return "Task updated successfully";
    }

    @GetMapping("/name")
    public AjaxResult getTaskInfoByName(@RequestParam String taskName) {
        Map<String, Object> data = new HashMap<>(1);
        data.put("tasks", taskService.getTaskInfoByName(taskName));
        return AjaxResult.success("任务获取成功",data);
    }

    @GetMapping
    public List<TaskInfo> getAllTasks() {
        return taskService.getAllTaskInfo();
    }
}