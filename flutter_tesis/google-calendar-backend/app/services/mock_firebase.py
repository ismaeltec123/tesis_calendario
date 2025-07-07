"""
Servicio temporal de Firebase que funciona sin conexión real
para pruebas de Google Calendar
"""
from typing import List, Dict, Any
from datetime import datetime
import json
import os

class MockFirebaseService:
    """Servicio de Firebase simulado para pruebas"""
    
    def __init__(self):
        # Usar archivo temporal para simular base de datos
        self.data_file = "temp_events.json"
        self._ensure_data_file()
        print("🔥 Usando Firebase simulado para pruebas")
    
    def _ensure_data_file(self):
        """Asegura que existe el archivo de datos temporal"""
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({"events": []}, f)
    
    def _load_data(self):
        """Carga datos del archivo temporal"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {"events": []}
    
    def _save_data(self, data):
        """Guarda datos al archivo temporal"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_all_events(self) -> List[Dict[str, Any]]:
        """Obtiene todos los eventos"""
        try:
            data = self._load_data()
            events = data.get("events", [])
            
            # Agregar firebase_id a cada evento
            for i, event in enumerate(events):
                if 'firebase_id' not in event:
                    event['firebase_id'] = f"temp_id_{i}"
            
            return events
        except Exception as e:
            print(f"Error cargando eventos: {e}")
            return []
    
    def create_event(self, event_data: Dict[str, Any]) -> str:
        """Crea un evento"""
        try:
            data = self._load_data()
            
            # Generar ID único
            event_id = f"temp_id_{datetime.now().timestamp()}"
            event_data['firebase_id'] = event_id
            event_data['created_at'] = datetime.now().isoformat()
            
            data["events"].append(event_data)
            self._save_data(data)
            
            print(f"✅ Evento creado (simulado): {event_data.get('title', 'Sin título')}")
            return event_id
            
        except Exception as e:
            print(f"Error creando evento: {e}")
            raise
    
    def update_event(self, firebase_id: str, event_data: Dict[str, Any]) -> bool:
        """Actualiza un evento"""
        try:
            data = self._load_data()
            events = data.get("events", [])
            
            for i, event in enumerate(events):
                if event.get('firebase_id') == firebase_id:
                    # Actualizar evento
                    events[i].update(event_data)
                    events[i]['updated_at'] = datetime.now().isoformat()
                    self._save_data(data)
                    print(f"✅ Evento actualizado (simulado): {firebase_id}")
                    return True
            
            print(f"❌ Evento no encontrado: {firebase_id}")
            return False
            
        except Exception as e:
            print(f"Error actualizando evento: {e}")
            return False
    
    def delete_event(self, firebase_id: str) -> bool:
        """Elimina un evento"""
        try:
            data = self._load_data()
            events = data.get("events", [])
            
            original_count = len(events)
            events = [e for e in events if e.get('firebase_id') != firebase_id]
            
            if len(events) < original_count:
                data["events"] = events
                self._save_data(data)
                print(f"✅ Evento eliminado (simulado): {firebase_id}")
                return True
            else:
                print(f"❌ Evento no encontrado para eliminar: {firebase_id}")
                return False
                
        except Exception as e:
            print(f"Error eliminando evento: {e}")
            return False
    
    def find_event_by_google_id(self, google_event_id: str) -> Dict[str, Any]:
        """Busca un evento por su ID de Google Calendar"""
        try:
            events = self.get_all_events()
            
            for event in events:
                if event.get('google_event_id') == google_event_id:
                    return event
            
            return None
            
        except Exception as e:
            print(f"Error buscando evento por Google ID: {e}")
            return None
    
    def add_google_id_to_event(self, firebase_id: str, google_event_id: str) -> bool:
        """Agrega el ID de Google Calendar a un evento existente"""
        try:
            return self.update_event(firebase_id, {'google_event_id': google_event_id})
        except Exception as e:
            print(f"Error agregando Google ID: {e}")
            return False

# Función para obtener el servicio correcto
def get_firebase_service():
    """Retorna el servicio de Firebase (real o simulado)"""
    try:
        # Intentar usar Firebase real
        from app.services.firebase_sync import FirebaseService
        return FirebaseService()
    except Exception as e:
        # Si falla, usar versión simulada
        print(f"⚠️  Firebase no disponible, usando modo simulado")
        return MockFirebaseService()
