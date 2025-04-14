package com.example.server.entity;

import lombok.Data;
import java.util.Date;

@Data
public class DataInfo {

    /**
     * 主键，自动增长
     */
    private Long id;

    /**
     * 文件名
     */
    private String fileName;

    /**
     * 数据提交者id
     */
    private Long submitterId;

    /**
     * 任务id
     */
    private Long taskId;

    /**
     * 文件在oss中的bucket名
     */
    private String fileBucket;

    /**
     * 文件在oss中的key
     */
    private String fileKey;

    /**
     * 数据版本
     */
    private String version;

    /**
     * 数据文件状态
     */
    private String dataStatus;

    /**
     * 任务创建时间
     */
    private Date submitTime;

    /**
     * 文件的其他元数据，JSON格式
     */
    private String metadata;
}