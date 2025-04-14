package chainmaker.sdk.demo.model.dto;

import com.alibaba.fastjson.annotation.JSONField;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class ContractDataDto {
    @JsonProperty(value = "contract_name")
    @JSONField(name = "contract_name")
    String contractName;

    @JsonProperty(value = "file_hash")
    @JSONField(name = "file_hash")
    String fileHash;

    @JsonProperty(value = "file_name")
    @JSONField(name = "file_name")
    String fileName;

}
