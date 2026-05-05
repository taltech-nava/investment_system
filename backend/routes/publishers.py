from fastapi import APIRouter, Depends

from src.models.publisher import Publisher
from src.services.publisher_service import PublisherService, get_publisher_service

router = APIRouter(prefix="/publishers")


@router.get("/", response_model=list[Publisher], summary="List all publishers")
def list_publishers(
    service: PublisherService = Depends(get_publisher_service),
) -> list[Publisher]:
    return service.list()
