package com.example.server.demos.web;


import com.example.server.entity.FileChunk;
import com.example.server.entity.dto.FileDataDto;
import com.example.server.service.FileDownloadService;
import com.example.server.service.UploadService;
import com.example.server.tools.AjaxResult;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;

@RestController
@RequestMapping("/file")
public class FileController {

    @Resource
    private UploadService uploadService;

    @Resource
    private FileDownloadService fileDownloadService;

    @GetMapping("/upload")
    public AjaxResult checkUpload(FileDataDto fileDataDto){
        return uploadService.checkUpload(fileDataDto);
    }

    @PostMapping("/upload")
    public AjaxResult uploadChunkFile(FileChunk fileChunk) throws Exception {
        return uploadService.uploadChunkFile(fileChunk);
    }

    @GetMapping("/key-with-id")
    public AjaxResult getFileKeyById(long taskId){
        return AjaxResult.success("",fileDownloadService.getDataInfoByTaskId(taskId));
    }

    @GetMapping("/key-with-name")
    public AjaxResult getFileKeyByName(String taskName){
        return AjaxResult.success("",fileDownloadService.getDataInfoByTaskName(taskName));
    }

    @GetMapping("/download")
    public AjaxResult download(String fileKey){
        return AjaxResult.success("",fileDownloadService.generatePresignedUrl(fileKey));
    }

}

