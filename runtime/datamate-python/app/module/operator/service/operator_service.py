"""
Operator Service
算子服务层
"""
import json
import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func

from app.core.logging import get_logger
from app.core.exception import BusinessError, ErrorCodes
from app.module.operator.repository import (
    OperatorRepository,
    CategoryRelationRepository,
    OperatorReleaseRepository,
)
from app.module.operator.schema import (
    OperatorDto,
    OperatorUpdateDto,
    OperatorReleaseDto,
)
from app.module.operator.parsers import ParserHolder
from app.module.operator.constants import (
    OPERATOR_BASE_PATH,
    UPLOAD_DIR,
    EXTRACT_DIR,
    YAML_PATH,
    SERVICE_ID,
)
from app.module.shared.file_service import FileService
from app.module.shared.file_models import (
    ChunkUploadRequestDto,
    FileUploadResult,
)

logger = get_logger(__name__)


class OperatorService:
    """算子服务"""

    def __init__(
        self,
        operator_repo: OperatorRepository,
        category_relation_repo: CategoryRelationRepository,
        operator_release_repo: OperatorReleaseRepository,
        parser_holder: ParserHolder,
        file_service: FileService,
    ):
        self.operator_repo = operator_repo
        self.category_relation_repo = category_relation_repo
        self.operator_release_repo = operator_release_repo
        self.parser_holder = parser_holder
        self.file_service = file_service

    async def get_operators(
        self,
        page: int,
        size: int,
        categories: List[List[str]],
        keyword: Optional[str],
        is_star: Optional[bool],
        db: AsyncSession
    ) -> List[OperatorDto]:
        """查询算子列表（分页）"""
        offset = page * size

        # Build query with categories filter
        conditions = []
        params = {"limit": size, "offset": offset}

        if is_star is not None:
            conditions.append("ov.is_star = :is_star")
            params["is_star"] = is_star

        if keyword:
            conditions.append(
                "(ov.operator_name ILIKE :keyword OR ov.description ILIKE :keyword)"
            )
            params["keyword"] = f"%{keyword}%"

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Handle categories grouping
        group_by = "GROUP BY ov.operator_id, ov.operator_name, ov.description, ov.version, " \
                   "ov.inputs, ov.outputs, ov.runtime, ov.settings, ov.is_star, " \
                   "ov.file_size, ov.usage_count, ov.created_at, ov.updated_at, ov.created_by, ov.updated_by"

        having_clause = ""
        if categories:
            # Flatten all category IDs for IN clause
            all_category_ids = [cat_id for sublist in categories for cat_id in sublist]
            if all_category_ids:
                where_clause += " AND category_id = ANY(:category_ids)" if where_clause else "WHERE category_id = ANY(:category_ids)"
                params["category_ids"] = all_category_ids

                # Build HAVING clause for category groups
                having_clauses = []
                for i, cat_group in enumerate(categories):
                    cat_list = ", ".join([f"'{cat_id}'" for cat_id in cat_group])
                    having_clauses.append(
                        f"SUM(CASE WHEN category_id IN ({cat_list}) THEN 1 ELSE 0 END) > 0"
                    )
                having_clause = "HAVING " + " AND ".join(having_clauses)

        query = f"""
            SELECT
                ov.operator_id AS id,
                ov.operator_name AS name,
                ov.description,
                ov.version,
                ov.inputs,
                ov.outputs,
                ov.runtime,
                ov.settings,
                ov.is_star,
                ov.file_size,
                ov.usage_count,
                ov.created_at,
                ov.updated_at,
                string_agg(ov.category_id, ',' ORDER BY ov.created_at DESC) AS categories
            FROM v_operator ov
            {where_clause}
            {group_by}
            {having_clause}
            ORDER BY ov.created_at DESC
            LIMIT :limit OFFSET :offset
        """

        result = await db.execute(text(query), params)
        rows = result.fetchall()

        # Convert to DTOs
        operators = []
        for row in rows:
            categories_list = []
            if row.categories:
                categories_list = [cat_id for cat_id in row.categories.split(',') if cat_id]

            operators.append(OperatorDto(
                id=row.id,
                name=row.name,
                description=row.description,
                version=row.version,
                inputs=row.inputs,
                outputs=row.outputs,
                runtime=row.runtime,
                settings=row.settings,
                file_name=None,
                file_size=row.file_size,
                metrics=None,
                usage_count=row.usage_count,
                is_star=row.is_star,
                categories=categories_list,
                created_at=row.created_at,
                updated_at=row.updated_at,
            ))

        return operators

    async def count_operators(
        self,
        categories: List[List[str]],
        keyword: Optional[str],
        is_star: Optional[bool],
        db: AsyncSession
    ) -> int:
        """统计算子数量"""
        conditions = []
        params = {}

        if is_star is not None:
            conditions.append("is_star = :is_star")
            params["is_star"] = is_star

        if keyword:
            conditions.append(
                "(operator_name ILIKE :keyword OR description ILIKE :keyword)"
            )
            params["keyword"] = f"%{keyword}%"

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Handle categories grouping
        group_by = "GROUP BY operator_id, operator_name, description, version, inputs, outputs, " \
                   "runtime, settings, is_star, file_size, usage_count, created_at, updated_at, " \
                   "created_by, updated_by"

        having_clause = ""
        if categories:
            # Flatten all category IDs for IN clause
            all_category_ids = [cat_id for sublist in categories for cat_id in sublist]
            if all_category_ids:
                where_clause += " AND category_id = ANY(:category_ids)" if where_clause else "WHERE category_id = ANY(:category_ids)"
                params["category_ids"] = all_category_ids

                # Build HAVING clause for category groups
                having_clauses = []
                for i, cat_group in enumerate(categories):
                    cat_list = ", ".join([f"'{cat_id}'" for cat_id in cat_group])
                    having_clauses.append(
                        f"SUM(CASE WHEN category_id IN ({cat_list}) THEN 1 ELSE 0 END) > 0"
                    )
                having_clause = "HAVING " + " AND ".join(having_clauses)

        query = f"""
            SELECT COUNT(*) as count
            FROM (
                SELECT operator_id
                FROM v_operator
                {where_clause}
                {group_by}
                {having_clause}
            ) AS t
        """

        result = await db.execute(text(query), params)
        return result.scalar() or 0

    async def get_operator_by_id(
        self,
        operator_id: str,
        db: AsyncSession
    ) -> OperatorDto:
        """根据 ID 获取算子详情"""
        result = await db.execute(
            text("""
                SELECT
                    operator_id, operator_name, description, version, inputs, outputs, runtime,
                    settings, is_star, file_name, file_size, usage_count, metrics,
                    created_at, updated_at, created_by, updated_by,
                    string_agg(category_name, ',' ORDER BY created_at DESC) AS categories
                FROM v_operator
                WHERE operator_id = :operator_id
                GROUP BY operator_id, operator_name, description, version, inputs, outputs, runtime,
                    settings, is_star, file_name, file_size, usage_count, metrics,
                    created_at, updated_at, created_by, updated_by
            """),
            {"operator_id": operator_id}
        )
        row = result.fetchone()

        if not row:
            raise BusinessError(ErrorCodes.OPERATOR_NOT_FOUND, operator_id)

        # Parse categories from comma-separated string
        categories_str = row.categories if hasattr(row, 'categories') and row.categories else ""
        categories = [c.strip() for c in categories_str.split(",")] if categories_str else []

        # Build DTO
        operator = OperatorDto(
            id=row.operator_id,
            name=row.operator_name,
            description=row.description,
            version=row.version,
            inputs=row.inputs,
            outputs=row.outputs,
            runtime=row.runtime,
            settings=row.settings,
            file_name=row.file_name,
            file_size=row.file_size,
            metrics=row.metrics,
            usage_count=row.usage_count,
            is_star=row.is_star,
            created_at=row.created_at,
            updated_at=row.updated_at,
            categories=categories,
        )

        # Read requirements and readme if file exists
        if row.file_name:
            extract_path = self._get_extract_path(
                self._get_stem(row.file_name)
            )
            operator.requirements = self._read_requirements(extract_path)
            operator.readme = self._get_readme_content(extract_path)

        # Load releases
        releases = await self.operator_release_repo.find_all_by_operator_id(
            operator_id, db
        )
        operator.releases = [
            OperatorReleaseDto(
                id=release.id,
                version=release.version,
                release_date=release.release_date,
                changelog=release.changelog
            )
            for release in releases
        ]

        return operator

    async def create_operator(
        self,
        req: OperatorDto,
        db: AsyncSession
    ) -> OperatorDto:
        """创建算子"""

        # Generate ID if not provided
        if not req.id:
            req.id = str(uuid.uuid4())

        # Override settings
        self._override_settings(req)

        # Insert operator
        await self.operator_repo.insert(req, db)
        await db.flush()

        # Insert category relations
        if req.categories:
            await self.category_relation_repo.batch_insert(
                req.id, req.categories, db
            )

        # Insert release
        if req.releases:
            release = req.releases[0]
            release.id = req.id
            release.version = req.version
            release.release_date = datetime.now()
            await self.operator_release_repo.insert(release, db)

        # Extract files
        if req.file_name:
            self.parser_holder.extract_to(
                self._get_file_type(req.file_name),
                self._get_upload_path(req.file_name),
                self._get_extract_path(self._get_stem(req.file_name))
            )

        return req

    async def update_operator(
        self,
        operator_id: str,
        req: OperatorUpdateDto,
        db: AsyncSession
    ) -> OperatorDto:
        """更新算子"""

        # Get existing operator
        existing = await self.get_operator_by_id(operator_id, db)

        # Save original version for release comparison
        original_version = existing.version

        # Merge update request into existing operator
        # Only update fields that are provided (not None)
        if req.name is not None:
            existing.name = req.name
        if req.description is not None:
            existing.description = req.description
        if req.version is not None:
            existing.version = req.version
        if req.inputs is not None:
            existing.inputs = req.inputs
        if req.outputs is not None:
            existing.outputs = req.outputs
        if req.runtime is not None:
            existing.runtime = req.runtime
        if req.settings is not None:
            existing.settings = req.settings
        if req.file_name is not None:
            existing.file_name = req.file_name
        if req.file_size is not None:
            existing.file_size = req.file_size
        if req.metrics is not None:
            existing.metrics = req.metrics
        if req.usage_count is not None:
            existing.usage_count = req.usage_count
        if req.is_star is not None:
            existing.is_star = req.is_star
        if req.categories is not None:
            existing.categories = req.categories
        if req.overrides is not None:
            existing.overrides = req.overrides

        # Override settings
        self._override_settings(existing)

        # Update operator
        await self.operator_repo.update(existing, db)

        # Update category relations
        if req.file_name is not None and req.categories is not None:
            await self.category_relation_repo.batch_update(
                operator_id, req.categories, db
            )

        # Update release
        if req.releases is not None and len(req.releases) > 0:
            release = req.releases[0]
            release.id = operator_id
            release.version = req.version
            release.release_date = datetime.now()
            if original_version == release.version:
                await self.operator_release_repo.update(release, db)
            else:
                await self.operator_release_repo.insert(release, db)

        # Extract files
        if req.file_name is not None:
            self.parser_holder.extract_to(
                self._get_file_type(req.file_name),
                self._get_upload_path(req.file_name),
                self._get_extract_path(self._get_stem(req.file_name))
            )

        await db.flush()
        return await self.get_operator_by_id(operator_id, db)

    async def delete_operator(
        self,
        operator_id: str,
        db: AsyncSession
    ) -> None:
        """删除算子"""
        # Check if operator is in use
        in_template = await self.operator_repo.operator_in_template(operator_id, db)
        in_unstop_task = await self.operator_repo.operator_in_unstop_task(operator_id, db)
        if in_template or in_unstop_task:
            raise BusinessError(ErrorCodes.OPERATOR_IN_INSTANCE)

        # Check if operator is predefined
        is_predefined = await self.category_relation_repo.operator_is_predefined(
            operator_id, db
        )
        if is_predefined:
            raise BusinessError(ErrorCodes.OPERATOR_CANNOT_DELETE_PREDEFINED)

        # Get operator for file cleanup
        operator = await self.get_operator_by_id(operator_id, db)

        # Delete from database
        await self.operator_repo.delete(operator_id, db)
        await self.category_relation_repo.delete_by_operator_id(operator_id, db)
        await self.operator_release_repo.delete(operator_id, db)

        # Delete extracted files
        if operator.file_name:
            extract_path = self._get_extract_path(self._get_stem(operator.file_name))
            shutil.rmtree(extract_path, ignore_errors=True)

    async def upload_operator(
        self,
        file_name: str,
        db: AsyncSession
    ) -> OperatorDto:
        """上传算子文件并解析元数据"""
        file_path = self._get_upload_path(file_name)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
        return self.parser_holder.parse_yaml_from_archive(
            self._get_file_type(file_name),
            file_path,
            YAML_PATH,
            file_name,
            file_size
        )

    async def pre_upload(self, db: AsyncSession) -> str:
        """预上传，返回请求 ID"""
        from app.module.operator.constants import OPERATOR_BASE_PATH, UPLOAD_DIR

        upload_path = os.path.join(OPERATOR_BASE_PATH, UPLOAD_DIR)
        req_id = await self.file_service.pre_upload(
            upload_path=upload_path,
            service_id=SERVICE_ID,
            db_session=db,
            check_info=None
        )
        return req_id

    async def chunk_upload(
        self,
        req_id: str,
        file_no: int,
        file_name: str,
        total_chunk_num: int,
        chunk_no: int,
        check_sum_hex: Optional[str],
        file_content: bytes,
        db: AsyncSession
    ) -> FileUploadResult:
        """分块上传文件"""
        from app.module.operator.constants import OPERATOR_BASE_PATH, UPLOAD_DIR

        upload_path = os.path.join(OPERATOR_BASE_PATH, UPLOAD_DIR)

        chunk_request = ChunkUploadRequestDto(
            req_id=req_id,
            file_no=file_no,
            file_name=file_name,
            total_chunk_num=total_chunk_num,
            chunk_no=chunk_no,
            check_sum_hex=check_sum_hex,
        )

        return await self.file_service.chunk_upload(
            chunk_request, upload_path, file_content, db
        )

    def download_example_operator(self, file_path: str) -> Path:
        """下载示例算子文件"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return path

    def _override_settings(self, operator: OperatorDto) -> None:
        """用 overrides 值覆盖 settings 的 defaultVal"""
        if not operator.settings or not operator.overrides:
            return

        try:
            settings = json.loads(operator.settings)
            for key, value in operator.overrides.items():
                if key not in settings:
                    continue

                setting = settings[key]
                setting_type = setting.get("type")

                match setting_type:
                    case "slider" | "switch" | "select" | "input" | "radio":
                        setting["defaultVal"] = value
                    case "checkbox":
                        setting["defaultVal"] = self._convert_to_list_string(value)
                    case "range":
                        self._update_properties(setting, value)

                settings[key] = setting

            operator.settings = json.dumps(settings)
        except json.JSONDecodeError as e:
            raise BusinessError(ErrorCodes.OPERATOR_PARSE_FAILED, str(e))

    def _convert_to_list_string(self, value: Any) -> str:
        """转换为逗号分隔的字符串"""
        if value is None:
            return ""
        if isinstance(value, list):
            return ",".join(str(v) for v in value)
        return str(value)

    def _update_properties(self, setting: Dict[str, Any], value: Any) -> None:
        """更新 range 类型的 properties"""
        if not isinstance(value, list):
            return

        properties = setting.get("properties", [])
        if not isinstance(properties, list) or len(properties) != len(value):
            return

        for i, prop in enumerate(properties):
            if isinstance(prop, dict):
                prop["defaultVal"] = value[i]

        setting["properties"] = properties

    def _read_requirements(self, extract_path: str) -> List[str]:
        """读取 requirements.txt"""
        requirements_path = Path(extract_path) / "requirements.txt"
        if not requirements_path.exists():
            return []

        requirements = []
        try:
            with open(requirements_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        requirements.append(line)
        except Exception as e:
            logger.warning(f"Failed to read requirements: {e}")
        return requirements

    def _get_readme_content(self, extract_path: str) -> str:
        """读取 README 内容"""
        dir_path = Path(extract_path)
        if not dir_path.exists() or not dir_path.is_dir():
            logger.info(f"Directory does not exist or is not a directory: {extract_path}")
            return ""

        candidates = ["README.md", "readme.md", "Readme.md"]
        for filename in candidates:
            readme_path = dir_path / filename
            if readme_path.exists() and readme_path.is_file():
                try:
                    content = readme_path.read_text(encoding='utf-8')
                    logger.info(f"Successfully read README from: {readme_path}")
                    return content
                except Exception as e:
                    logger.warning(f"Failed to read README from {readme_path}: {e}")
        logger.info(f"No README found in: {extract_path}")
        return ""

    def _get_file_type(self, file_name: str) -> str:
        """获取文件类型（扩展名）"""
        return file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ""

    def _get_stem(self, file_name: str) -> str:
        """获取文件名不含扩展名"""
        return file_name.rsplit('.', 1)[0] if '.' in file_name else file_name

    def _get_upload_path(self, file_name: str) -> str:
        """获取上传文件路径"""
        return os.path.join(OPERATOR_BASE_PATH, UPLOAD_DIR, file_name)

    def _get_extract_path(self, file_stem: str) -> str:
        """获取解压路径"""
        return os.path.join(OPERATOR_BASE_PATH, EXTRACT_DIR, file_stem)
