package com.example.server.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Random;
import java.util.stream.Collectors;

@Service
public class UploadAddrService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    public String getRandomUploadAddr() {
        // 获取 ZSet 中的所有成员及其分数
        List<String> addrs = redisTemplate.opsForZSet().rangeWithScores("upload-addr-zset", 0, -1)
                .stream()
                .map(entry -> entry.getValue())
                .collect(Collectors.toList());

        List<Double> weights = redisTemplate.opsForZSet().rangeWithScores("upload-addr-zset", 0, -1)
                .stream()
                .map(entry -> entry.getScore())
                .collect(Collectors.toList());

        if (addrs.isEmpty()) {
            return null;
        }

        // 计算总权重
        double totalWeight = weights.stream().mapToDouble(Double::doubleValue).sum();

        // 生成一个随机数
        Random random = new Random();
        double randomWeight = random.nextDouble() * totalWeight;

        // 按权重选择一个地址
        double cumulativeWeight = 0.0;
        for (int i = 0; i < addrs.size(); i++) {
            cumulativeWeight += weights.get(i);
            if (randomWeight <= cumulativeWeight) {
                return addrs.get(i);
            }
        }

        return null; // 如果没有找到合适的地址，返回 null
    }
}
