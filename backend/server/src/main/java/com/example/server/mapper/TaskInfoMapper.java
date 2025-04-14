package com.example.server.mapper;

import com.example.server.entity.TaskInfo;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface TaskInfoMapper {

    Long insertTask(TaskInfo task);

    int updateTaskStatusById(TaskInfo task);

    List<TaskInfo> getAllTasks();

    List<TaskInfo> getTasksByTaskName(String taskName);
}