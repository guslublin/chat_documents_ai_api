from django.urls import path
from .views import upload_file, get_files, delete_file, train_ia

urlpatterns = [
    path('upload/', upload_file, name='upload_file'),
    path('files/', get_files, name='get_files'),  # Nueva URL para listar los archivos
    path('delete/', delete_file, name='delete_file'),  # Nueva URL para eliminar archivos
    path('train_ia/', train_ia, name='train_ia'),  # Renamed URL for moving files
]