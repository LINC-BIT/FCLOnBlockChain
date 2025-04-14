package com.example.server.mapper;

import com.example.server.entity.FileInfo;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface FileInfoMapper {

    int insert(FileInfo fileInfo);

    List<FileInfo> selectByFileHash(String fileHash);

    List<FileInfo> selectByFileName(String fileName);
}
