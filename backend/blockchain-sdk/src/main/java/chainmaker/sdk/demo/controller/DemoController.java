package chainmaker.sdk.demo.controller;

import chainmaker.sdk.demo.Contract;
import chainmaker.sdk.demo.InitClient;
import chainmaker.sdk.demo.model.dto.ContractDataDto;
import chainmaker.sdk.demo.model.dto.File;
import chainmaker.sdk.demo.http.ResponseResult;
import com.alibaba.fastjson.JSON;
import org.chainmaker.pb.common.ResultOuterClass;
import org.springframework.web.bind.annotation.*;

import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

import static chainmaker.sdk.demo.InitClient.inItChainClient;

@RestController
@RequestMapping("/demo")
public class DemoController {

    @PostMapping("/contract/save")
    public ResponseResult saveParamsToContract(@RequestBody ContractDataDto contractDataDto) {
        try {
            ResultOuterClass.TxResponse responseInfo = null;
            String message = null;

            inItChainClient();

            Map<String, byte[]> params = new HashMap<String, byte[]>() {{
                put("file_name", contractDataDto.getFileName().getBytes(StandardCharsets.UTF_8));
                put("file_hash", contractDataDto.getFileHash().getBytes(StandardCharsets.UTF_8));
                put("time", "0".getBytes(StandardCharsets.UTF_8));
            }};
            responseInfo = Contract.invokeContract(InitClient.getChainClient(), contractDataDto.getContractName(), params);

            if (responseInfo != null) {
                message = responseInfo.getMessage();
            }

            if ("OK".equals(message)) {
                return ResponseResult.success(null, 200, message);
            } else {
                return ResponseResult.success(null, 500, message);
            }
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseResult.success(null, 500, "error");
        }
    }

    @PostMapping("/contract/get")
    public ResponseResult getParamsFromContract(@RequestBody ContractDataDto contractDataDto) {
        try {
            ResultOuterClass.TxResponse responseInfo = null;
            String message = null;
            File file = null;

            inItChainClient();

            Map<String, byte[]> params = new HashMap<String, byte[]>() {{
                put("file_hash", contractDataDto.getFileHash().getBytes(StandardCharsets.UTF_8));
            }};
            responseInfo = Contract.queryContract(InitClient.getChainClient(), contractDataDto.getContractName(), params);

            if (responseInfo != null) {
                message = responseInfo.getMessage();
                ResultOuterClass.ContractResult result = responseInfo.getContractResult();
                file = JSON.parseObject(result.getResult().toStringUtf8(), File.class);
            }

            if ("SUCCESS".equals(message)) {
                return ResponseResult.success(file, 200, message);
            } else {
                return ResponseResult.success(file, 500, message);
            }
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseResult.success(null, 500, "error");
        }
    }

}
