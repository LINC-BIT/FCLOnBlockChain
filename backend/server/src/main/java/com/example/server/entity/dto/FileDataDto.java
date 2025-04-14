package com.example.server.entity.dto;


import lombok.Data;
import org.springframework.web.multipart.MultipartFile;

import java.io.Serializable;
import java.util.Date;

@Data
public class FileDataDto implements Serializable {

    /**
     * 主键
     */
    private Long id;
    /**
     * 文件 md5
     */
    private String identifier;
    /**
     * 当前分块序号
     */
    private Integer chunkNumber;
    /**
     * 分块大小
     */
    private Long chunkSize;
    /**
     * 当前分块大小
     */
    private Long currentChunkSize;
    /**
     * 文件总大小
     */
    private Long totalSize;
    /**
     * 分块总数
     */
    private Integer totalChunks;
    /**
     * 文件名
     */
    private String filename;
    /**
     * 版本号
     */
    private String version;
    /**
     * 创建时间
     */
    private Date createTime;

    /**
     * 文件分片数据
     */
    private MultipartFile file;

    /**
     * 对应的任务id
     */
    private Long taskId;

    /**
     * 上传者id
     */
    private Long submitterId;
}
