import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings
import magic
from PIL import Image
from io import BytesIO

def handle_uploaded_file(file, user_id):
    """
    Handle file upload for chat messages.
    Returns a dictionary with file information or an error message.
    """
    try:
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return {'error': 'File size exceeds the maximum limit of 10MB'}
        
        # Get file extension
        file_extension = os.path.splitext(file.name)[1].lower()
        
        # Generate a unique filename
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        filename = f"chat_uploads/{user_id}/{timestamp}_{file.name}"
        
        # Read the file content
        file_content = file.read()
        
        # Detect MIME type
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file_content)
        
        # Check if it's an image
        is_image = mime_type.startswith('image/')
        
        # Process image if it's an image
        if is_image:
            try:
                # Open the image
                img = Image.open(BytesIO(file_content))
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large (max 1200px on the longest side)
                max_size = (1200, 1200)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save the processed image as WebP for better compression
                output = BytesIO()
                img_format = 'webp'  # Default to webp for better compression
                img.save(output, format=img_format, quality=85, optimize=True)
                file_content = output.getvalue()
                
                # Update filename extension to webp
                filename = f"{os.path.splitext(filename)[0]}.{img_format}"
                
            except Exception as e:
                # If image processing fails, still save the original
                print(f"Image processing error: {e}")
        
        # Save the file
        file_path = default_storage.save(filename, ContentFile(file_content))
        file_url = default_storage.url(file_path)
        
        # Get file size for display
        file_size = len(file_content)
        size_suffixes = ['B', 'KB', 'MB', 'GB']
        size_index = 0
        while file_size > 1024 and size_index < len(size_suffixes) - 1:
            file_size /= 1024.0
            size_index += 1
        file_size_display = f"{file_size:.1f} {size_suffixes[size_index]}"
        
        return {
            'success': True,
            'file_path': file_path,
            'file_url': file_url,
            'file_name': os.path.basename(file.name),
            'file_size': file_size_display,
            'is_image': is_image,
            'mime_type': mime_type,
        }
    except Exception as e:
        return {'error': str(e)}
