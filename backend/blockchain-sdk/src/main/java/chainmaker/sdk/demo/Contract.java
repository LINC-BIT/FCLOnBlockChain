package chainmaker.sdk.demo;

import org.chainmaker.pb.common.ContractOuterClass;
import org.chainmaker.pb.common.Request;
import org.chainmaker.pb.common.ResultOuterClass;
import org.chainmaker.sdk.ChainClient;
import org.chainmaker.sdk.User;
import org.chainmaker.sdk.utils.FileUtils;
import org.chainmaker.sdk.utils.SdkUtils;

import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;


public class Contract {

    //合约
    private static final String QUERY_CONTRACT_METHOD = "find_by_file_hash";
    private static final String INVOKE_CONTRACT_METHOD = "save";
    private static final String CONTRACT_NAME = "test1";
    private static final String CONTRACT_FILE_PATH = "chainmaker_contract.wasm";

    public static void createContract(ChainClient chainClient, User adminUser1, User adminUser2, User adminUser3) {
        ResultOuterClass.TxResponse responseInfo = null;
        try {
            byte[] byteCode = FileUtils.getResourceFileBytes(CONTRACT_FILE_PATH);
            System.out.println("byte len:"+byteCode.length);

            // 1. create payload WASMER
            Request.Payload payload = chainClient.createContractCreatePayload(CONTRACT_NAME, "1", byteCode,
                    ContractOuterClass.RuntimeType.WASMER, null);
            //2. create payloads with endorsement
            Request.EndorsementEntry[] endorsementEntries = SdkUtils
                    .getEndorsers(payload, new User[]{adminUser1, adminUser2, adminUser3});
            // 3. send request
            responseInfo = chainClient.sendContractManageRequest(payload, endorsementEntries, 10000, 10000);
        } catch (Exception e) {
            e.printStackTrace();
        }
        System.out.println(responseInfo);
    }

    public static ResultOuterClass.TxResponse invokeContract(ChainClient chainClient, String contractName, Map<String, byte[]> params) {
        ResultOuterClass.TxResponse responseInfo = null;
        try {
            String invokeContractMethod = "save";
            responseInfo = chainClient.invokeContract(contractName, invokeContractMethod,
                    null, params,10000, 10000);
        } catch (Exception e) {
            e.printStackTrace();
        }
        System.out.println(responseInfo);
        return responseInfo;
    }

    public static ResultOuterClass.TxResponse queryContract(ChainClient chainClient, String contractName, Map<String, byte[]> params) {
        ResultOuterClass.TxResponse responseInfo = null;
        try {
            String queryContractMethod = "find_by_file_hash";
            responseInfo = chainClient.queryContract(contractName, queryContractMethod,
                    null,  params,10000);
        } catch (Exception e) {
            e.printStackTrace();
        }
        System.out.println(responseInfo);
        return responseInfo;
    }


    public static ResultOuterClass.TxResponse saveToContract(ChainClient chainClient, Map<String, byte[]> params) {
        ResultOuterClass.TxResponse responseInfo = null;
        try {
            params = new HashMap<String, byte[]>(){{
                put("file_hash","111a".getBytes(StandardCharsets.UTF_8));
                put("file_name","222a".getBytes(StandardCharsets.UTF_8));
                put("time","333".getBytes(StandardCharsets.UTF_8));
            }};
            responseInfo = chainClient.invokeContract(CONTRACT_NAME, INVOKE_CONTRACT_METHOD,
                    null, params,10000, 10000);
        } catch (Exception e) {
            e.printStackTrace();
        }
        System.out.println(responseInfo);
        return responseInfo;
    }


    public static ResultOuterClass.TxResponse queryContract2(ChainClient chainClient) {
        ResultOuterClass.TxResponse responseInfo = null;
        try {
            Map<String, byte[]> params = new HashMap<String, byte[]>(){{
                put("file_hash","111a".getBytes(StandardCharsets.UTF_8));
            }};
            responseInfo = chainClient.queryContract(CONTRACT_NAME, QUERY_CONTRACT_METHOD,
                    null,  params,10000);
        } catch (Exception e) {
            e.printStackTrace();
        }
        System.out.println(responseInfo);
        return responseInfo;
    }

}
