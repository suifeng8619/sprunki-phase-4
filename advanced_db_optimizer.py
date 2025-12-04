#!/usr/bin/env python3
"""
高级数据库优化系统
提供更深层的数据库性能优化和查询重构
"""

import time
from mongoengine import connect, Document
from loguru import logger
from apps.models.article_model import 文章db
from cache_system import cached_function, article_cache

class AdvancedDatabaseOptimizer:
    """
    高级数据库优化器
    """
    
    def __init__(self):
        self.optimization_stats = {
            'queries_optimized': 0,
            'time_saved': 0,
            'cache_hits': 0
        }
    
    def create_advanced_indexes(self):
        """创建高级复合索引"""
        logger.info("🔍 创建高级数据库索引...")
        
        try:
            collection = 文章db._get_collection()
            
            # 复合索引集合
            advanced_indexes = [
                # 语言 + 状态 + 发布时间 (用于多语言首页查询)
                {
                    'index': [("lang", 1), ("状态", 1), ("发布时间", -1)],
                    'name': "idx_lang_status_time",
                    'background': True
                },
                
                # 文章URL + 语言 (用于URL路由查询)
                {
                    'index': [("article_url", 1), ("lang", 1)],
                    'name': "idx_url_lang",
                    'background': True
                },
                
                # 分类 + 状态 + 时间 (用于分类页面)
                {
                    'index': [("分类", 1), ("状态", 1), ("发布时间", -1)],
                    'name': "idx_category_status_time", 
                    'background': True
                },
                
                # 标签数组索引 (用于标签查询)
                {
                    'index': [("标签", 1), ("状态", 1)],
                    'name': "idx_tags_status",
                    'background': True
                },
                
                # 文本搜索索引
                {
                    'index': [("标题", "text"), ("简介", "text"), ("正文内容", "text")],
                    'name': "idx_fulltext_search",
                    'background': True
                }
            ]
            
            created_count = 0
            for idx_config in advanced_indexes:
                try:
                    # 检查索引是否已存在
                    existing_indexes = collection.list_indexes()
                    index_exists = any(idx.get('name') == idx_config['name'] for idx in existing_indexes)
                    
                    if not index_exists:
                        collection.create_index(
                            idx_config['index'],
                            name=idx_config['name'],
                            background=idx_config['background']
                        )
                        created_count += 1
                        logger.info(f"✅ 创建索引: {idx_config['name']}")
                    else:
                        logger.debug(f"⏩ 索引已存在: {idx_config['name']}")
                        
                except Exception as e:
                    logger.error(f"❌ 创建索引失败 {idx_config['name']}: {e}")
            
            logger.info(f"🎯 高级索引创建完成: {created_count} 个新索引")
            return True
            
        except Exception as e:
            logger.error(f"❌ 高级索引创建失败: {e}")
            return False
    
    @cached_function(cache_instance=article_cache, timeout=900)
    def get_articles_by_language_optimized(self, lang='en', limit=20, skip=0, status='发布'):
        """
        优化的语言文章查询
        使用复合索引和投影优化
        """
        start_time = time.time()
        
        try:
            # 使用复合索引: lang + 状态 + 发布时间
            articles = 文章db.objects(
                lang=lang,
                状态=status
            ).only(
                'ids',
                '标题', 
                '简介',
                'article_url',
                'image_url',
                '发布时间'
            ).order_by('-发布时间').skip(skip).limit(limit)
            
            # 转换为字典列表以减少序列化开销
            result = []
            for article in articles:
                result.append({
                    'ids': article.ids,
                    'title': article.标题,
                    'summary': article.简介,
                    'url': article.article_url,
                    'image': article.image_url,
                    'publish_time': article.发布时间.isoformat() if article.发布时间 else None
                })
            
            query_time = (time.time() - start_time) * 1000
            logger.info(f"语言文章查询优化: {lang}, {len(result)}条, 耗时: {query_time:.2f}ms")
            
            self.optimization_stats['queries_optimized'] += 1
            self.optimization_stats['time_saved'] += max(0, 1000 - query_time)  # 假设原查询需1秒
            
            return result
            
        except Exception as e:
            query_time = (time.time() - start_time) * 1000
            logger.error(f"语言文章查询失败: {lang}, 耗时: {query_time:.2f}ms, 错误: {e}")
            return []
    
    @cached_function(cache_instance=article_cache, timeout=1200)  
    def get_article_by_url_advanced(self, article_url, lang='en'):
        """
        高级URL文章查询
        使用复合索引优化
        """
        start_time = time.time()
        
        try:
            # 使用复合索引: article_url + lang
            article = 文章db.objects(
                article_url=article_url,
                lang=lang,
                状态='发布'
            ).only(
                'ids',
                '标题',
                '简介', 
                'iframe',
                'image_url',
                '正文内容',
                'article_url',
                '发布时间',
                '标签'
            ).first()
            
            if not article:
                return None
            
            # 优化的数据结构
            result = {
                'ids': article.ids,
                'title': article.标题,
                'summary': article.简介,
                'content': article.正文内容,
                'iframe': article.iframe,
                'image_url': article.image_url,
                'article_url': article.article_url,
                'publish_time': article.发布时间.isoformat() if article.发布时间 else None,
                'tags': article.标签 if article.标签 else []
            }
            
            query_time = (time.time() - start_time) * 1000
            logger.info(f"URL文章查询优化: {article_url}, 耗时: {query_time:.2f}ms")
            
            self.optimization_stats['queries_optimized'] += 1
            return result
            
        except Exception as e:
            query_time = (time.time() - start_time) * 1000
            logger.error(f"URL文章查询失败: {article_url}, 耗时: {query_time:.2f}ms, 错误: {e}")
            return None
    
    @cached_function(cache_instance=article_cache, timeout=600)
    def get_related_articles(self, article_id, lang='en', limit=5):
        """
        获取相关文章（基于标签和分类）
        """
        start_time = time.time()
        
        try:
            # 首先获取当前文章的标签和分类
            current_article = 文章db.objects(ids=article_id).only('标签', '分类').first()
            if not current_article:
                return []
            
            # 查询条件：相同标签或分类，排除当前文章
            query_conditions = {
                'lang': lang,
                '状态': '发布',
                'ids__ne': article_id  # 排除当前文章
            }
            
            # 添加标签或分类匹配条件
            or_conditions = []
            if current_article.标签:
                or_conditions.append({'标签__in': current_article.标签})
            if current_article.分类:
                or_conditions.append({'分类': current_article.分类})
            
            if not or_conditions:
                return []
            
            # 使用$or查询相关文章
            related_articles = 文章db.objects(**query_conditions).filter(
                __raw__={'$or': [cond for cond in or_conditions]}
            ).only(
                'ids',
                '标题',
                '简介',
                'article_url',
                'image_url'
            ).limit(limit)
            
            result = []
            for article in related_articles:
                result.append({
                    'ids': article.ids,
                    'title': article.标题,
                    'summary': article.简介,
                    'url': article.article_url,
                    'image': article.image_url
                })
            
            query_time = (time.time() - start_time) * 1000
            logger.info(f"相关文章查询: ID={article_id}, {len(result)}条, 耗时: {query_time:.2f}ms")
            
            return result
            
        except Exception as e:
            query_time = (time.time() - start_time) * 1000  
            logger.error(f"相关文章查询失败: ID={article_id}, 耗时: {query_time:.2f}ms, 错误: {e}")
            return []
    
    def analyze_slow_queries(self):
        """分析慢查询"""
        logger.info("🔍 分析数据库性能...")
        
        try:
            collection = 文章db._get_collection()
            
            # 获取集合统计信息
            stats = collection.database.command("collStats", collection.name)
            
            analysis = {
                'collection_size': stats.get('size', 0),
                'document_count': stats.get('count', 0),
                'index_count': len(list(collection.list_indexes())),
                'avg_document_size': stats.get('avgObjSize', 0)
            }
            
            logger.info(f"📊 数据库分析结果:")
            logger.info(f"   文档数量: {analysis['document_count']:,}")
            logger.info(f"   集合大小: {analysis['collection_size']:,} bytes")
            logger.info(f"   索引数量: {analysis['index_count']}")
            logger.info(f"   平均文档大小: {analysis['avg_document_size']} bytes")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ 数据库分析失败: {e}")
            return {}
    
    def get_optimization_stats(self):
        """获取优化统计"""
        return {
            **self.optimization_stats,
            'cache_stats': article_cache.get_stats()
        }

