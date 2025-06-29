# Image Processor App - Azure

Aplicação serverless para pós-processamento de imagens construída com Azure Functions + Bicep. A aplicação permite upload, edição, geração de thumbnail e download das imagens centralizadas por meio de um API Management.

## Arquitetura

A aplicação utiliza uma arquitetura serverless baseada em Azure Functions, Azure Blob Storage e API Management.

### Fluxo de dados:

1. Upload de imagem via API POST `/upload` → Imagem armazenada em container
2. Upload de imagem → Imagem armazenada no container `received-images`
3. Trigger automático no Blob Storage → Geração de thumbnail → Thumbnail armazenado em outro container
4. Edição de imagem via API POST `/edit`
5. Download da imagem via API GET `/images/{image_key}`

## Tecnologias utilizadas

- **Azure Functions**: Execução das funções serverless
- **Azure Blob Storage**: Armazenamento de imagens originais e processadas
- **API Management**: Enpoints REST para interação
- **Azure Storage SDK**: Integração com serviços de armazenamento Azure
- **Bicep**: Infraestrutura como código para Azure

## Pré-requisitos

Para desenvolvimento e deployment da aplicação:

- Azure Functions Core Tools
- Python 3
- Azure CLI
- Azure Bicep CLI

## Execução local:
Após instalar o azure-functions-core-tools, execute

```bash
python -m venv .venv
source .venv/bin/activate
func start
```

## Deployment
É possível realizar o primeiro deploy da aplicação pelo comando:

```bash
az group create --name <nome_resource_group> --location <localizacao>
az deployment group create \
  --resource-group <nome_resource_group> \
  --template-file bicep/main.bicep \
  --parameters bicep/main.parameters.json
```

### Deploy com GitHub Actions:
O projeto está configurado para CI/CD automático via GitHub Actions. Commits na branch principal acionam o deployment automaticamente.

Existe também um workflow para deploy da infraestrutura usando Bicep. Commits na branch principal que alterem arquivos na pasta `bicep/` acionam o deploy da infraestrutura.

## Endpoints da API

Após o deploy, os seguintes endpoints estarão disponíveis:

- **POST** `/save` - Upload de imagens
- **POST** `/edit` - Edição de imagens com filtros
- **GET** `/images/{image_key}` - Recuperação de imagens

### Exemplo de uso:

```bash
# Edição de imagem
curl -X POST https://<app>.azurewebsites.net/api/edit \
  -H "Content-Type: application/json" \
  -d '{
    "key": "minha-imagem.jpg", 
    "edit_properties": {
      "brightness": 20, 
      "contrast": 10,
      "sharpness": 5,
      "color": -10
    }
  }'

# Download de imagem
curl -X GET https://<app>.azurewebsites.net/api/images/edited-minha-imagem.jpg
```
