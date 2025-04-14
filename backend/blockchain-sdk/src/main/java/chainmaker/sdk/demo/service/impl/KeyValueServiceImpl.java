package chainmaker.sdk.demo.service.impl;

import chainmaker.sdk.demo.mapper.KeyValueMapper;
import chainmaker.sdk.demo.model.entity.KeyValue;
import chainmaker.sdk.demo.service.IKeyValueService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;


@Service
public class KeyValueServiceImpl extends ServiceImpl<KeyValueMapper, KeyValue> implements IKeyValueService {

}
