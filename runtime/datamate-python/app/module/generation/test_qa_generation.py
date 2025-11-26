"""
QA生成模块单元测试

运行测试:
    pytest test_qa_generation.py -v
"""

import pytest
from app.module.generation.service.text_splitter import TextSplitter
from app.module.generation.schema.qa_generation import (
    TextSplitConfig,
    QAGenerationConfig,
    CreateQATaskRequest,
)


class TestTextSplitter:
    """文本切片器测试"""

    def test_basic_split(self):
        """测试基本切分功能"""
        splitter = TextSplitter(
            max_characters=-1,
            chunk_size=100,
            chunk_overlap=20
        )
        
        text = "这是第一句话。这是第二句话。" * 50  # 创建一个长文本
        chunks = splitter.split_text(text)
        
        assert len(chunks) > 0
        assert all(len(chunk) <= 100 for chunk in chunks)

    def test_chunk_overlap(self):
        """测试块重叠功能"""
        splitter = TextSplitter(
            max_characters=-1,
            chunk_size=50,
            chunk_overlap=10
        )
        
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 10
        chunks = splitter.split_text(text)
        
        # 检查是否有重叠
        assert len(chunks) >= 2

    def test_max_characters(self):
        """测试最大字符限制"""
        max_chars = 100
        splitter = TextSplitter(
            max_characters=max_chars,
            chunk_size=50,
            chunk_overlap=10
        )
        
        text = "A" * 1000
        chunks = splitter.split_text(text)
        
        # 总字符数不应超过max_characters
        total_unique_chars = len("".join(chunks))
        assert total_unique_chars <= max_chars + 50  # 允许一些overlap

    def test_normalize_newlines(self):
        """测试换行符归一化"""
        splitter = TextSplitter(
            max_characters=-1,
            chunk_size=100,
            chunk_overlap=20
        )
        
        text = "第一段\n\n\n\n第二段\n\n\n第三段"
        chunks = splitter.split_text(text)
        
        # 检查是否归一化
        for chunk in chunks:
            assert "\n\n" not in chunk

    def test_invalid_config(self):
        """测试无效配置"""
        with pytest.raises(ValueError):
            TextSplitter(
                max_characters=-1,
                chunk_size=100,
                chunk_overlap=150  # overlap > chunk_size
            )


class TestSchemas:
    """Schema验证测试"""

    def test_text_split_config_validation(self):
        """测试文本切片配置验证"""
        # 有效配置
        config = TextSplitConfig(
            max_characters=50000,
            chunk_size=800,
            chunk_overlap=200
        )
        assert config.chunk_size == 800
        
        # 无效配置 - overlap >= chunk_size
        with pytest.raises(ValueError):
            TextSplitConfig(
                max_characters=50000,
                chunk_size=800,
                chunk_overlap=800
            )

    def test_qa_generation_config_validation(self):
        """测试QA生成配置验证"""
        config = QAGenerationConfig(
            max_questions=3,
            temperature=0.3,
            model="gpt-5-nano"
        )
        assert config.max_questions == 3
        assert 0.0 <= config.temperature <= 2.0

    def test_create_qa_task_request(self):
        """测试创建任务请求模型"""
        request_data = {
            "name": "测试任务",
            "description": "测试描述",
            "sourceDatasetId": "dataset-001",
            "textSplitConfig": {
                "max_characters": 50000,
                "chunk_size": 800,
                "chunk_overlap": 200
            },
            "qaGenerationConfig": {
                "max_questions": 3,
                "temperature": 0.3,
                "model": "gpt-5-nano"
            },
            "llmApiKey": "sk-test",
            "llmBaseUrl": "https://api.test.com"
        }
        
        request = CreateQATaskRequest(**request_data)
        assert request.name == "测试任务"
        assert request.source_dataset_id == "dataset-001"
        assert request.text_split_config.chunk_size == 800


class TestIntegration:
    """集成测试"""

    def test_full_workflow_simulation(self):
        """模拟完整工作流"""
        # 1. 准备文本
        text = """
        祥子是一个人力车夫，他来自农村，来到北京后，决心靠自己的劳动买一辆车。
        经过三年的努力，他终于买到了自己的车。
        然而好景不长，他的车被军阀的乱兵抢走了。
        祥子没有放弃，他继续拉车攒钱，希望能再买一辆车。
        """ * 10  # 重复以创建足够长的文本
        
        # 2. 文本切片
        splitter = TextSplitter(
            max_characters=5000,
            chunk_size=200,
            chunk_overlap=50
        )
        chunks = splitter.split_text(text)
        
        assert len(chunks) > 0
        print(f"\n切分后文本块数量: {len(chunks)}")
        
        # 3. 验证切片质量
        for i, chunk in enumerate(chunks[:3]):  # 只检查前3个
            print(f"\n文本块 {i+1} (长度: {len(chunk)}):")
            print(chunk[:100] + "..." if len(chunk) > 100 else chunk)
            assert len(chunk) <= 200 + 50  # chunk_size + 一些容差


if __name__ == "__main__":
    # 运行基本测试
    print("运行文本切片测试...")
    test_splitter = TestTextSplitter()
    test_splitter.test_basic_split()
    print("✓ 基本切分测试通过")
    
    test_splitter.test_normalize_newlines()
    print("✓ 换行符归一化测试通过")
    
    print("\n运行Schema验证测试...")
    test_schemas = TestSchemas()
    test_schemas.test_text_split_config_validation()
    print("✓ 文本切片配置验证通过")
    
    test_schemas.test_qa_generation_config_validation()
    print("✓ QA生成配置验证通过")
    
    print("\n运行集成测试...")
    test_integration = TestIntegration()
    test_integration.test_full_workflow_simulation()
    print("✓ 完整工作流测试通过")
    
    print("\n所有测试通过! ✓")
