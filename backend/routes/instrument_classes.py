from fastapi import APIRouter, Depends, HTTPException, status

from src.models.instrument_class import InstrumentClass
from src.services.instrument_class_service import (
    InstrumentClassService,
    get_instrument_class_service,
)

router = APIRouter(prefix="/instrument-classes")


@router.get("/", response_model=list[InstrumentClass], summary="List all instrument classes")
def list_instrument_classes(
    service: InstrumentClassService = Depends(get_instrument_class_service),
) -> list[InstrumentClass]:
    return service.list()


@router.get("/{class_id}", response_model=InstrumentClass, summary="Get an instrument class by ID")
def get_instrument_class(
    class_id: int,
    service: InstrumentClassService = Depends(get_instrument_class_service),
) -> InstrumentClass:
    instrument_class = service.get(class_id)
    if not instrument_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Instrument class not found"
        )
    return instrument_class
