from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from .models import Document
from .readme_generator import process_uploaded_files
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.files.base import ContentFile
from wsgiref.util import FileWrapper
import zipfile
import io
import os
from django.conf import settings
from django.urls import reverse
import threading

import logging

logger = logging.getLogger(__name__)

def home(request):
    if request.method == 'POST':
        source_code = request.FILES.get('source_code')
        presentation = request.FILES.get('presentation')
        
        if source_code and presentation:
            try:
                # Read and re-encode the source code file
                source_code_content = source_code.read()
                try:
                    source_code_text = source_code_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        source_code_text = source_code_content.decode('cp949')
                    except UnicodeDecodeError:
                        source_code_text = source_code_content.decode('euc-kr', errors='ignore')
                
                # Save the re-encoded content
                document = Document()
                document.source_code.save(source_code.name, ContentFile(source_code_text.encode('utf-8')), save=False)
                document.presentation = presentation
                document.save()
                
                # Start the README generation in a separate thread
                threading.Thread(target=generate_readme, args=(document.id,)).start()
                
                return HttpResponseRedirect(reverse('loading') + f'?document_id={document.id}')
            except Exception as e:
                logger.error(f"Error processing files: {str(e)}")
                return render(request, 'home.html', {'error': str(e)})
        else:
            logger.warning("Missing files in upload")
            return render(request, 'home.html', {'error': 'Please upload both source code and presentation files.'})
    
    return render(request, 'home.html')

def generate_readme(document_id):
    try:
        document = Document.objects.get(id=document_id)
        readme_content = process_uploaded_files(document)
        document.readme = readme_content
        document.save()
        logger.info(f"README generated successfully for document {document_id}")
    except Exception as e:
        logger.error(f"Error generating README for document {document_id}: {str(e)}")

def regenerate_readme(request, document_id):
    try:
        document = Document.objects.get(id=document_id)
        readme_content = process_uploaded_files(document)
        document.readme = readme_content
        document.save()
        return HttpResponseRedirect(reverse('result') + f'?document_id={document_id}')
    except Document.DoesNotExist:
        return render(request, 'home.html', {'error': 'Document not found.'})
    except Exception as e:
        return render(request, 'home.html', {'error': str(e)})

def download_files(request, document_id):
    document = Document.objects.get(id=document_id)
    
    # ZIP 파일 생성
    zip_buffer = io.BytesIO()
    image_folder = os.path.join(settings.MEDIA_ROOT, 'images')
    
    if not os.path.exists(image_folder):
        logger.error(f"Image folder does not exist: {image_folder}")
        return HttpResponse('Image folder does not exist', status=400)
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # README 추가
        zip_file.writestr('README.md', document.readme)
        
        # 이미지 파일 추가
        for filename in os.listdir(image_folder):
            file_path = os.path.join(image_folder, filename)
            if os.path.isfile(file_path):
                zip_file.write(file_path, f'images/{filename}')
            else:
                logger.warning(f"Skipped non-file: {file_path}")
    
    # 버퍼 리셋
    zip_buffer.seek(0)
    
    # HTTP 응답 설정
    response = HttpResponse(FileWrapper(zip_buffer), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="project_files_{document_id}.zip"'
    
    return response

def loading(request):
    document_id = request.GET.get('document_id')
    if document_id:
        try:
            document = Document.objects.get(id=document_id)
            return render(request, 'loading.html', {'document_id': document_id})
        except Document.DoesNotExist:
            return render(request, 'home.html', {'error': 'Document not found.'})
    return render(request, 'home.html', {'error': 'Document ID not provided.'})

def check_readme_status(request):
    document_id = request.GET.get('document_id')
    if document_id:
        try:
            document = Document.objects.get(id=document_id)
            if document.readme:
                return JsonResponse({'status': 'complete'})
            else:
                return JsonResponse({'status': 'in_progress'})
        except Document.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Document not found.'})
    return JsonResponse({'status': 'error', 'message': 'Document ID not provided.'})

def result(request):
    document_id = request.GET.get('document_id')
    if document_id:
        try:
            document = Document.objects.get(id=document_id)
            return render(request, 'result.html', {'document': document})
        except Document.DoesNotExist:
            return render(request, 'home.html', {'error': 'Document not found.'})
    return HttpResponseRedirect(reverse('home'))