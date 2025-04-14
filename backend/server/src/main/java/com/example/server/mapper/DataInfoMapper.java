package com.example.server.mapper;

import com.example.server.entity.DataInfo;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface DataInfoMapper {

    void insertDataInfo(DataInfo dataInfo);

    List<DataInfo> getAllDataInfo();

    List<DataInfo> getAllDataInfoByTaskId(@Param("taskId")long taskId);

    List<DataInfo> getAllDataInfoByParams(@Param("submitterId")long submitterId, @Param("taskId")long taskId,
                                            @Param("version")String version);
}