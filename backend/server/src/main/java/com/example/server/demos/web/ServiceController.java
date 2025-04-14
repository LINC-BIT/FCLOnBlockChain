package com.example.server.demos.web;

import com.example.server.service.UploadAddrService;
import com.example.server.tools.AjaxResult;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
public class ServiceController {

    @Autowired
    private DiscoveryClient discoveryClient;

    @Autowired
    private UploadAddrService uploadAddrService;

    @GetMapping("/services")
    public Map<String, List<ServiceInstance>> getAllServices() {
        // 获取所有服务名称
        List<String> serviceNames = discoveryClient.getServices();

        // 获取每个服务的所有实例
        Map<String, List<ServiceInstance>> servicesMap = serviceNames.stream()
                .collect(Collectors.toMap(
                        serviceName -> serviceName,
                        serviceName -> discoveryClient.getInstances(serviceName)
                ));

        return servicesMap;
    }

//    @GetMapping("/upload-service")
//    public String getUploadService() {
//        // 获取所有服务名称
//        List<String> serviceNames = discoveryClient.getServices();
//
//        // 获取每个服务的所有实例
//        Map<String, List<ServiceInstance>> servicesMap = serviceNames.stream()
//                .collect(Collectors.toMap(
//                        serviceName -> serviceName,
//                        serviceName -> discoveryClient.getInstances(serviceName)
//                ));
//        for(String key:servicesMap.keySet()){
//            System.out.println(servicesMap.get("upload-service").get(0).getMetadata());
//        }
//        return servicesMap.get("upload-service").get(0).getMetadata().get("upload-addr");
//    }

    @GetMapping("/upload-service")
    public AjaxResult getUploadService() {
        Map<String, Object> data = new HashMap<>();
        data.put("addr", this.uploadAddrService.getRandomUploadAddr());
        data.put("chunk", 80 * 1024 * 1024);
        return AjaxResult.success("success",data);
//        return ResponseEntity.ok(this.uploadAddrService.getRandomUploadAddr());
    }
}