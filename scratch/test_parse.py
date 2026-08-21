import json
from app import app

def test_pm_review_parse():
    client = app.test_client()
    
    # Load the copied file content
    with open('uploads/pm_reply_test.json', 'rb') as f:
        file_data = f.read()
    
    # Call the parse-reply api
    response = client.post(
        '/api/pm-review/parse-reply',
        data={'file': (BytesIO(file_data), 'PM確認回覆_test.json')},
        content_type='multipart/form-data'
    )
    
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    from io import BytesIO
    test_pm_review_parse()
