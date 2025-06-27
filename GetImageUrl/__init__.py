import logging
import os
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import ResourceNotFoundError
import azure.functions as func

def parse_connection_string(conn_string):
    parts = {}
    for part in conn_string.split(';'):
        if '=' in part:
            key, value = part.split('=', 1)
            parts[key] = value
    return parts

conn_parts = parse_connection_string(os.environ['AzureWebJobsStorage'])
ACCOUNT_NAME = conn_parts.get('AccountName', '')
ACCOUNT_KEY = conn_parts.get('AccountKey', '')
DEST_CONTAINER_NAME = os.environ.get('DEST_CONTAINER_NAME', 'dest-images')

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('GetImageURL recebeu uma solicitação')

    try:
        image_key = req.route_params.get('image_key')
        if not image_key:
            image_key = req.params.get('image_key')
        
        if not image_key:
            return func.HttpResponse(
                'image_key é obrigatório (forneça como parâmetro de rota ou query)',
                status_code=400
            )

        sas_token = generate_blob_sas(
            account_name=ACCOUNT_NAME,
            account_key=ACCOUNT_KEY,
            container_name=DEST_CONTAINER_NAME,
            blob_name=image_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=15)
        )
        blob_service_client = BlobServiceClient.from_connection_string(os.environ['AzureWebJobsStorage'])
        blob_url = blob_service_client.get_blob_client(
            container=DEST_CONTAINER_NAME,
            blob=image_key).url

        sas_url = f"{blob_url}?{sas_token}"

        return func.HttpResponse(
            body=f'{{"download_url": "{sas_url}", "image_key": "{image_key}"}}',
            status_code=200,
            mimetype="application/json"
        )

    except ResourceNotFoundError:
        return func.HttpResponse(
            'Imagem não encontrada',
            status_code=404
        )
    
    except Exception as e:
        logging.error(f'Erro ao gerar SAS URL: {str(e)}')
        return func.HttpResponse(
            f'Erro interno: {str(e)}',
            status_code=500
        )