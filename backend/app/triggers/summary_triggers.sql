-- 节点汇总表触发器（核心性能优化）
-- 使用path字段前缀匹配替代递归CTE

-- 当知识条目插入时，更新所有祖先节点的汇总表
CREATE TRIGGER IF NOT EXISTS trigger_knowledge_update_summary
AFTER INSERT ON knowledge
FOR EACH ROW
BEGIN
    INSERT INTO node_summaries (category_id, total_count, pending_count, updated_at)
    SELECT 
        c.id,
        (SELECT COUNT(*) FROM knowledge k 
         INNER JOIN categories cat ON k.category_id = cat.id 
         WHERE (cat.id = c.id OR cat.path LIKE c.path || '/%')
         AND k.review_status != 'rejected'),
        (SELECT COUNT(*) FROM knowledge k 
         INNER JOIN categories cat ON k.category_id = cat.id 
         WHERE (cat.id = c.id OR cat.path LIKE c.path || '/%')
         AND k.review_status = 'pending'),
        CURRENT_TIMESTAMP
    FROM categories c
    WHERE c.id = NEW.category_id OR (SELECT path FROM categories WHERE id = NEW.category_id) LIKE c.path || '/%'
    ON CONFLICT(category_id) DO UPDATE SET
        total_count = excluded.total_count,
        pending_count = excluded.pending_count,
        updated_at = CURRENT_TIMESTAMP;
END;

-- 知识条目更新时触发
CREATE TRIGGER IF NOT EXISTS trigger_knowledge_update_summary_update
AFTER UPDATE ON knowledge
FOR EACH ROW
BEGIN
    -- 更新旧分类的所有祖先
    INSERT INTO node_summaries (category_id, total_count, pending_count, updated_at)
    SELECT 
        c.id,
        (SELECT COUNT(*) FROM knowledge k 
         INNER JOIN categories cat ON k.category_id = cat.id 
         WHERE (cat.id = c.id OR cat.path LIKE c.path || '/%')
         AND k.review_status != 'rejected'),
        (SELECT COUNT(*) FROM knowledge k 
         INNER JOIN categories cat ON k.category_id = cat.id 
         WHERE (cat.id = c.id OR cat.path LIKE c.path || '/%')
         AND k.review_status = 'pending'),
        CURRENT_TIMESTAMP
    FROM categories c
    WHERE c.id = OLD.category_id OR (SELECT path FROM categories WHERE id = OLD.category_id) LIKE c.path || '/%'
    ON CONFLICT(category_id) DO UPDATE SET
        total_count = excluded.total_count,
        pending_count = excluded.pending_count,
        updated_at = CURRENT_TIMESTAMP;

    -- 如果分类变化，更新新分类的所有祖先
    INSERT INTO node_summaries (category_id, total_count, pending_count, updated_at)
    SELECT 
        c.id,
        (SELECT COUNT(*) FROM knowledge k 
         INNER JOIN categories cat ON k.category_id = cat.id 
         WHERE (cat.id = c.id OR cat.path LIKE c.path || '/%')
         AND k.review_status != 'rejected'),
        (SELECT COUNT(*) FROM knowledge k 
         INNER JOIN categories cat ON k.category_id = cat.id 
         WHERE (cat.id = c.id OR cat.path LIKE c.path || '/%')
         AND k.review_status = 'pending'),
        CURRENT_TIMESTAMP
    FROM categories c
    WHERE c.id = NEW.category_id OR (SELECT path FROM categories WHERE id = NEW.category_id) LIKE c.path || '/%'
    ON CONFLICT(category_id) DO UPDATE SET
        total_count = excluded.total_count,
        pending_count = excluded.pending_count,
        updated_at = CURRENT_TIMESTAMP;
END;

-- 知识条目删除时触发
CREATE TRIGGER IF NOT EXISTS trigger_knowledge_update_summary_delete
AFTER DELETE ON knowledge
FOR EACH ROW
BEGIN
    INSERT INTO node_summaries (category_id, total_count, pending_count, updated_at)
    SELECT 
        c.id,
        (SELECT COUNT(*) FROM knowledge k 
         INNER JOIN categories cat ON k.category_id = cat.id 
         WHERE (cat.id = c.id OR cat.path LIKE c.path || '/%')
         AND k.review_status != 'rejected'),
        (SELECT COUNT(*) FROM knowledge k 
         INNER JOIN categories cat ON k.category_id = cat.id 
         WHERE (cat.id = c.id OR cat.path LIKE c.path || '/%')
         AND k.review_status = 'pending'),
        CURRENT_TIMESTAMP
    FROM categories c
    WHERE c.id = OLD.category_id OR (SELECT path FROM categories WHERE id = OLD.category_id) LIKE c.path || '/%'
    ON CONFLICT(category_id) DO UPDATE SET
        total_count = excluded.total_count,
        pending_count = excluded.pending_count,
        updated_at = CURRENT_TIMESTAMP;
END;
