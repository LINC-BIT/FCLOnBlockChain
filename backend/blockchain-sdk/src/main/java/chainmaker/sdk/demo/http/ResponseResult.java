package chainmaker.sdk.demo.http;

import lombok.Data;

@Data
public class ResponseResult {

    private Object data;
    private Integer code;
    private String message;

    public ResponseResult(Object data, Integer code, String message) {
        this.data = data;
        this.code = code;
        this.message = message;
    }
    public static ResponseResult success(Object data) {
        return new ResponseResult(data,200,"success");
    }
    public static ResponseResult success(Object data, Integer code, String message) {
        return new ResponseResult(data,code,message);
    }
    public static ResponseResult fail(Object data, Integer code, String message) {
        return new ResponseResult(data,code,message);
    }
}