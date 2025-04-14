package com.example.server.entity;


import lombok.Data;
import org.springframework.web.multipart.MultipartFile;

import java.io.Serializable;
import java.util.Date;

@Data
public class FileChunk implements Serializable {

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
     * 创建时间
     */
    private Date createTime;

    /**
     * 文件对应的taskId
     */
    private Long taskId;

    /**
     * 上传者Id
     */
    private Long subId;

    /**
     * 文件分片数据
     */
    private MultipartFile file;


}
