package chainmaker.sdk.demo;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import static chainmaker.sdk.demo.InitClient.inItChainClient;

@MapperScan("chainmaker.sdk.demo.mapper")
@SpringBootApplication
public class DemoApplication  {
    public static void main(String[] args) throws Exception {
        SpringApplication.run(DemoApplication.class, args);

    }
}

