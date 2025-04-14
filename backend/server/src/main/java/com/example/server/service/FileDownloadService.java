package com.example.server.service;

import com.example.server.entity.DataInfo;
import com.example.server.entity.FileInfo;
import com.example.server.entity.TaskInfo;
import com.example.server.mapper.DataInfoMapper;
import com.example.server.mapper.FileInfoMapper;
import com.example.server.mapper.TaskInfoMapper;
import io.minio.GetPresignedObjectUrlArgs;
import io.minio.MinioClient;
import io.minio.errors.MinioException;
import io.minio.http.Method;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.Date;
import java.util.List;
import java.util.concurrent.TimeUnit;

@Service
public class FileDownloadService {

    @Resource
    private MinioClient minioClient;

    @Resource
    private DataInfoMapper dataInfoMapper;

    @Resource
    private TaskInfoMapper taskInfoMapper;

    @Value("${minio.bucket-name}")
    private String bucketName;

    public String generatePresignedUrl(String fileKey) {
        try {
            return minioClient.getPresignedObjectUrl(
                    GetPresignedObjectUrlArgs.builder()
                            .method(Method.GET)
                            .bucket(bucketName)
                            .object(fileKey)
                            .expiry(3, TimeUnit.DAYS) // 一天过期时间
                            .build());
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    public List<DataInfo> getDataInfoByTaskId(long taskId) {
        return dataInfoMapper.getAllDataInfoByTaskId(taskId);
    }

    public List<DataInfo> getDataInfoByTaskName(String taskName) {
        Long taskId;
        List<TaskInfo> list = taskInfoMapper.getTasksByTaskName(taskName);
        System.out.println(taskName);
        System.out.println(list);
        if(list!=null && list.size()>0){
            taskId = list.get(list.size()-1).getId();
        } else {
            return null;
        }
        System.out.println(taskId);
        return dataInfoMapper.getAllDataInfoByTaskId(taskId);
    }
}
