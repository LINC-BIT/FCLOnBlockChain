package com.example.server.demos.web;

import com.example.server.entity.DataInfo;
import com.example.server.service.DataInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/data-info")
public class DataInfoController {

    @Autowired
    private DataInfoService fileInfoService;

    @PostMapping
    public String createDataInfo(@RequestBody DataInfo fileInfo) {
        fileInfoService.addDataInfo(fileInfo);
        return "File info created successfully";
    }

    @GetMapping
    public List<DataInfo> getAllDataInfos() {
        return fileInfoService.getAllDataInfo();
    }
}