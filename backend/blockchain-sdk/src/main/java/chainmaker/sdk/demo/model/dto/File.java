package chainmaker.sdk.demo.model.dto;

import com.alibaba.fastjson.annotation.JSONField;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class File{
    @JsonProperty(value = "file_hash")
    @JSONField(name = "file_hash")
    String fileHash;

    @JsonProperty(value = "file_name")
    @JSONField(name = "file_name")
    String fileName;

    @JsonProperty(value = "time")
    @JSONField(name = "time")
    String time;
}
