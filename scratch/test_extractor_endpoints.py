import os
import json
import urllib.request
import urllib.error
import shutil
from pypdf import PdfWriter

def run_test():
    print("=== TESTING EXTRACTOR BACKEND ENDPOINTS (urllib version) ===")
    
    pdf_path = "test_blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with open(pdf_path, "wb") as f:
        writer.write(f)
    print(f"Created temporary mock PDF: {pdf_path}")
    
    # Copy a real PNG image from user uploads
    src_image = "/Users/yawan/.gemini/antigravity-ide/brain/5cb4859b-28b4-4964-a6a8-235c8d6cc6a0/.user_uploaded/media_1787275400773.png"
    image_path = "test_image.png"
    
    if os.path.exists(src_image):
        shutil.copy(src_image, image_path)
        print(f"Copied real test PNG: {image_path}")
    else:
        # Fallback to creating a larger mock PNG (10x10) if the source is missing
        # But this source should exist.
        raise FileNotFoundError(f"Source test image not found at {src_image}")
    
    server_url = "http://127.0.0.1:5001"
    
    # helper for multipart/form-data request
    def upload_file(url, file_path, field_name, mime_type):
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        with open(file_path, 'rb') as f:
            file_content = f.read()
            
        filename = os.path.basename(file_path)
        body = []
        body.append(f'--{boundary}'.encode('utf-8'))
        body.append(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"'.encode('utf-8'))
        body.append(f'Content-Type: {mime_type}'.encode('utf-8'))
        body.append(b'')
        body.append(file_content)
        body.append(f'--{boundary}--'.encode('utf-8'))
        body.append(b'')
        
        data = b'\r\n'.join(body)
        
        req = urllib.request.Request(url, data=data)
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        req.add_header('Content-Length', str(len(data)))
        
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode('utf-8'))

    # 3. Test PDF extraction
    print("\nTesting PDF extraction endpoint (/api/extract/pdf)...")
    try:
        status, data = upload_file(f"{server_url}/api/extract/pdf", pdf_path, "file", "application/pdf")
        print("Status code:", status)
        print("Response:", data)
        assert status == 200
        assert data["ok"] is True
        assert len(data["pages"]) == 1
        print("✅ PDF Extraction endpoint passed!")
    except Exception as e:
        print("❌ PDF Extraction endpoint failed:", e)
        cleanup(pdf_path, image_path)
        raise e
        
    # 4. Test Image OCR
    print("\nTesting Image OCR endpoint (/api/extract/ocr)...")
    try:
        status, data = upload_file(f"{server_url}/api/extract/ocr", image_path, "file", "image/png")
        print("Status code:", status)
        print("Response layout keys:", data.keys())
        assert status == 200
        assert data["ok"] is True
        assert "blocks" in data
        print(f"✅ Image OCR endpoint passed! Detected {len(data['blocks'])} text blocks.")
        if len(data['blocks']) > 0:
            print("First block example:", data['blocks'][0])
    except Exception as e:
        print("❌ Image OCR endpoint failed:", e)
        cleanup(pdf_path, image_path)
        raise e
        
    cleanup(pdf_path, image_path)
    print("\n🎉 ALL BACKEND ENDPOINTS TESTS PASSED SUCCESSFULLY! 🎉")

def cleanup(pdf_path, image_path):
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    if os.path.exists(image_path):
        os.remove(image_path)
    print("Cleaned up temporary test files.")

if __name__ == '__main__':
    run_test()
