#!/usr/bin/env python3
"""
Data-Engine Python执行器
基于Ray的统一算子执行入口
"""

import ray
import json
import logging
import importlib
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OperatorType(Enum):
    """算子类型"""
    DATA_JUICER = "data_juicer"
    DINGO = "dingo"
    UNSTRUCTURED_IO = "unstructured_io"
    CUSTOM = "custom"

@dataclass
class OperatorConfig:
    """算子配置"""
    name: str
    type: OperatorType
    version: str
    parameters: Dict[str, Any]

@dataclass
class ExecutionContext:
    """执行上下文"""
    task_id: str
    user_id: str
    workspace_id: str
    input_path: str
    output_path: str
    temp_path: str

@ray.remote
class OperatorExecutor:
    """算子执行器Actor"""
    
    def __init__(self):
        self.initialized = False
        self.operators = {}
        
    def initialize(self):
        """初始化执行器"""
        if not self.initialized:
            logger.info("Initializing operator executor...")
            self._load_operators()
            self.initialized = True
            logger.info("Operator executor initialized successfully")
    
    def _load_operators(self):
        """加载算子包装器"""
        try:
            # 导入算子包装器
            from wrappers.data_juicer_wrapper import DataJuicerWrapper
            from wrappers.dingo_wrapper import DingoWrapper
            from wrappers.unstructured_io_wrapper import UnstructuredIOWrapper
            from wrappers.custom_operator_loader import CustomOperatorLoader
            
            self.operators = {
                OperatorType.DATA_JUICER: DataJuicerWrapper(),
                OperatorType.DINGO: DingoWrapper(),
                OperatorType.UNSTRUCTURED_IO: UnstructuredIOWrapper(),
                OperatorType.CUSTOM: CustomOperatorLoader()
            }
            logger.info(f"Loaded {len(self.operators)} operator types")
        except Exception as e:
            logger.error(f"Failed to load operators: {e}")
            raise
    
    def execute_operator(self, 
                        config: Dict[str, Any], 
                        context: Dict[str, Any]) -> Dict[str, Any]:
        """执行算子"""
        try:
            # 解析配置
            operator_config = OperatorConfig(
                name=config['name'],
                type=OperatorType(config['type']),
                version=config.get('version', '1.0.0'),
                parameters=config.get('parameters', {})
            )
            
            execution_context = ExecutionContext(
                task_id=context['task_id'],
                user_id=context['user_id'],
                workspace_id=context['workspace_id'],
                input_path=context['input_path'],
                output_path=context['output_path'],
                temp_path=context.get('temp_path', '/tmp')
            )
            
            logger.info(f"Executing operator: {operator_config.name} "
                       f"(type: {operator_config.type.value})")
            
            # 获取对应的算子包装器
            wrapper = self.operators.get(operator_config.type)
            if not wrapper:
                raise ValueError(f"Unsupported operator type: {operator_config.type}")
            
            # 执行算子
            result = wrapper.execute(operator_config, execution_context)
            
            logger.info(f"Operator {operator_config.name} executed successfully")
            return {
                'status': 'success',
                'result': result,
                'task_id': execution_context.task_id
            }
            
        except Exception as e:
            logger.error(f"Operator execution failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'task_id': context.get('task_id', 'unknown')
            }

class OperatorRuntime:
    """算子运行时管理器"""
    
    def __init__(self, ray_address: Optional[str] = None):
        self.ray_address = ray_address
        self.executor_pool = []
        self.pool_size = 4  # 默认4个执行器
        
    def initialize(self):
        """初始化运行时"""
        # 连接到Ray集群
        if self.ray_address:
            ray.init(address=self.ray_address)
        else:
            ray.init()
            
        logger.info("Connected to Ray cluster")
        
        # 创建执行器池
        self._create_executor_pool()
        
    def _create_executor_pool(self):
        """创建执行器池"""
        logger.info(f"Creating executor pool with {self.pool_size} executors")
        
        for i in range(self.pool_size):
            executor = OperatorExecutor.remote()
            executor.initialize.remote()
            self.executor_pool.append(executor)
            
        logger.info("Executor pool created successfully")
    
    def submit_task(self, config: Dict[str, Any], context: Dict[str, Any]) -> ray.ObjectRef:
        """提交任务到执行器池"""
        # 简单的轮询调度
        executor = self.executor_pool[0]  # TODO: 实现更智能的调度策略
        
        return executor.execute_operator.remote(config, context)
    
    def get_result(self, task_ref: ray.ObjectRef) -> Dict[str, Any]:
        """获取任务结果"""
        return ray.get(task_ref)
    
    def shutdown(self):
        """关闭运行时"""
        logger.info("Shutting down operator runtime")
        ray.shutdown()

def main():
    """主函数"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Data-Engine Operator Runtime')
    parser.add_argument('--ray-address', help='Ray cluster address')
    parser.add_argument('--config', required=True, help='Operator config file')
    parser.add_argument('--context', required=True, help='Execution context file')
    
    args = parser.parse_args()
    
    # 读取配置文件
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    with open(args.context, 'r') as f:
        context = json.load(f)
    
    # 初始化运行时
    runtime = OperatorRuntime(args.ray_address)
    runtime.initialize()
    
    try:
        # 提交任务
        task_ref = runtime.submit_task(config, context)
        
        # 等待结果
        result = runtime.get_result(task_ref)
        
        # 输出结果
        print(json.dumps(result, indent=2))
        
        # 设置退出码
        sys.exit(0 if result['status'] == 'success' else 1)
        
    finally:
        runtime.shutdown()

if __name__ == '__main__':
    main()
