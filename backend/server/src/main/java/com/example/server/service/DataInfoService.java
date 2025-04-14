package com.example.server.service;


import com.example.server.entity.DataInfo;
import com.example.server.mapper.DataInfoMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class DataInfoService {

    @Autowired
    private DataInfoMapper dataInfoMapper;

    public void addDataInfo(DataInfo fileInfo) {
        dataInfoMapper.insertDataInfo(fileInfo);
    }

    public List<DataInfo> getAllDataInfo() {
        return dataInfoMapper.getAllDataInfo();
    }
}