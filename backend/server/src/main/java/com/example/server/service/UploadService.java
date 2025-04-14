package com.example.server.service;


import com.example.server.entity.DataInfo;
import com.example.server.entity.FileChunk;
import com.example.server.entity.FileInfo;
import com.example.server.entity.dto.FileDataDto;
import com.example.server.mapper.DataInfoMapper;
import com.example.server.mapper.FileChunkMapper;
import com.example.server.mapper.FileInfoMapper;
import com.example.server.tools.AjaxResult;
import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Value;

import javax.annotation.Resource;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

/**
 * @author HTT
 */
@Service
public class UploadService {

    /**
     * 默认的分片大小：50MB
     * DataInfo保存的是文件在minio中的存储信息, FileInfo保存文件的描述信息
     * 可以通过taskId查询DataInfo并下载文件，而FileInfo目前则不怎么使用
     */
    public static final long DEFAULT_CHUNK_SIZE = 50 * 1024 * 1024;

    @Resource
    private FileChunkMapper fileChunkMapper;

    @Resource
    private FileInfoMapper fileInfoMapper;

    @Resource
    private DataInfoMapper dataInfoMapper;

    @Resource
    private MinioClient minioClient;

    @Value("${minio.bucket-name}")
    private String bucketName;

    public AjaxResult checkUpload(FileDataDto fileDataDto) {
        Map<String, Object> data = new HashMap<>(1);
        List<FileInfo> fileList = fileInfoMapper.selectByFileHash(fileDataDto.getIdentifier());
        // 判断文件存不存在
        if (fileList != null && fileList.size() != 0) {
            data.put("uploaded", true);
            // 文件存在，但文件信息不存在；将未写入的文件信息保存到data_info
            DataInfo dataInfo = new DataInfo();
            dataInfo.setFileName(fileList.get(0).getOriginFileName());
            dataInfo.setSubmitterId(fileDataDto.getSubmitterId());
            dataInfo.setFileBucket(bucketName);
            dataInfo.setFileKey(fileList.get(0).getFilePath());
            dataInfo.setVersion(fileDataDto.getVersion()); // 可以根据需要设置版本号
            dataInfo.setDataStatus("active"); // 可以根据需要设置数据状态
            dataInfo.setSubmitTime(new Date());
            dataInfo.setMetadata("{\"message\": \"This is a test file\"}"); // 可以根据需要设置元数据
            dataInfo.setTaskId(fileDataDto.getTaskId());
            dataInfo.setVersion("1.0");
            dataInfoMapper.insertDataInfo(dataInfo);
            return AjaxResult.success("文件已上传成功",data);
        }
        List<FileChunk> list = fileChunkMapper.findFileChunkParamByMd5AndChunkSize(fileDataDto.getIdentifier(), fileDataDto.getChunkSize());
        // 判断文件存不存在
        if (list == null || list.size() == 0) {
            data.put("uploaded", false); // false表示不存在
            return AjaxResult.success("文件未上传",data);
        } else if(list.size() == list.get(0).getTotalChunks()) {
            data.put("uploaded", true);
            // 文件存在，但文件信息不存在；将未写入的文件信息保存到data_info
            DataInfo dataInfo = new DataInfo();
            dataInfo.setFileName(fileList.get(0).getOriginFileName());
            dataInfo.setSubmitterId(fileDataDto.getSubmitterId());
            dataInfo.setFileBucket(bucketName);
            dataInfo.setFileKey(fileList.get(0).getFilePath());
            dataInfo.setVersion("1.0"); // 可以根据需要设置版本号
            dataInfo.setDataStatus("active"); // 可以根据需要设置数据状态
            dataInfo.setSubmitTime(new Date());
            dataInfo.setMetadata("{\"message\": \"This is a test file\"}"); // 可以根据需要设置元数据
            dataInfo.setTaskId(fileDataDto.getTaskId());
            dataInfo.setVersion("1.0");
            dataInfoMapper.insertDataInfo(dataInfo);
            return AjaxResult.success("文件已上传成功",data);
        }

        // 如果查询到多片数据，则表示这是一个分片上传的大文件
        // 遍历这些分片数据，获取每个文件块的编号保存到uploadedFiles数组中
        // 最后返回uploadedChunks（包含分块序号）给前端
        int[] uploadedFiles = new int[list.size()];
        int index = 0;
        for (FileChunk fileChunkItem : list) {
            uploadedFiles[index] = fileChunkItem.getChunkNumber();
            index++;
        }
        data.put("uploadedChunks", uploadedFiles);
        return AjaxResult.success("缺少分片未上传",data);
    }

