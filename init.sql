-- 初始化PostGIS扩展
-- 此文件会在容器首次启动时自动执行

-- 创建PostGIS扩展
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- 验证PostGIS安装
DO $$
BEGIN
    RAISE NOTICE 'PostGIS版本: %', PostGIS_Version();
END $$;

-- 显示已安装的扩展
SELECT extname, extversion 
FROM pg_extension 
WHERE extname LIKE 'postgis%';

