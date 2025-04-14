package com.example.server.entity;

import lombok.Data;
import java.util.Date;

@Data
public class TaskInfo {

    /**
     * 主键，自动增长
     */
    private Long id;

    /**
     * 任务名
     */
    private String taskName;

    /**
     * 任务创建者id
     */
    private Long submitterId;

    /**
     * 任务类型
     */
    private String taskType;

    /**
     * 任务状态
     */
    private String taskStatus;

    /**
     * 任务创建时间
     */
    private Date submitTime;

    /**
     * 任务更新时间
     */
    private Date updateTime;

    /**
     * 需求的文件数
     */
    private Long fileNumber;

    /**
     * 文件的其他元数据，JSON格式
     */
    private String metadata;

}