from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database.session import get_session
from src.models.publisher import Publisher

router = APIRouter(prefix="/publishers")


@router.get("", response_model=list[Publisher], summary="List all publishers")
def list_publishers(session: Session = Depends(get_session)) -> list[Publisher]:
    return list(session.exec(select(Publisher)).all())


@router.get("/{publisher_id}", response_model=Publisher, summary="Get a publisher by ID")
def get_publisher(publisher_id: int, session: Session = Depends(get_session)) -> Publisher:
    publisher = session.get(Publisher, publisher_id)
    if not publisher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publisher not found")
    return publisher