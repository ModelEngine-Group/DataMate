# 数据管理服务单元测试配置文件

# 测试覆盖范围说明
## 1. Application Service 层测试
- TagApplicationServiceTest.java: 标签应用服务测试，覆盖标签创建、查询、搜索等核心功能
- DatasetApplicationServiceTest.java: 数据集应用服务测试，覆盖数据集CRUD操作、统计信息获取等
- DatasetFileApplicationServiceTest.java: 数据集文件应用服务测试，覆盖文件上传、下载、删除等操作

## 2. REST Controller 层测试  
- TagControllerTest.java: 标签REST控制器测试，覆盖HTTP接口的请求响应处理
- DatasetControllerTest.java: 数据集REST控制器测试，覆盖分页查询、CRUD操作的HTTP接口
- DatasetFileControllerTest.java: 文件控制器测试，覆盖文件上传下载的HTTP接口
- DatasetTypeControllerTest.java: 数据集类型控制器测试，覆盖数据集类型查询接口

## 3. Domain Model 层测试
- TagTest.java: 标签领域模型测试，覆盖使用计数器等业务逻辑
- DatasetTest.java: 数据集领域模型测试，覆盖文件添加移除、标签管理等业务逻辑  
- DatasetFileTest.java: 数据集文件领域模型测试，覆盖文件属性管理

## 4. Integration 集成测试
- DataManagementIntegrationTest.java: 集成测试，覆盖各层协作的完整业务流程

# 测试覆盖的主要功能点

## 标签管理
- ✅ 标签创建（含重复名称检测）
- ✅ 标签查询（按ID、按名称）  
- ✅ 标签搜索（关键词模糊匹配）
- ✅ 标签使用计数统计
- ✅ 所有标签列表查询（按使用次数排序）

## 数据集管理
- ✅ 数据集创建（含标签关联）
- ✅ 数据集更新（名称、描述、标签、状态）
- ✅ 数据集删除（含关联关系清理）
- ✅ 数据集详情查询
- ✅ 数据集分页查询（支持类型、状态、关键词、标签筛选）
- ✅ 数据集统计信息获取（文件数量、大小、完成率等）

## 文件管理  
- ✅ 文件上传（支持MultipartFile）
- ✅ 文件下载（Resource响应）
- ✅ 文件删除（含存储清理）
- ✅ 文件列表分页查询
- ✅ 文件详情查询
- ✅ 文件类型和格式检测

## 数据集类型管理
- ✅ 预定义数据集类型查询
- ✅ 类型属性验证（名称、描述、支持格式、图标）

## HTTP接口
- ✅ REST API请求响应处理
- ✅ 分页参数处理
- ✅ 异常情况的HTTP状态码返回
- ✅ 数据传输对象(DTO)转换

## 错误处理
- ✅ 业务异常处理（重复创建、资源不存在等）
- ✅ 系统异常处理（IO异常等）
- ✅ 参数验证异常处理

## 边界条件测试
- ✅ 空值、null值处理
- ✅ 空字符串、空白字符处理  
- ✅ 大文件处理
- ✅ 负数统计值处理
- ✅ 并发访问场景

# 测试工具和框架
- JUnit 5: 单元测试框架
- Mockito: Mock框架，用于依赖隔离
- Spring Test: Spring集成测试支持
- ArgumentCaptor: 参数捕获验证
- MockMultipartFile: 文件上传模拟

# 测试策略
1. 单元测试：每个方法独立测试，使用Mock隔离依赖
2. 集成测试：验证多个组件协作的完整业务流程
3. 边界测试：验证各种边界条件和异常情况
4. 契约测试：验证接口输入输出符合预期规范

# 覆盖率目标
- 行覆盖率: >90%
- 分支覆盖率: >85%  
- 方法覆盖率: >95%
- 类覆盖率: >95%

# 测试运行建议
```bash
# 运行所有测试
mvn test

# 运行特定测试类
mvn test -Dtest=TagApplicationServiceTest

# 运行测试并生成覆盖率报告
mvn test jacoco:report

# 运行集成测试
mvn test -Dtest=*IntegrationTest
```

# 注意事项
1. 所有测试都是独立的，可以单独运行
2. 使用Mock避免对外部系统的依赖
3. 测试数据使用固定值，保证测试结果可重现
4. 异常情况都有对应的测试用例覆盖
5. 集成测试验证了完整的业务流程
