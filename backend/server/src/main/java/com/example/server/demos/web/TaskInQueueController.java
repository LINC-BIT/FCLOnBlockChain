/*
 * Copyright 2013-2018 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.example.server.demos.web;


import com.example.server.entity.Task;
import com.example.server.entity.dto.TaskInQueueDto;
import com.example.server.service.scheduler.Scheduler;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;


/**
 * @author <a href="mailto:chenxilzx1@gmail.com">theonefx</a>
 */
@Controller
public class TaskInQueueController {

    @Autowired
    private Scheduler scheduler;

    @PostMapping("/task")
    @ResponseBody
    public void submitTask(@RequestBody TaskInQueueDto taskDto) {
        scheduler.enqueue(new Task(taskDto.getTaskId(), taskDto.getPriority(), taskDto.getEstimatedDuration(), taskDto.getStatus()));
    }

    @GetMapping("/task")
    @ResponseBody
    public Task getTask() {
        Task t = scheduler.dequeue();
        System.out.println(t);
        return t;
    }


}