    /**
     * 上传一个分片文件
     * @param fileChunk
     * @return
     * @throws Exception
     */
    public AjaxResult uploadChunkFile(FileChunk fileChunk) throws IOException {
        // 前端将md5作为文件名，文件名不能有中文，否则生成的url会失效
        int idx = fileChunk.getFilename().indexOf('.');
        String extension;
        if(idx==-1)
            extension= "";
        else {
            extension = fileChunk.getFilename().substring(idx + 1);;
        }

        String newFileName = fileChunk.getIdentifier() + "." + extension;
        String filePath = "C:\\Users\\keqiu\\Desktop\\tmp\\" + fileChunk.getChunkSize() + newFileName;
        // 将分片写入文件
        uploadFileByRandomAccessFile(filePath, fileChunk);
        fileChunk.setCreateTime(new Date());
        // 注意：insert不会插入分片内容到数据库
        fileChunkMapper.insertFileChunk(fileChunk);
//        List<FileChunk> list = fileChunkMapper.findFileChunkParamByMd5(fileChunk.getIdentifier());

        // 数据库中已上传的分片总数
        Integer count = fileChunkMapper.findCountByMd5(fileChunk.getIdentifier());
        // 写入文件信息
        if(fileChunk.getTotalChunks().equals(count)){
            String keyName = "";
            try {
                File file = new File(filePath);
                FileInputStream fileInputStream = new FileInputStream(file);
                keyName = file.getName(); // 对象名称，即MinIO中的文件名
                minioClient.putObject(PutObjectArgs.builder()
                        .bucket(bucketName)
                        .object(keyName)
                        .stream(fileInputStream , fileInputStream.available(), -1)
                        .build());
            }
            catch (Exception e) {
                e.printStackTrace();
                return AjaxResult.error(500, "上传失败");
            }
            FileInfo fileInfo = new FileInfo();
            String originalFilename = fileChunk.getFile().getOriginalFilename();
            fileInfo.setId(UUID.randomUUID().toString());
            fileInfo.setOriginFileName(originalFilename);
            fileInfo.setFileName(newFileName);
            fileInfo.setFilePath(keyName);
            fileInfo.setFileSize(fileChunk.getTotalSize());
            fileInfo.setCreateTime(new Date());
            fileInfo.setFileHash(fileChunk.getIdentifier());
            fileInfoMapper.insert(fileInfo);

            DataInfo dataInfo = new DataInfo();
            dataInfo.setFileName(originalFilename);
            dataInfo.setSubmitterId(fileChunk.getSubId()); // 假设FileChunk中有一个submitterId字段
            dataInfo.setFileBucket(bucketName);
            dataInfo.setFileKey(keyName);
            dataInfo.setVersion("1.0"); // 可以根据需要设置版本号
            dataInfo.setDataStatus("active"); // 可以根据需要设置数据状态
            dataInfo.setSubmitTime(new Date());
            dataInfo.setMetadata("{\"message\": \"This is a test file\"}"); // 可以根据需要设置元数据
            dataInfo.setTaskId(fileChunk.getTaskId());
            dataInfo.setVersion("1.0");
            dataInfoMapper.insertDataInfo(dataInfo);

        }
        return AjaxResult.success("文件上传成功");
    }

    // 将分片写入文件
    private void uploadFileByRandomAccessFile(String filePath, FileChunk fileChunk) throws IOException {

        RandomAccessFile randomAccessFile = new RandomAccessFile(filePath, "rw");
        // 分片大小必须和前端匹配，否则上传会导致文件损坏
        long chunkSize = fileChunk.getChunkSize() == 0L ? DEFAULT_CHUNK_SIZE : fileChunk.getChunkSize().longValue();
        // 偏移量
        long offset = chunkSize * (fileChunk.getChunkNumber() - 1);
        // 定位到该分片的偏移量
        randomAccessFile.seek(offset);
        // 写入
        randomAccessFile.write(fileChunk.getFile().getBytes());
        randomAccessFile.close();
    }


}
