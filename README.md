# Image Processor App - Azure

Aplicação serverless para processamento de imagens construída com Azure Functions. A aplicação permite upload, edição, geração de thumbnail e download das imagens centralizadas por meio de um API Management.

## Arquitetura

A aplicação utiliza uma arquitetura serverless baseada em Azure Functions, Azure Blob Storage e HTTP triggers:

### Fluxo de dados:

1. Geração de URL de upload via API POST `/save` → URL SAS temporária para upload
2. Upload de imagem → Imagem armazenada no container `received-images`
3. Trigger automático no Blob Storage → Geração de thumbnail → Thumbnail armazenado no container `dest-images`
4. Edição de imagem via API POST `/edit` → Imagem editada salva no container `dest-images`
5. Download da imagem via API GET `/images/{image_key}` → URL SAS temporária para download

## Tecnologias utilizadas

- **Azure Functions**: Execução das funções serverless em Python
- **Azure Blob Storage**: Armazenamento de imagens originais e processadas
- **Pillow (PIL)**: Biblioteca Python para processamento de imagens
- **Azure Storage SDK**: Integração com serviços de armazenamento Azure

## Pré-requisitos

Para desenvolvimento e deployment da aplicação:

- Azure Functions Core Tools
- Python 3
- Azure CLI

## Desenvolvimento local

### Configuração inicial:

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente no `local.settings.json`:
```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=<your-storage-account>;AccountKey=<your-key>;"
  }
}
```

### Execução local:

```bash
# Instalar Azure Functions Core Tools (se necessário)
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Executar localmente
func start
```

## Deployment

### Deploy manual:
```bash
# Login no Azure
az login

# Deploy da aplicação
func azure functionapp publish <your-function-app-name>
```

### Deploy com GitHub Actions:
O projeto está configurado para CI/CD automático via GitHub Actions. Commits na branch principal acionam o deployment automaticamente.

Existe também um workflow para deploy da infraestrutura usando Bicep. Commits na branch principal que alterem arquivos na pasta `bicep/` acionam o deploy da infraestrutura.

## Endpoints da API

Após o deploy, os seguintes endpoints estarão disponíveis:

- **POST** `/save` - Geração de URL para upload de imagens
- **POST** `/edit` - Edição de imagens com filtros (brilho, contraste, nitidez, cor)
- **GET** `/images/{image_key}` - Obtenção de URL para download de imagens
- **Trigger automático** - Geração de thumbnails quando imagem é carregada

### Exemplo de uso:

```bash
# Gerar URL para upload
curl -X POST https://<app>.azurewebsites.net/api/save \
  -H "Content-Type: application/json" \
  -d '{"key": "minha-imagem.jpg"}'

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

# Download de imagem processada
curl -X GET https://<app>.azurewebsites.net/api/images/edited-minha-imagem.jpg
```

## Containers do Azure Blob Storage

- **received-images**: Armazena imagens originais carregadas
- **dest-images**: Armazena imagens processadas (thumbnails e editadas)

## Configurações

### Variáveis de ambiente:
- `AzureWebJobsStorage`: String de conexão do Storage Account
- `SOURCE_CONTAINER`: Container de imagens originais (padrão: received-images)
- `DEST_CONTAINER`: Container de imagens processadas (padrão: dest-images)
