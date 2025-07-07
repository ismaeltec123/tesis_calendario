from fastapi import APIRouter, HTTPException
from typing import List
from app.models.event_models import EventCreate, EventResponse, EventUpdate
from app.services.calendar_service import GoogleCalendarService
from app.services.mock_firebase import get_firebase_service

router = APIRouter(prefix="/calendar", tags=["calendar"])

calendar_service = GoogleCalendarService()
firebase_service = get_firebase_service()

@router.post("/events", response_model=EventResponse)
async def create_event(event: EventCreate):
    """Crea un evento en Google Calendar y Firebase"""
    try:
        # Convertir el evento a diccionario
        event_data = event.dict()
        
        # Crear en Google Calendar
        google_event_id = calendar_service.create_event(event_data)
        
        # Agregar el ID de Google al evento
        event_data['google_event_id'] = google_event_id
        
        # Crear en Firebase
        firebase_id = firebase_service.create_event(event_data)
        
        # Preparar respuesta
        response_data = event_data.copy()
        response_data['id'] = firebase_id
        response_data['firebase_id'] = firebase_id
        
        return EventResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear evento: {str(e)}")

@router.get("/events", response_model=List[EventResponse])
async def get_events():
    """Obtiene todos los eventos de Firebase"""
    try:
        events = firebase_service.get_all_events()
        
        response_events = []
        for event in events:
            event['id'] = event.get('firebase_id', '')
            response_events.append(EventResponse(**event))
        
        return response_events
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener eventos: {str(e)}")

@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(event_id: str, event_update: EventUpdate):
    """Actualiza un evento en Google Calendar y Firebase"""
    try:
        # Obtener el evento actual de Firebase
        events = firebase_service.get_all_events()
        current_event = None
        
        for event in events:
            if event.get('firebase_id') == event_id:
                current_event = event
                break
        
        if not current_event:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        
        # Preparar datos actualizados
        update_data = event_update.dict(exclude_unset=True)
        
        # Actualizar en Google Calendar si tiene ID de Google
        google_event_id = current_event.get('google_event_id')
        if google_event_id:
            # Combinar datos actuales con actualizaciones
            updated_data = {**current_event, **update_data}
            calendar_service.update_event(google_event_id, updated_data)
        
        # Actualizar en Firebase
        firebase_service.update_event(event_id, update_data)
        
        # Preparar respuesta
        response_data = {**current_event, **update_data}
        response_data['id'] = event_id
        
        return EventResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar evento: {str(e)}")

@router.delete("/events/{event_id}")
async def delete_event(event_id: str):
    """Elimina un evento de Google Calendar y Firebase"""
    try:
        # Obtener el evento actual de Firebase
        events = firebase_service.get_all_events()
        current_event = None
        
        for event in events:
            if event.get('firebase_id') == event_id:
                current_event = event
                break
        
        if not current_event:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        
        # Eliminar de Google Calendar si tiene ID de Google
        google_event_id = current_event.get('google_event_id')
        if google_event_id:
            calendar_service.delete_event(google_event_id)
        
        # Eliminar de Firebase
        firebase_service.delete_event(event_id)
        
        return {
            "success": True,
            "message": "Evento eliminado exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar evento: {str(e)}")
