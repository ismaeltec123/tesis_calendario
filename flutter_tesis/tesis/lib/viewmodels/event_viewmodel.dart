import 'package:flutter/material.dart';
import '../models/event_model.dart';
import '../services/firebase_service.dart';
import '../services/google_calendar_api_service.dart';

class EventViewModel extends ChangeNotifier {
  final FirebaseService _firebaseService = FirebaseService();
  List<EventModel> _events = [];
  bool _isLoading = false;
  bool _isGoogleAuthenticated = false;
  bool _isServerRunning = false;
  String? _lastSyncMessage;

  // Getters
  List<EventModel> get events => _events;
  bool get isLoading => _isLoading;
  bool get isGoogleAuthenticated => _isGoogleAuthenticated;
  bool get isServerRunning => _isServerRunning;
  String? get lastSyncMessage => _lastSyncMessage;

  // Cargar eventos con sincronización automática de Google Calendar
  Future<void> loadEvents() async {
    _isLoading = true;
    notifyListeners();

    try {
      // 1. Verificar si el servidor backend está funcionando
      _isServerRunning = await GoogleCalendarApiService.isServerRunning();
      
      if (_isServerRunning) {
        // 2. Verificar autenticación con Google
        _isGoogleAuthenticated = await GoogleCalendarApiService.isAuthenticated();
        
        // 3. Si está autenticado, sincronizar con Google Calendar
        if (_isGoogleAuthenticated) {
          print('🔄 Sincronizando con Google Calendar...');
          final syncResult = await GoogleCalendarApiService.fullSync();
          _lastSyncMessage = syncResult['message'];
          
          if (syncResult['success']) {
            print('✅ Sincronización exitosa: ${syncResult['events_synced']} eventos procesados');
          } else {
            print('⚠️ Sincronización con errores: ${syncResult['message']}');
          }
        } else {
          print('⚠️ Google Calendar no autenticado, cargando solo desde Firebase');
          _lastSyncMessage = 'Google Calendar no autenticado';
        }
      } else {
        print('⚠️ Servidor backend no disponible, cargando solo desde Firebase');
        _lastSyncMessage = 'Servidor backend no disponible';
      }

      // 4. Cargar eventos desde la fuente correcta
      if (_isServerRunning) {
        // Si el servidor está disponible, cargar desde el backend
        _events = await GoogleCalendarApiService.getAllEvents();
        print('📱 Eventos cargados desde el backend: ${_events.length} eventos');
      } else {
        // Si no, cargar desde Firebase local
        _events = await _firebaseService.fetchEvents();
        print('📱 Eventos cargados desde Firebase local: ${_events.length} eventos');
      }
      
    } catch (e) {
      print('Error cargando eventos: $e');
      _events = [];
      _lastSyncMessage = 'Error: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Agregar evento con sincronización automática a Google Calendar
  Future<void> addEvent(EventModel event) async {
    try {
      if (_isServerRunning && _isGoogleAuthenticated) {
        // Opción 1: Usar la API que sincroniza automáticamente
        bool success = await GoogleCalendarApiService.createEvent(event);
        if (success) {
          print('✅ Evento creado y sincronizado con Google Calendar');
          // Recargar eventos para obtener el evento con todos los IDs
          await loadEvents();
        } else {
          throw Exception('Error creando evento en la API de Google Calendar');
        }
      } else {
        // Opción 2: Crear solo en Firebase (como antes)
        await _firebaseService.addEvent(event);
        await loadEvents();
        print('📝 Evento creado solo en Firebase (Google Calendar no disponible)');
      }
    } catch (e) {
      print('Error agregando evento: $e');
      // Fallback: intentar guardar solo en Firebase
      try {
        await _firebaseService.addEvent(event);
        await loadEvents();
        print('📝 Evento guardado en Firebase como fallback');
      } catch (fallbackError) {
        print('Error en fallback: $fallbackError');
        rethrow;
      }
    }
    notifyListeners();
  }

  // Actualizar evento en ambas plataformas
  Future<void> updateEvent(EventModel event) async {
    try {
      if (_isServerRunning && _isGoogleAuthenticated && event.id.isNotEmpty) {
        // Actualizar a través de la API (sincroniza automáticamente)
        bool success = await GoogleCalendarApiService.updateEvent(event.id, event);
        if (success) {
          print('✅ Evento actualizado en ambas plataformas');
          await loadEvents(); // Recargar para obtener cambios
        } else {
          throw Exception('Error actualizando evento en la API');
        }
      } else {
        // Actualizar solo en Firebase
        await _firebaseService.updateEvent(event);
        await loadEvents();
        print('📝 Evento actualizado solo en Firebase');
      }
    } catch (e) {
      print('Error actualizando evento: $e');
      // Fallback: intentar actualizar solo en Firebase
      try {
        await _firebaseService.updateEvent(event);
        await loadEvents();
        print('📝 Evento actualizado en Firebase como fallback');
      } catch (fallbackError) {
        print('Error en fallback de actualización: $fallbackError');
        rethrow;
      }
    }
    notifyListeners();
  }

  // Eliminar evento de ambas plataformas
  Future<void> deleteEvent(String eventId) async {
    try {
      if (_isServerRunning && _isGoogleAuthenticated) {
        // Eliminar a través de la API (elimina de ambos lugares)
        bool success = await GoogleCalendarApiService.deleteEvent(eventId);
        if (success) {
          print('✅ Evento eliminado de ambas plataformas');
          _events.removeWhere((event) => event.id == eventId);
        } else {
          throw Exception('Error eliminando evento en la API');
        }
      } else {
        // Eliminar solo de Firebase
        await _firebaseService.deleteEvent(eventId);
        _events.removeWhere((event) => event.id == eventId);
        print('📝 Evento eliminado solo de Firebase');
      }
    } catch (e) {
      print('Error eliminando evento: $e');
      // Fallback: intentar eliminar solo de Firebase
      try {
        await _firebaseService.deleteEvent(eventId);
        _events.removeWhere((event) => event.id == eventId);
        print('📝 Evento eliminado de Firebase como fallback');
      } catch (fallbackError) {
        print('Error en fallback de eliminación: $fallbackError');
        rethrow;
      }
    }
    notifyListeners();
  }

  // Obtener URL de autenticación de Google Calendar
  Future<String?> getGoogleAuthUrl() async {
    try {
      if (!_isServerRunning) {
        throw Exception('Servidor backend no está funcionando');
      }
      
      String? authUrl = await GoogleCalendarApiService.getGoogleAuthUrl();
      return authUrl;
    } catch (e) {
      print('Error obteniendo URL de autenticación Google: $e');
      return null;
    }
  }

  // Sincronizar manualmente con Google Calendar
  Future<void> manualSync() async {
    if (!_isServerRunning) {
      print('❌ Servidor backend no está funcionando');
      _lastSyncMessage = 'Servidor backend no disponible';
      notifyListeners();
      return;
    }

    if (!_isGoogleAuthenticated) {
      print('❌ No autenticado con Google Calendar');
      _lastSyncMessage = 'Google Calendar no autenticado';
      notifyListeners();
      return;
    }

    _isLoading = true;
    notifyListeners();

    try {
      final result = await GoogleCalendarApiService.fullSync();
      _lastSyncMessage = result['message'];
      print('🔄 Sincronización manual: ${result['message']}');
      
      // Recargar eventos después de sincronizar
      _events = await _firebaseService.fetchEvents();
      
    } catch (e) {
      print('Error en sincronización manual: $e');
      _lastSyncMessage = 'Error en sincronización: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Verificar estado de conexión y autenticación
  Future<void> checkStatus() async {
    try {
      _isServerRunning = await GoogleCalendarApiService.isServerRunning();
      if (_isServerRunning) {
        _isGoogleAuthenticated = await GoogleCalendarApiService.isAuthenticated();
      } else {
        _isGoogleAuthenticated = false;
      }
    } catch (e) {
      print('Error verificando estado: $e');
      _isServerRunning = false;
      _isGoogleAuthenticated = false;
    }
    notifyListeners();
  }

  // Importar solo desde Google Calendar (sin sincronizar hacia Google)
  Future<void> importFromGoogleOnly() async {
    if (!_isServerRunning || !_isGoogleAuthenticated) {
      print('❌ No se puede importar: servidor no disponible o no autenticado');
      return;
    }

    _isLoading = true;
    notifyListeners();

    try {
      final result = await GoogleCalendarApiService.importFromGoogle();
      _lastSyncMessage = result['message'];
      print('📥 Importación desde Google: ${result['message']}');
      
      // Recargar eventos después de importar
      await loadEvents();
      
    } catch (e) {
      print('Error importando desde Google: $e');
      _lastSyncMessage = 'Error importando: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
