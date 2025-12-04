def get_next_sequence(counters, name):
    """计数器函数用来实现自增id"""
    sequence_document = counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        return_document=True,
        upsert=True  # 如果文档不存在则插入
    )
    return sequence_document['seq']
