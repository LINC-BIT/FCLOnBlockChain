package com.example.server.mapper;


import com.example.server.entity.FileChunk;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * @author HTT
 */
@Mapper
public interface FileChunkMapper {

    public List<FileChunk> findFileChunkParamByMd5(String identifier);

    public List<FileChunk> findFileChunkParamByMd5AndChunkSize(@Param("identifier")String identifier, @Param("chunkSize")long chunkSize);

    public Integer findCountByMd5(String identifier);

    public int insertFileChunk(FileChunk fileChunk);
}

