import logging
import os
import json
from azure.functions import HttpRequest, HttpResponse
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

def main(req: HttpRequest) -> HttpResponse:
    logging.info("Requisição recebida para gerar URL de upload SAS: %s", req.get_body())

    try:
        try:
            body = req.get_json()
        except ValueError:
            body = {}

        image_key = body.get('key')
        if not image_key:
            return HttpResponse(
                json.dumps({'error': 'O campo "key" (nome do arquivo) é obrigatório.'}),
                status_code=400,
                mimetype="application/json"
            )

        connect_str = os.environ["AzureWebJobsStorage"]
        container_name = os.environ.get('FRONT_BUCKET_NAME', 'received-images')

        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_client = blob_service_client.get_container_client(container_name)

        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=container_name,
            blob_name=image_key,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(write=True, create=True),
            expiry=datetime.utcnow() + timedelta(minutes=15)
        )
        blob_url = container_client.get_blob_client(image_key).url
        upload_url = f"{blob_url}?{sas_token}"

        return HttpResponse(
            json.dumps({'upload_url': upload_url}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Erro ao gerar URL SAS: {e}")
        return HttpResponse(
            json.dumps({'error': f'Erro ao gerar URL para salvar imagem: {str(e)}'}),
            status_code=500,
            mimetype="application/json"
        )