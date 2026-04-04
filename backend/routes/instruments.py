from fastapi import APIRouter, Depends, HTTPException, status

from src.models.instrument import Instrument
from src.services.instrument_service import InstrumentService, get_instrument_service

router = APIRouter(prefix="/instruments")


@router.get("/", response_model=list[Instrument], summary="List all instruments")
def list_instruments(service: InstrumentService = Depends(get_instrument_service)) -> list[Instrument]:
    return service.list()


@router.get("/{instrument_id}", response_model=Instrument, summary="Get an instrument by ID")
def get_instrument(instrument_id: int, service: InstrumentService = Depends(get_instrument_service)) -> Instrument:
    instrument = service.get(instrument_id)
    if not instrument:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found")
    return instrument


@router.delete(
    "/{instrument_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an instrument",
)
def delete_instrument(
    instrument_id: int,
    service: InstrumentService = Depends(get_instrument_service),
) -> None:
    if not service.delete(instrument_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found")
