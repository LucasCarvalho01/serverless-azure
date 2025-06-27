import logging
import os
import json
from io import BytesIO
from typing import Dict, Tuple
from PIL import Image, ImageEnhance
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
import azure.functions as func

SOURCE_CONTAINER = os.environ.get('SOURCE_CONTAINER', 'received-images')
DEST_CONTAINER = os.environ.get('DEST_CONTAINER', 'dest-images')
CONNECTION_STRING = os.environ['AzureWebJobsStorage']

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)

def apply_image_edits(image: Image.Image, edits: Dict[str, float]) -> Image.Image:
    if "brightness" in edits:
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.0 + edits["brightness"] / 100.0)
    
    if "contrast" in edits:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.0 + edits["contrast"] / 100.0)
    
    if "sharpness" in edits:
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.0 + edits["sharpness"] / 100.0)
    
    if "color" in edits:
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.0 + edits["color"] / 100.0)
    
    logging.info(f"Aplicadas edições: {edits}")
    return image

def get_image_from_blob(container: str, blob_name: str) -> Tuple[Image.Image, str]:
    try:
        blob_client = blob_service_client.get_blob_client(container=container, blob=blob_name)
        stream = blob_client.download_blob()
        image_data = stream.readall()
        
        img = Image.open(BytesIO(image_data))
        format = img.format
        
        logging.info(f"Imagem {blob_name} carregada do container {container} com formato {format}")
        return img, format
    except ResourceNotFoundError:
        raise ValueError("Imagem não encontrada no container de origem")

def upload_edited_image(image: Image.Image, container: str, blob_name: str, format: str) -> str:
    try:
        buffer = BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        
        dest_blob_client = blob_service_client.get_blob_client(container=container, blob=blob_name)
        dest_blob_client.upload_blob(buffer, overwrite=True)
        
        return f"https://{blob_service_client.account_name}.blob.core.windows.net/{container}/{blob_name}"
    except Exception as e:
        raise RuntimeError(f"Erro ao fazer upload da imagem editada: {str(e)}")

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processando requisição de edição de imagem')

    try:
        req_body = req.get_json()
        image_key = req_body.get('key')
        edit_properties = req_body.get('edit_properties')

        if not image_key:
            return func.HttpResponse(
                "Parâmetro 'key' é obrigatório",
                status_code=400
            )

        if not edit_properties:
            return func.HttpResponse(
                "Parâmetro 'edit_properties' é obrigatório",
                status_code=400
            )

        image, format = get_image_from_blob(SOURCE_CONTAINER, image_key)
        edited_image = apply_image_edits(image, edit_properties)
        
        dest_blob_name = f"edited-{image_key}"
        image_url = upload_edited_image(edited_image, DEST_CONTAINER, dest_blob_name, format)

        return func.HttpResponse(
            body=json.dumps({
                "message": "Imagem processada com sucesso",
                "edited_image_url": image_url,
                "source_image": f"https://{blob_service_client.account_name}.blob.core.windows.net/{SOURCE_CONTAINER}/{image_key}"
            }),
            status_code=200,
            mimetype="application/json"
        )

    except ValueError as e:
        return func.HttpResponse(str(e), status_code=404)
    except json.JSONDecodeError:
        return func.HttpResponse("Formato JSON inválido", status_code=400)
    except Exception as e:
        logging.error(f"Erro: {str(e)}")
        return func.HttpResponse(f"Erro interno: {str(e)}", status_code=500)