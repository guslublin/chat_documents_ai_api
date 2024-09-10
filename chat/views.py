import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import openai
from pinecone import Pinecone, ServerlessSpec, PineconeApiException

# Configuración de OpenAI
openai.api_key = "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"

# Inicializar Pinecone usando la nueva API
pinecone_client = Pinecone(api_key='e1870b8a-1371-4d9f-b4ac-757a9d69b06e')

# Verificar si el índice existe, si no, crearlo
try:
    indexes = pinecone_client.list_indexes()
    if 'chat-documents-ai' not in indexes:
        pinecone_client.create_index(
            name='chat-documents-ai',
            dimension=1536,  # Ajustado a tu modelo de embeddings
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
except PineconeApiException as e:
    if e.status == 409:  # Manejar conflicto si ya existe el índice
        print("El índice ya existe. Continuando...")
    else:
        raise  # Re-lanzar la excepción si es otro error

# Conectarse al índice
index = pinecone_client.Index('chat-documents-ai')

# Función para listar archivos en 'uploaded_files'
def list_uploaded_files():
    upload_dir = os.path.join(settings.BASE_DIR, 'uploaded_files')
    if not os.path.exists(upload_dir):
        return []
    return os.listdir(upload_dir)

# Función para listar archivos en 'processed_files'
def list_processed_files():
    processed_dir = os.path.join(settings.BASE_DIR, 'processed_files')
    if not os.path.exists(processed_dir):
        return []
    return os.listdir(processed_dir)

# Extraer texto de un archivo PDF
def extract_text_from_pdf(file_path):
    from PyPDF2 import PdfReader
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Función para generar embeddings con OpenAI
def generate_embeddings(text):
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    return response['data'][0]['embedding']

@csrf_exempt
def upload_file(request):
    """Subir archivo PDF sin procesar el contenido"""
    if request.method == 'POST':
        uploaded_file = request.FILES['file']

        # Directorio donde se guardan los archivos
        upload_dir = os.path.join(settings.BASE_DIR, 'uploaded_files')

        # Crear el directorio si no existe
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        # Guardar el archivo
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Devolver la lista de archivos actualizados
        return JsonResponse({
            'status': 'File uploaded',
            'uploaded_files': list_uploaded_files(),
            'processed_files': list_processed_files()
        })

    return JsonResponse({'error': 'Only POST method allowed'}, status=400)

@csrf_exempt
def delete_file(request):
    """Eliminar un archivo de 'uploaded_files'"""
    if request.method == 'POST':
        file_name = request.POST.get('file_name')
        if file_name:
            file_path = os.path.join(settings.BASE_DIR, 'uploaded_files', file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                return JsonResponse({
                    'status': 'File deleted',
                    'uploaded_files': list_uploaded_files(),
                    'processed_files': list_processed_files()
                })
            else:
                return JsonResponse({'error': 'File not found'}, status=404)
    return JsonResponse({'error': 'Only POST method allowed'}, status=400)

def get_files(request):
    """Obtener lista de archivos en 'uploaded_files' y 'processed_files'"""
    return JsonResponse({
        'uploaded_files': list_uploaded_files(),
        'processed_files': list_processed_files()
    })

@csrf_exempt
def train_ia(request):
    """Entrenar IA con archivos PDF en 'uploaded_files' y luego moverlos a 'processed_files'"""
    if request.method == 'POST':
        upload_dir = os.path.join(settings.BASE_DIR, 'uploaded_files')
        processed_dir = os.path.join(settings.BASE_DIR, 'processed_files')

        # Crear el directorio de archivos procesados si no existe
        if not os.path.exists(processed_dir):
            os.makedirs(processed_dir)

        # Procesar todos los archivos en 'uploaded_files'
        files_processed = []
        for file_name in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, file_name)

            # Procesar solo archivos PDF
            if file_name.endswith('.pdf'):
                try:
                    # Extraer texto del PDF
                    text_content = extract_text_from_pdf(file_path)

                    # Generar embeddings del texto
                    embeddings = generate_embeddings(text_content)

                    # Subir los embeddings a Pinecone
                    index.upsert([(file_name, embeddings)])

                    # Mover el archivo a 'processed_files'
                    new_file_path = os.path.join(processed_dir, file_name)
                    os.rename(file_path, new_file_path)

                    files_processed.append(file_name)

                except Exception as e:
                    return JsonResponse({'error': f'Error procesando {file_name}: {str(e)}'}, status=500)

        return JsonResponse({
            'status': 'Training completed',
            'processed_files': list_processed_files(),
            'files_processed': files_processed
        })

    return JsonResponse({'error': 'Only POST method allowed'}, status=400)
