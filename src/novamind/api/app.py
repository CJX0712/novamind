"""FastAPI 应用装配：启动时构建系统，挂载路由。

作者：晨星
"""
from __future__ import annotations

from fastapi import FastAPI

from novamind.api.routes import router
from novamind.core.config import Settings
from novamind.core.container import build_system


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="NovaMind", version="1.0.0", description="本地优先模块化 AI 智能体系统")
    app.state.system = build_system(settings)
    app.include_router(router)
    return app


app = create_app()
