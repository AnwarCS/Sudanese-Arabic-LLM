import os
from mistralai import Mistral

def run_mistral_ocr(pdf_path: str, model: str = "mistral-ocr-latest") -> str:
    """
    Uploads a PDF to Mistral OCR API and returns the extracted text.

    Args:
        pdf_path (str): Path to the PDF file.
        model (str): OCR model to use (default: "mistral-ocr-latest").

    Returns:
        str: OCR result as text.
    """
    # Initialize the Mistral client
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable is not set.")

    client = Mistral(api_key=api_key)

    # Upload the PDF file
    with open(pdf_path, "rb") as file:
        uploaded_pdf = client.files.upload(
            file={
                "file_name": os.path.basename(pdf_path),
                "content": file,
            },
            purpose="ocr"
        )

    # Get signed URL for the uploaded file
    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

    # Send the document for OCR processing
    ocr_response = client.ocr.process(
        model=model,
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        }
    )

    return ocr_response.text if hasattr(ocr_response, 'text') else str(ocr_response)
