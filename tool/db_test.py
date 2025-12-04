from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['your_database']
counters = db.counters


def get_next_sequence(name):
    sequence_document = counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        return_document=True,
        upsert=True  # 如果文档不存在则插入
    )
    return sequence_document['seq']


# 使用封装函数
for _ in range(10):
    new_id = get_next_sequence('article_id')
    article = {
        "_id": new_id,
        "content": "This is article number {}".format(new_id)
        # 其他字段
    }
    db.articles.insert_one(article)
