from fastapi import APIRouter, HTTPException
from app.models.event_models import SyncResponse
from app.services.calendar_service import GoogleCalendarService
from app.services.mock_firebase import get_firebase_service

router = APIRouter(prefix="/sync", tags=["synchronization"])

calendar_service = GoogleCalendarService()
firebase_service = get_firebase_service()

@router.post("/import-from-google", response_model=SyncResponse)
async def import_events_from_google():
    """Importa todos los eventos de Google Calendar a Firebase"""
    try:
        # Obtener eventos de Google Calendar
        google_events = calendar_service.list_events()
        
        events_synced = 0
        errors = []
        
        for google_event in google_events:
            try:
                # Convertir formato de Google a formato interno
                event_data = calendar_service._convert_from_google_format(google_event)
                
                # Verificar si el evento ya existe en Firebase
                existing_event = firebase_service.find_event_by_google_id(
                    google_event.get('id')
                )
                
                if not existing_event:
                    # Crear nuevo evento en Firebase
                    firebase_id = firebase_service.create_event(event_data)
                    events_synced += 1
                    print(f"Evento importado: {event_data.get('title')} -> {firebase_id}")
                else:
                    print(f"Evento ya existe: {event_data.get('title')}")
                    
            except Exception as e:
                error_msg = f"Error al procesar evento {google_event.get('summary', 'Sin título')}: {str(e)}"
                errors.append(error_msg)
                print(error_msg)
        
        return SyncResponse(
            success=True,
            message=f"Sincronización completada. {events_synced} eventos importados.",
            events_synced=events_synced,
            errors=errors
        )
        
    except Exception as e:
        return SyncResponse(
            success=False,
            message=f"Error en la sincronización: {str(e)}",
            events_synced=0,
            errors=[str(e)]
        )

@router.post("/sync-to-google", response_model=SyncResponse)
async def sync_firebase_to_google():
    """Sincroniza eventos de Firebase que no están en Google Calendar"""
    try:
        # Obtener eventos de Firebase
        firebase_events = firebase_service.get_all_events()
        
        events_synced = 0
        errors = []
        
        for firebase_event in firebase_events:
            try:
                # Solo sincronizar eventos que no tienen ID de Google
                if not firebase_event.get('google_event_id'):
                    # Crear en Google Calendar
                    google_event_id = calendar_service.create_event(firebase_event)
                    
                    # Actualizar Firebase con el ID de Google
                    firebase_service.add_google_id_to_event(
                        firebase_event.get('firebase_id'),
                        google_event_id
                    )
                    
                    events_synced += 1
                    print(f"Evento sincronizado a Google: {firebase_event.get('title')}")
                    
            except Exception as e:
                error_msg = f"Error al sincronizar evento {firebase_event.get('title', 'Sin título')}: {str(e)}"
                errors.append(error_msg)
                print(error_msg)
        
        return SyncResponse(
            success=True,
            message=f"Sincronización a Google completada. {events_synced} eventos sincronizados.",
            events_synced=events_synced,
            errors=errors
        )
        
    except Exception as e:
        return SyncResponse(
            success=False,
            message=f"Error en la sincronización: {str(e)}",
            events_synced=0,
            errors=[str(e)]
        )

@router.post("/full-sync", response_model=SyncResponse)
async def full_synchronization():
    """Realiza una sincronización completa bidireccional"""
    try:
        # Primero importar de Google Calendar
        import_result = await import_events_from_google()
        
        # Luego sincronizar a Google Calendar
        sync_result = await sync_firebase_to_google()
        
        total_synced = import_result.events_synced + sync_result.events_synced
        all_errors = import_result.errors + sync_result.errors
        
        return SyncResponse(
            success=import_result.success and sync_result.success,
            message=f"Sincronización completa finalizada. {total_synced} eventos procesados.",
            events_synced=total_synced,
            errors=all_errors
        )
        
    except Exception as e:
        return SyncResponse(
            success=False,
            message=f"Error en la sincronización completa: {str(e)}",
            events_synced=0,
            errors=[str(e)]
        )
