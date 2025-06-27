import logging
import os
from PIL import Image
from azure.storage.blob import BlobServiceClient
from io import BytesIO
import azure.functions as func

def resize_image(image_bytes):
    with Image.open(BytesIO(image_bytes)) as image:
        max_width = 150
        original_format = image.format or 'jpg'
        
        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            new_size = (max_width, new_height)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        output = BytesIO()
        image.save(output, format=original_format)
        output.seek(0)
        return output

def main(myblob: func.InputStream):
    name = myblob.name.split('/')[-1] 
    logging.info(f"Processando blob: {name}")

    try:
        blob_content = myblob.read()
        resized_image_io = resize_image(blob_content)

        connect_str = os.environ["AzureWebJobsStorage"]
        dest_container = "dest-images"
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        dest_container_client = blob_service_client.get_container_client(dest_container)

        dest_blob_name = f"resized-{name}"
        dest_blob_client = dest_container_client.get_blob_client(dest_blob_name)
        dest_blob_client.upload_blob(resized_image_io, overwrite=True)

        logging.info(f"Thumbnail {dest_blob_name} salva em {dest_container}")

    except Exception as e:
        logging.error(f"Erro ao criar thumbnail: {e}")
        raise