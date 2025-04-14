package com.example.server.script;

import com.alibaba.cloud.nacos.NacosDiscoveryProperties;
import com.alibaba.cloud.nacos.discovery.NacosServiceDiscovery;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.data.redis.core.RedisTemplate;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Component
public class ScheduledTasks {

    @Autowired
    private DiscoveryClient discoveryClient;

    @Autowired
    private RedisTemplate<String, String> redisTemplate;


    @Scheduled(fixedDelay = 5000)
    public void fetchUploadUrlsAndStoreInRedis() {
        // 获取名为 "upload-service" 的服务的所有实例
        List<ServiceInstance> instances = discoveryClient.getInstances("upload-service");
//        System.out.println("定时检测可用上传端口并写入redis");
        if (instances != null && !instances.isEmpty()) {
            // 清除现有的 ZSet
            redisTemplate.delete("upload-addr-zset");

            // 提取每个实例的元数据中的 upload-addr 和 weight
            instances.stream()
                    .filter(instance -> instance.getMetadata() != null &&
                            instance.getMetadata().containsKey("upload-addr") &&
                            instance.getMetadata().containsKey("weight"))
                    .forEach(instance -> {
                        String uploadAddr = instance.getMetadata().get("upload-addr");
                        double weight = Double.parseDouble(instance.getMetadata().get("weight"));
                        redisTemplate.opsForZSet().add("upload-addr-zset", uploadAddr, weight);
                    });

            // 设置60秒的有效时间
            redisTemplate.expire("upload-addr-zset", 60, java.util.concurrent.TimeUnit.SECONDS);
        }
    }
}