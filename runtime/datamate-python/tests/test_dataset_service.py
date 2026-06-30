# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, AsyncMock
import sys
import os

# 确保 runtime/datamate-python 目录在 sys.path 中
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(TEST_DIR)
sys.path.insert(0, APP_DIR)

from app.module.dataset.service.service import Service
from app.module.dataset.schema import DatasetResponse, PagedDatasetFileResponse, DatasetFileResponse
from app.db.models import Dataset, DatasetFiles


class TestDatasetService(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # 创建模拟的 AsyncSession 对象
        self.mock_db = MagicMock()
        self.mock_db.execute = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.rollback = AsyncMock()
        self.mock_db.flush = AsyncMock()
        
        # 初始化 Service
        self.service = Service(self.mock_db)

    async def test_get_dataset_success(self):
        """测试正常获取数据集详情"""
        # 准备 Mock 数据
        mock_dataset = Dataset(
            id="test-dataset-id",
            name="Test Dataset",
            description="A test description",
            dataset_type="TEXT",
            status="DRAFT",
            file_count=5,
            size_bytes=1024,
            created_by="system"
        )
        
        # 模拟 db.execute 返回值
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dataset
        self.mock_db.execute.return_value = mock_result

        # 执行测试
        response = await self.service.get_dataset("test-dataset-id")

        # 校验结果
        self.assertIsNotNone(response)
        self.assertEqual(response.id, "test-dataset-id")
        self.assertEqual(response.name, "Test Dataset")
        self.assertEqual(response.description, "A test description")
        self.assertEqual(response.datasetType, "TEXT")
        self.assertEqual(response.status, "DRAFT")
        self.assertEqual(response.fileCount, 5)
        self.assertEqual(response.totalSize, 1024)

    async def test_get_dataset_not_found(self):
        """测试获取不存在的数据集时返回 None"""
        # 模拟数据库未找到数据
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.mock_db.execute.return_value = mock_result

        # 执行并验证
        response = await self.service.get_dataset("non-existent-id")
        self.assertIsNone(response)

    async def test_create_dataset_success(self):
        """测试创建数据集成功流程"""
        # 1. 模拟名称不存在检查 (select Dataset.name) -> 返回 None
        mock_result_check = MagicMock()
        mock_result_check.scalar_one_or_none.return_value = None
        self.mock_db.execute.return_value = mock_result_check

        # 2. 调用创建服务
        response = await self.service.create_dataset(
            name="New Dataset",
            dataset_type="IMAGE",
            description="Testing create_dataset API",
            status="PUBLISHED"
        )

        # 3. 验证结果
        self.assertIsNotNone(response)
        self.assertEqual(response.name, "New Dataset")
        self.assertEqual(response.datasetType, "IMAGE")
        self.assertEqual(response.description, "Testing create_dataset API")
        self.assertEqual(response.status, "PUBLISHED")
        
        # 确认 db.add 和 db.commit 被调用
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    async def test_create_dataset_duplicated_name(self):
        """测试创建重名的数据集时抛出异常"""
        # 模拟冲突的已有数据集
        existing_dataset = Dataset(
            id="existing-id",
            name="Existing Dataset"
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_dataset
        self.mock_db.execute.return_value = mock_result

        # 检查是否正如预期抛出包含关键字 Exception
        with self.assertRaises(Exception) as context:
            await self.service.create_dataset(
                name="Existing Dataset",
                dataset_type="AUDIO"
            )
        self.assertIn("already exists", str(context.exception))
        
        # 校验事务有无进行 commit
        self.mock_db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
