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
from .models import Document, SourceCode, Presentation

logger = logging.getLogger(__name__)

def home(request):
    if request.method == 'POST':
        source_codes = request.FILES.getlist('source_code')
        presentations = request.FILES.getlist('presentation')
        project_title = request.POST.get('project_title')
        project_description = request.POST.get('project_description')
        
        # Store previous data
        previous_data = {
            'project_title': project_title,
            'project_description': project_description,
        }
        
        if not all([source_codes, project_title, project_description]):
            return render(request, 'home.html', {
                'error': 'Please fill in all required fields.',
                'previous_data': previous_data
            })
            
        try:
            # Create main Document object
            document = Document.objects.create(
                project_title=project_title,
                project_description=project_description
            )
            
            # Process source code files
            for source_code in source_codes:
                source_code_content = source_code.read()
                try:
                    source_code_text = source_code_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        source_code_text = source_code_content.decode('cp949')
                    except UnicodeDecodeError:
                        source_code_text = source_code_content.decode('euc-kr', errors='ignore')
                
                # Save source code file
                SourceCode.objects.create(
                    document=document,
                    file=ContentFile(source_code_text.encode('utf-8'), name=source_code.name)
                )
            
            # Process presentation files
            if presentations:
                for presentation in presentations:
                    Presentation.objects.create(
                        document=document,
                        file=presentation
                    )
            
            threading.Thread(target=generate_readme, args=(document.id,)).start()
            return HttpResponseRedirect(reverse('loading') + f'?document_id={document.id}')
            
        except Exception as e:
            logger.error(f"Error processing files: {str(e)}")
            return render(request, 'home.html', {
                'error': str(e),
                'previous_data': previous_data
            })
    
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
    
    # Create ZIP file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add README
        zip_file.writestr('README.md', document.readme)
        
        # Add source code files
        for source_code in document.source_codes.all():
            file_path = os.path.join(settings.MEDIA_ROOT, source_code.file.name)
            if os.path.exists(file_path):
                # Get the original file name from the uploaded file
                original_name = source_code.file.name.split('/')[-1]  # Get just the filename
                # Remove only the random string that Django adds
                if '_' in original_name:
                    name_parts = original_name.rsplit('_', 1)  # Split from the right side only once
                    if len(name_parts) == 2 and len(name_parts[1]) >= 7:  # Check if second part looks like a random string
                        original_name = name_parts[0] + os.path.splitext(name_parts[1])[1]
                zip_file.write(file_path, f'source_code/{original_name}')
        
        # Add presentation files
        for presentation in document.presentations.all():
            file_path = os.path.join(settings.MEDIA_ROOT, presentation.file.name)
            if os.path.exists(file_path):
                # Get the original file name from the uploaded file
                original_name = presentation.file.name.split('/')[-1]  # Get just the filename
                # Remove only the random string that Django adds
                if '_' in original_name:
                    name_parts = original_name.rsplit('_', 1)  # Split from the right side only once
                    if len(name_parts) == 2 and len(name_parts[1]) >= 7:  # Check if second part looks like a random string
                        original_name = name_parts[0] + os.path.splitext(name_parts[1])[1]
                zip_file.write(file_path, f'presentations/{original_name}')
    
    # Reset buffer
    zip_buffer.seek(0)
    
    # Set up HTTP response
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