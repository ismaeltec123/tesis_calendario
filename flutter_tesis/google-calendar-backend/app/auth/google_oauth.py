import os
import pickle
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config.settings import settings

class GoogleAuthService:
    def __init__(self):
        self.scopes = settings.GOOGLE_SCOPES
        # Usar ruta absoluta para el archivo de credenciales (fallback)
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.credentials_file = os.path.join(current_dir, "config", "credentials.json")
        self.token_dir = os.path.join(current_dir, "tokens")
        self.token_file = os.path.join(self.token_dir, "token.pickle")
        
        # Crear directorio de tokens si no existe
        os.makedirs(self.token_dir, exist_ok=True)
    
    def _get_client_config(self):
        """Obtiene la configuración del cliente desde variables de entorno o archivo"""
        try:
            # Intentar primero con variables de entorno (para producción)
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
            
            if client_id and client_secret:
                print("🔑 Usando credenciales desde variables de entorno")
                return {
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                    }
                }
            
            # Fallback: usar archivo de credenciales (para desarrollo local)
            if os.path.exists(self.credentials_file):
                print(f"📄 Usando credenciales desde archivo: {self.credentials_file}")
                with open(self.credentials_file, 'r') as f:
                    return json.load(f)
            
            raise FileNotFoundError("No se encontraron credenciales de Google. Configure GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET como variables de entorno o coloque credentials.json en config/")
            
        except Exception as e:
            print(f"❌ Error obteniendo configuración del cliente: {e}")
            raise
        
    def get_authorization_url(self):
        """Genera la URL de autorización de Google"""
        try:
            client_config = self._get_client_config()
            
            print(f"🔗 Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
            
            flow = Flow.from_client_config(
                client_config,
                scopes=self.scopes,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            print(f"✅ URL de autorización generada correctamente")
            return authorization_url, state
            
        except Exception as e:
            print(f"❌ Error generando URL de autorización: {e}")
            raise
    
    def get_credentials_from_code(self, authorization_code: str):
        """Intercambia el código de autorización por credenciales"""
        try:
            client_config = self._get_client_config()
            
            flow = Flow.from_client_config(
                client_config,
                scopes=self.scopes,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )
            
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Guardar credenciales
            self._save_credentials(credentials)
            
            return credentials
            
        except Exception as e:
            print(f"❌ Error obteniendo credenciales desde código: {e}")
            raise
    
    def get_stored_credentials(self):
        """Obtiene las credenciales almacenadas"""
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                credentials = pickle.load(token)
                
            # Verificar si las credenciales son válidas
            if credentials and credentials.valid:
                return credentials
            
            # Refrescar si han expirado
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self._save_credentials(credentials)
                return credentials
                
        return None
    
    def _save_credentials(self, credentials):
        """Guarda las credenciales en archivo"""
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        with open(self.token_file, 'wb') as token:
            pickle.dump(credentials, token)
    
    def revoke_credentials(self):
        """Revoca las credenciales y elimina el archivo"""
        credentials = self.get_stored_credentials()
        if credentials:
            credentials.revoke(Request())
        
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
    
    def get_calendar_service(self):
        """Obtiene el servicio de Google Calendar"""
        credentials = self.get_stored_credentials()
        if not credentials:
            raise Exception("No hay credenciales válidas. El usuario debe autenticarse primero.")
        
        service = build('calendar', 'v3', credentials=credentials)
        return service
