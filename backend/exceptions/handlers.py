import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)


async def handle_data_error(request: Request, exc: DataError) -> JSONResponse:
    logger.exception("Database data error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Database constraint validation failed",
            "error": str(getattr(exc, "orig", exc)),
        },
    )


async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.exception("Database integrity error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=409,
        content={
            "detail": "Database integrity error",
            "error": str(getattr(exc, "orig", exc)),
        },
    )


async def handle_sqlalchemy_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Unhandled database error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Database operation failed"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DataError, handle_data_error)
    app.add_exception_handler(IntegrityError, handle_integrity_error)
    app.add_exception_handler(SQLAlchemyError, handle_sqlalchemy_error)
