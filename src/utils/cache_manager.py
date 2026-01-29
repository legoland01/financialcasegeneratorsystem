"""
缓存管理器 - 负责数据的缓存、读取和清理

该模块实现了按判决书哈希值的缓存机制，支持：
- 缓存读写
- 哈希计算
- 自动清理（30天过期、100个上限）
- 手动清理

Author: OpenCode AI
Date: 2026-01-27
"""

import os
import time
import hashlib
import json
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class CacheManager:
    """缓存管理器 - 负责数据的缓存、读取和清理"""
    
    def __init__(
        self,
        cache_dir: str = "cache",
        max_cache_days: int = 30,
        max_cache_count: int = 100
    ):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            max_cache_days: 缓存最大保留天数（默认30天）
            max_cache_count: 缓存最大数量（默认100个）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.cache_index_path = self.cache_dir / "cache_index.json"
        self.max_cache_days = max_cache_days
        self.max_cache_count = max_cache_count
        
        # 线程锁（防止并发写入冲突）
        self._lock = threading.Lock()
        
        # 加载缓存索引
        self._load_index()
    
    def get_cache_key(self, judgment_path: str) -> str:
        """
        计算判决书文件的哈希值作为缓存键
        
        Args:
            judgment_path: 判决书文件路径
        Returns:
            SHA256哈希值
        """
        hash_sha256 = hashlib.sha256()
        try:
            with open(judgment_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_sha256.update(chunk)
        except FileNotFoundError:
            # 如果文件不存在，使用文件路径的哈希
            hash_sha256.update(judgment_path.encode('utf-8'))
        
        return hash_sha256.hexdigest()
    
    def get(
        self,
        judgment_path: str,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存数据
        
        Args:
            judgment_path: 判决书文件路径
            force_refresh: 是否强制刷新
        Returns:
            缓存数据或None（如果不存在或已过期）
        """
        cache_key = self.get_cache_key(judgment_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        # 检查缓存是否存在
        if cache_file.exists() and not force_refresh:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # 检查缓存是否过期
                if self._is_expired(cache_data):
                    self._remove_expired_cache(cache_file, cache_key)
                    return None
                
                # 更新最后使用时间
                cache_data['last_used'] = datetime.utcnow().isoformat()
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
                return cache_data
            except (json.JSONDecodeError, KeyError):
                # 缓存文件损坏，删除并重新生成
                cache_file.unlink()
        
        return None
    
    def save(self, judgment_path: str, data: Dict[str, Any]) -> str:
        """
        保存数据到缓存
        
        Args:
            judgment_path: 判决书文件路径
            data: 要缓存的数据
        Returns:
            cache_key
        """
        cache_key = self.get_cache_key(judgment_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        with self._lock:
            # 添加元数据
            data["version"] = "2.0"
            data["judgment_hash"] = cache_key
            data["judgment_path"] = judgment_path
            data["created_at"] = datetime.utcnow().isoformat()
            data["last_used"] = datetime.utcnow().isoformat()
            
            # 保存缓存文件
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 更新索引
            self._update_index(cache_key, cache_file)
            
            # 检查是否需要清理
            self._cleanup_if_needed()
        
        return cache_key
    
    def _load_index(self):
        """加载缓存索引"""
        if self.cache_index_path.exists():
            try:
                with open(self.cache_index_path, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            except json.JSONDecodeError:
                self.index = {}
        else:
            self.index = {}
    
    def _update_index(self, cache_key: str, cache_file: Path):
        """更新缓存索引"""
        self.index[cache_key] = {
            "file": str(cache_file),
            "created_at": datetime.utcnow().isoformat()
        }
        
        with open(self.cache_index_path, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
    
    def _is_expired(self, cache_data: Dict[str, Any]) -> bool:
        """检查缓存是否过期"""
        created_at = cache_data.get('created_at')
        if not created_at:
            return False
        
        try:
            created_date = datetime.fromisoformat(created_at)
            expiry_date = created_date + timedelta(days=self.max_cache_days)
            return datetime.now() > expiry_date
        except (ValueError, TypeError):
            return False
    
    def _remove_expired_cache(self, cache_file: Path, cache_key: str):
        """删除过期缓存"""
        try:
            cache_file.unlink()
            if cache_key in self.index:
                del self.index[cache_key]
            with open(self.cache_index_path, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _cleanup_if_needed(self):
        """如果需要，清理缓存"""
        # 检查数量限制
        if len(self.index) > self.max_cache_count:
            self._cleanup_by_count()
        
        # 检查过期缓存
        self._cleanup_expired()
    
    def _cleanup_by_count(self):
        """按数量清理（删除最旧的缓存）"""
        # 按创建时间排序
        sorted_items = sorted(
            self.index.items(),
            key=lambda x: x[1].get('created_at', '')
        )
        
        # 删除最旧的缓存
        items_to_delete = len(self.index) - self.max_cache_count + 10
        for cache_key, cache_info in sorted_items[:items_to_delete]:
            try:
                cache_file = Path(cache_info['file'])
                if cache_file.exists():
                    cache_file.unlink()
                del self.index[cache_key]
            except Exception:
                pass
    
    def _cleanup_expired(self):
        """清理所有过期缓存"""
        expired_keys = []
        for cache_key, cache_info in self.index.items():
            cache_file = Path(cache_info['file'])
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    if self._is_expired(cache_data):
                        expired_keys.append(cache_key)
                except Exception:
                    expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            self._remove_expired_cache(
                self.index[cache_key].get('file') or cache_key,
                cache_key
            )
    
    def clear_all(self):
        """清理所有缓存"""
        with self._lock:
            for cache_key, cache_info in self.index.items():
                try:
                    cache_file = Path(cache_info['file'])
                    if cache_file.exists():
                        cache_file.unlink()
                except Exception:
                    pass
            
            self.index = {}
            if self.cache_index_path.exists():
                self.cache_index_path.unlink()
    
    def clear_by_hash(self, cache_key: str):
        """清理指定缓存"""
        with self._lock:
            if cache_key in self.index:
                try:
                    cache_file = Path(self.index[cache_key]['file'])
                    if cache_file.exists():
                        cache_file.unlink()
                except Exception:
                    pass
                del self.index[cache_key]
                
                with open(self.cache_index_path, 'w', encoding='utf-8') as f:
                    json.dump(self.index, f, ensure_ascii=False, indent=2)
    
    def clear_expired(self):
        """清理过期缓存（对外接口）"""
        with self._lock:
            self._cleanup_expired()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        total_size = 0
        valid_count = 0
        
        for cache_key, cache_info in self.index.items():
            cache_file = Path(cache_info['file'])
            if cache_file.exists():
                total_size += cache_file.stat().st_size
                valid_count += 1
        
        return {
            "total_caches": len(self.index),
            "valid_caches": valid_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_cache_days": self.max_cache_days,
            "max_cache_count": self.max_cache_count
        }
    
    def exists(self, judgment_path: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            judgment_path: 判决书文件路径
        Returns:
            缓存是否存在
        """
        cache_key = self.get_cache_key(judgment_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        return cache_file.exists()


# 测试代码
if __name__ == "__main__":
    import tempfile
    import json
    
    # 创建临时缓存目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建缓存管理器
        cache_manager = CacheManager(
            cache_dir=tmpdir,
            max_cache_days=30,
            max_cache_count=100
        )
        
        # 创建测试判决书文件
        judgment_file = os.path.join(tmpdir, "test_judgment.txt")
        with open(judgment_file, 'w', encoding='utf-8') as f:
            f.write("测试判决书内容")
        
        # 测试缓存
        test_data = {
            "boundary_conditions": {
                "合同金额": 150000000,
                "利率": 0.061
            }
        }
        
        # 保存缓存
        cache_key = cache_manager.save(judgment_file, test_data)
        print(f"缓存键: {cache_key}")
        
        # 读取缓存
        cached_data = cache_manager.get(judgment_file)
        print(f"缓存数据: {json.dumps(cached_data, ensure_ascii=False, indent=2)}")
        
        # 获取缓存信息
        info = cache_manager.get_cache_info()
        print(f"缓存信息: {info}")
        
        # 清理所有缓存
        cache_manager.clear_all()
        print("已清理所有缓存")
