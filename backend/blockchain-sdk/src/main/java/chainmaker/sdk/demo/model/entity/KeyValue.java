package chainmaker.sdk.demo.model.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.experimental.Accessors;



@Data
@TableName("demo")
@Accessors(chain = true)
public class KeyValue {

    @TableId(type = IdType.AUTO)
    private Integer id;

    @JsonProperty(value = "file_hash")
    @TableField("file_hash")
    private String fileHash;

    @TableField("value")
    private String value;
}
