"""
数据库会话管理

提供便捷的数据库会话管理函数
"""

from typing import AsyncGenerator, TypeVar, Type, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from . import AsyncSessionLocal

T = TypeVar("T")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session


class SessionManager:
    """会话管理器，提供便捷的CRUD操作"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(
        self,
        model: Type[T],
        id: int,
        options: Optional[List] = None,
    ) -> Optional[T]:
        """根据ID获取单个对象"""
        stmt = select(model).where(model.id == id)
        if options:
            for opt in options:
                stmt = stmt.options(opt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_field(
        self,
        model: Type[T],
        field_name: str,
        value: any,
        options: Optional[List] = None,
    ) -> Optional[T]:
        """根据字段值获取单个对象"""
        stmt = select(model).where(getattr(model, field_name) == value)
        if options:
            for opt in options:
                stmt = stmt.options(opt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        model: Type[T],
        limit: Optional[int] = None,
        offset: int = 0,
        options: Optional[List] = None,
        **filters,
    ) -> List[T]:
        """获取对象列表"""
        stmt = select(model)
        if filters:
            for key, value in filters.items():
                stmt = stmt.where(getattr(model, key) == value)
        if options:
            for opt in options:
                stmt = stmt.options(opt)
        stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj: T) -> T:
        """创建新对象"""
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(self, obj: T) -> T:
        """更新对象"""
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: T) -> None:
        """删除对象"""
        await self.session.delete(obj)

    async def bulk_create(self, objects: List[T]) -> List[T]:
        """批量创建对象"""
        for obj in objects:
            self.session.add(obj)
        await self.session.flush()
        return objects

    async def commit(self) -> None:
        """提交事务"""
        await self.session.commit()

    async def rollback(self) -> None:
        """回滚事务"""
        await self.session.rollback()

    @classmethod
    async def transaction(cls, callback):
        """执行事务回调"""
        async with AsyncSessionLocal() as session:
            manager = cls(session)
            try:
                result = await callback(manager)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