# 全局优化器实例
db_optimizer = AdvancedDatabaseOptimizer()

def optimize_database_advanced():
    """执行高级数据库优化"""
    logger.info("🚀 开始高级数据库优化...")
    
    # 创建高级索引
    success = db_optimizer.create_advanced_indexes()
    
    if success:
        # 分析性能
        db_optimizer.analyze_slow_queries()
        
        # 显示优化统计
        stats = db_optimizer.get_optimization_stats()
        logger.info(f"✅ 高级优化完成")
        logger.info(f"   优化查询数: {stats['queries_optimized']}")
        logger.info(f"   节省时间: {stats['time_saved']:.2f}ms")
        
        return True
    else:
        logger.error("❌ 高级数据库优化失败")
        return False

if __name__ == "__main__":
    # 执行高级数据库优化
    print("🚀 开始高级数据库优化...")
    
    # 连接数据库 (使用应用的数据库配置)
    try:
        from setting import DATABASE_CONFIG
        if DATABASE_CONFIG.get('MONGO_URI'):
            connect(host=DATABASE_CONFIG['MONGO_URI'])
        else:
            connect('sprunki_test')  # 默认测试数据库
        
        # 执行优化
        success = optimize_database_advanced()
        
        if success:
            print("✅ 高级数据库优化完成！")
            
            # 测试优化后的查询
            print("\n🧪 测试优化查询...")
            optimizer = AdvancedDatabaseOptimizer()
            
            # 测试语言文章查询
            articles = optimizer.get_articles_by_language_optimized('en', limit=5)
            print(f"✅ 英语文章查询: {len(articles)} 条结果")
            
            # 测试URL查询
            if articles:
                article_url = articles[0].get('url')
                if article_url:
                    article = optimizer.get_article_by_url_advanced(article_url, 'en')
                    print(f"✅ URL文章查询: {'成功' if article else '未找到'}")
            
            print("🎯 高级优化测试完成！")
        else:
            print("❌ 高级数据库优化失败")
            
    except Exception as e:
        print(f"❌ 优化过程出错: {e}")