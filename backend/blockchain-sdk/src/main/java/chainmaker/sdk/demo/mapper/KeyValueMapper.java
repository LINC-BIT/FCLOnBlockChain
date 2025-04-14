package chainmaker.sdk.demo.mapper;

import chainmaker.sdk.demo.model.entity.KeyValue;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.Set;

/**
 * 查询帖子到tag的映射关系
 */
@Repository
public interface KeyValueMapper extends BaseMapper<KeyValue> {
}
