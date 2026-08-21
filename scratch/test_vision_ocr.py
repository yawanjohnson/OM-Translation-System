import os
import sys

# Test PyObjC imports
try:
    import objc
    from Cocoa import NSURL
    from Vision import VNImageRequestHandler, VNRecognizeTextRequest
    print("✅ PyObjC and macOS Vision Framework imported successfully!")
except ImportError as e:
    print("❌ Failed to import PyObjC/Vision:", e)
    sys.exit(1)

# Check if we can instantiate VNRecognizeTextRequest
try:
    results = []
    def completion_handler(request, error):
        if error:
            print("Request error:", error)
            return
        observations = request.results()
        if observations:
            for obs in observations:
                text = obs.topCandidates_(1)[0].string()
                box = obs.boundingBox()
                results.append({
                    'text': text,
                    'x': box.origin.x,
                    'y': box.origin.y,
                    'w': box.size.width,
                    'h': box.size.height
                })

    request = VNRecognizeTextRequest.alloc().initWithCompletionHandler_(completion_handler)
    request.setRecognitionLevel_(0)  # VNRequestTextRecognitionLevelAccurate is 0
    # Try setting recognition languages
    request.setRecognitionLanguages_(["zh-Hant", "en-US"])
    print("✅ Successfully instantiated and configured VNRecognizeTextRequest!")
except Exception as e:
    print("❌ Failed to instantiate VNRecognizeTextRequest:", e)
    sys.exit(1)

print("\n🎉 macOS Native Vision OCR library is ready for local offline OCR! 🎉")
