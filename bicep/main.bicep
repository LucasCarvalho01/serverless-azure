param appName string = 'imgproc'
param environment string = 'dev'
param location string = 'eastus'
param publisherEmail string = 'lucascarvalhopc@hotmail.com'
param publisherName string = 'image-processor-org'

var storageAccountName = '${appName}${environment}sa01'
var appInsightsName = '${appName}-${environment}-ai'
var appServicePlanName = '${appName}-${environment}-plan'
var functionAppName = '${appName}-${environment}-func'
var apiManagementName = '${appName}-${environment}-apim'
var apimApiName = '${appName}-api'

// Storage account 
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowCrossTenantReplication: false
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    accessTier: 'Hot'
  }
}

resource storageAccount_default 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  sku: {
    name: 'Standard_LRS'
    tier: 'Standard'
  }
  properties: {
    cors: {
      corsRules: [
        {
          allowedOrigins: [
            'http://localhost:8000'
          ]
          allowedMethods: [
            'PATCH'
            'PUT'
            'OPTIONS'
            'POST'
            'GET'
            'HEAD'
          ]
          maxAgeInSeconds: 3600
          exposedHeaders: [
            '*'
          ]
          allowedHeaders: [
            '*'
          ]
        }
        {
          allowedOrigins: [
            'https://ashy-smoke-018632d0f.6.azurestaticapps.net'
          ]
          allowedMethods: [
            'GET'
            'POST'
            'OPTIONS'
            'PUT'
            'PATCH'
            'HEAD'
          ]
          maxAgeInSeconds: 3600
          exposedHeaders: [
            '*'
          ]
          allowedHeaders: [
            '*'
          ]
        }
      ]
    }
    deleteRetentionPolicy: {
      allowPermanentDelete: false
      enabled: false
    }
  }
}

resource receivedImagesContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: storageAccount_default
  name: 'received-images'
  properties: {
    publicAccess: 'None'
  }
}

resource destImagesContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: storageAccount_default
  name: 'dest-images'
  properties: {
    publicAccess: 'None'
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
    size: 'Y1'
    family: 'Y'
    capacity: 0
  }
  kind: 'functionapp'
  properties: {
    perSiteScaling: false
    elasticScaleEnabled: false
    maximumElasticWorkerCount: 1
    isSpot: false
    reserved: true
    isXenon: false
    hyperV: false
    targetWorkerCount: 0
    targetWorkerSizeId: 0
    zoneRedundant: false
  }
}

// Function App
resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https,AccountName=${storageAccount.name},AccountKey=${listKeys(storageAccount.id, storageAccount.apiVersion).keys[0].value}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.instrumentationKey
        }
      ]
    }
  }
}

// API Management Service
resource apiManagement 'Microsoft.ApiManagement/service@2023-05-01-preview' = {
  name: apiManagementName
  location: location
  sku: {
    name: 'Consumption'
    capacity: 0
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
}

// API Definition 
resource apimApi 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  parent: apiManagement
  name: apimApiName
  properties: {
    displayName: 'Image Processor API'
    path: 'api'
    protocols: [
      'https'
    ]
    serviceUrl: 'https://${functionAppName}.azurewebsites.net/api'
  }
}

// API Management Policy 
resource apimPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-05-01-preview' = {
  parent: apimApi
  name: 'policy'
  properties: {
    value: '<!--\r\n    - Policies are applied in the order they appear.\r\n    - Position <base/> inside a section to inherit policies from the outer scope.\r\n    - Comments within policies are not preserved.\r\n-->\r\n<!-- Add policies as children to the <inbound>, <outbound>, <backend>, and <on-error> elements -->\r\n<policies>\r\n  <!-- Throttle, authorize, validate, cache, or transform the requests -->\r\n  <inbound>\r\n    <base />\r\n    <cors allow-credentials="true">\r\n      <allowed-origins>\r\n        <origin>http://localhost:8000</origin>\r\n        <origin>https://lucascarvalho01.github.io</origin>\r\n        <origin>https://ashy-smoke-018632d0f.6.azurestaticapps.net</origin>\r\n      </allowed-origins>\r\n      <allowed-methods preflight-result-max-age="3600">\r\n        <method>GET</method>\r\n        <method>POST</method>\r\n        <method>PUT</method>\r\n        <method>HEAD</method>\r\n        <method>OPTIONS</method>\r\n      </allowed-methods>\r\n      <allowed-headers>\r\n        <header>*</header>\r\n      </allowed-headers>\r\n      <expose-headers>\r\n        <header>*</header>\r\n      </expose-headers>\r\n    </cors>\r\n    <validate-jwt header-name="Authorization" failed-validation-httpcode="401" failed-validation-error-message="Unauthorized - invalid token">\r\n      <openid-config url="https://login.microsoftonline.com/f704d502-c8eb-4c10-990d-aa70d85f4f89/v2.0/.well-known/openid-configuration" />\r\n      <audiences>\r\n        <audience>api://70a602af-44d8-4a76-9bd8-e299af93266a</audience>\r\n      </audiences>\r\n      <issuers>\r\n        <issuer>https://sts.windows.net/f704d502-c8eb-4c10-990d-aa70d85f4f89/</issuer>\r\n      </issuers>\r\n      <required-claims>\r\n        <claim name="roles" match="any">\r\n          <value>Image.Processor</value>\r\n        </claim>\r\n      </required-claims>\r\n    </validate-jwt>\r\n  </inbound>\r\n  <!-- Control if and how the requests are forwarded to services  -->\r\n  <backend>\r\n    <base />\r\n  </backend>\r\n  <!-- Customize the responses -->\r\n  <outbound>\r\n    <base />\r\n  </outbound>\r\n  <!-- Handle exceptions and customize error responses  -->\r\n  <on-error>\r\n    <base />\r\n  </on-error>\r\n</policies>'
    format: 'xml'
  }
}
