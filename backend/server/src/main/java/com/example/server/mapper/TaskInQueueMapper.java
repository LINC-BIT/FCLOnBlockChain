package com.example.server.mapper;



import com.example.server.entity.Task;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface TaskInQueueMapper {
//    @Insert("INSERT INTO submitted_task (task_id, priority, submit_time, estimated_duration, status, task_type, submitter, deadline, description) " +
//            "VALUES (#{taskId}, #{priority}, #{submitTime}, #{estimatedDuration}, #{status}, #{taskType}, #{submitter}, #{deadline}, #{description})")
    void insertTask(Task task);

//    @Select("SELECT * FROM submitted_task WHERE status = 'IN_QUEUE'")
    List<Task> fetchInQueueTasks();

//    @Update("UPDATE submitted_task SET status = 'COMPLETED' WHERE task_id = #{taskId}")
    void markTaskAsCompleted(int taskId);
}