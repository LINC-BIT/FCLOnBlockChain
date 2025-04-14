package chainmaker.sdk.demo;

import org.chainmaker.pb.config.ChainConfigOuterClass;
import org.chainmaker.sdk.ChainClient;

public class ChainConfig {

    public static void getChainConfig(ChainClient chainClient) {
        ChainConfigOuterClass.ChainConfig chainConfig = null;
        try {
            chainConfig = chainClient.getChainConfig(20000);
        } catch (Exception e) {
            e.printStackTrace();
        }
        System.out.println(chainConfig.toString());
    }


}
