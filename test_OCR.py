import unittest
import subprocess
import time
import cv2
import requests
from ocr_client import OCR

class OCRTestCase(unittest.TestCase):
    server_process = None

    @classmethod
    def setUpClass(cls):
        """Start the OCR server in a background process and wait for it to be ready."""
        cls.server_process = subprocess.Popen(['python', 'ocr_server.py'])
        print("Waiting for OCR server to start...")

        start_time = time.time()
        timeout = 180  # 3 minutes timeout for the server to start
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://127.0.0.1:8000/health")
                if response.status_code == 200:
                    print("OCR server is ready.")
                    time.sleep(2) # Give it a moment to settle
                    return
            except requests.ConnectionError:
                time.sleep(2)  # Wait and retry

        # If we reach here, the server did not start in time.
        cls.server_process.terminate()
        cls.server_process.wait()
        raise Exception("OCR server failed to start within the timeout period.")

    @classmethod
    def tearDownClass(cls):
        """Terminate the OCR server process."""
        if cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait()
            print("OCR server terminated.")

    def test_simple_OCR(self):
        """ Simple check of OCR to bring back text of a know image. """
        ocr = OCR(screen=None)

        image_path = 'templates/destination.png'
        orig_image = cv2.imread(image_path)
        if orig_image is None:
            self.fail(f"Could not load image at {image_path}")

        ocr_textlist = ocr.image_simple_ocr(orig_image)
        if ocr_textlist is None:
            self.fail("OCR request failed. The server might not be running or an error occurred.")

        actual = str(ocr_textlist)
        expected = "['DESTINATION', 'SIRIUS ATMOSPHERICS']"

        self.assertEqual(actual, expected)

    def test_similarity_test1(self):
        ocr = OCR(screen=None)
        s1 = "Orbital Construction Site: Wingrove's Inheritance"
        s2 = "Wingrove's Inheritance (Orbital Construction Site)"
        actual = ocr.string_similarity(s1, s2)
        print(f"Dice: {actual}")
        self.assertGreater(actual, 0.9)

    def test_similarity_test2(self):
        ocr = OCR(screen=None)
        s1 = "STAR BLAZE V2V-65W"
        s2 = "STAR BLAZE (V2V-65W)"
        actual = ocr.string_similarity(s1, s2)
        print(f"Dice: {actual}")
        self.assertGreater(actual, 0.8)


if __name__ == '__main__':
    unittest.main()
