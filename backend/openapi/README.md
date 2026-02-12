# OpenAPI Code Generation Configuration
# 基于YAML生成API代码的配置文件

## Maven Plugin Configuration for Spring Boot
# 在各个服务的pom.xml中添加以下插件配置：

```xml

<plugin>
    <groupId>org.openapitools</groupId>
    <artifactId>openapi-generator-maven-plugin</artifactId>
    <version>6.6.0</version>
    <executions>
        <execution>
            <goals>
                <goal>generate</goal>
            </goals>
            <configuration>
                <inputSpec>${project.basedir}/../../openapi/specs/${project.artifactId}.yaml</inputSpec>
                <generatorName>spring</generatorName>
                <output>${project.build.directory}/generated-sources/openapi</output>
                <apiPackage>com.datamate.${project.name}.interfaces.api</apiPackage>
                <modelPackage>com.datamate.${project.name}.interfaces.dto</modelPackage>
                <configOptions>
                    <interfaceOnly>true</interfaceOnly>
                    <useTags>true</useTags>
                    <skipDefaultInterface>true</skipDefaultInterface>
                    <hideGenerationTimestamp>true</hideGenerationTimestamp>
                    <java8>true</java8>
                    <dateLibrary>java8</dateLibrary>
                    <useBeanValidation>true</useBeanValidation>
                    <performBeanValidation>true</performBeanValidation>
                    <useSpringBoot3>true</useSpringBoot3>
                    <documentationProvider>springdoc</documentationProvider>
                </configOptions>
            </configuration>
        </execution>
    </executions>
</plugin>
```

## Gradle Plugin Configuration (Alternative)
# 如果使用Gradle，可以使用以下配置：

```gradle
plugins {
    id 'org.openapi.generator' version '6.6.0'
}

openApiGenerate {
    generatorName = "spring"
    inputSpec = "$rootDir/openapi/specs/${project.name}.yaml"
    outputDir = "$buildDir/generated-sources/openapi"
    apiPackage = "com.datamate.${project.name}.interfaces.api"
    modelPackage = "com.datamate.${project.name}.interfaces.dto"
    configOptions = [
        interfaceOnly: "true",
        useTags: "true",
        skipDefaultInterface: "true",
        hideGenerationTimestamp: "true",
        java8: "true",
        dateLibrary: "java8",
        useBeanValidation: "true",
        performBeanValidation: "true",
        useSpringBoot3: "true",
        documentationProvider: "springdoc"
    ]
}
```

## Frontend TypeScript Client Generation
# 为前端生成TypeScript客户端：

```bash
# 安装 OpenAPI Generator CLI
npm install -g @openapitools/openapi-generator-cli

# 生成TypeScript客户端
openapi-generator-cli generate \
  -i openapi/specs/data-annotation-service.yaml \
  -g typescript-axios \
  -o frontend/packages/api-client/src/generated/annotation \
  --additional-properties=supportsES6=true,npmName=@datamate/annotation-api,npmVersion=1.0.0
```

## Usage in Services
# 在各个服务中使用生成的代码：

1. **在 interfaces 层实现生成的API接口**：
```java
@RestController
@RequestMapping("/api/v1/annotation")
public class AnnotationTaskController implements AnnotationTasksApi {

    private final AnnotationTaskApplicationService annotationTaskService;

    @Override
    public ResponseEntity<AnnotationTaskPageResponse> getAnnotationTasks(
            Integer page, Integer size, String status) {
        // 实现业务逻辑
        return ResponseEntity.ok(annotationTaskService.getTasks(page, size, status));
    }
}
```

2. **在 application 层使用生成的DTO**：
```java
@Service
public class AnnotationTaskApplicationService {

    public AnnotationTaskPageResponse getTasks(Integer page, Integer size, String status) {
        // 业务逻辑实现
        // 使用生成的DTO类型
    }
}
```

## Build Integration
# 构建集成脚本位置：scripts/build/generate-api.sh

```bash
#!/bin/bash
# 生成所有服务的API代码

OPENAPI_DIR="openapi/specs"
SERVICES=(
    "data-annotation-service"
    "data-management-service"
    "data-synthesis-service"
    "data-evaluation-service"
    "pipeline-orchestration-service"
    "execution-engine-service"
    "rag-indexer-service"
    "rag-query-service"
    "api-gateway"
    "auth-service"
)

for service in "${SERVICES[@]}"; do
    echo "Generating API for $service..."
    mvn -f backend/services/$service/pom.xml openapi-generator:generate
done

echo "All APIs generated successfully!"
```
