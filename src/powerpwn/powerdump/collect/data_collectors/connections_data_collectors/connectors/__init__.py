from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.excelonlinebusiness import ExcelOnlineBusinessConnector
from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.github import GitHubConnector
from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.gmail import GmailConnector
from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.keyvault import KeyVaultConnector
from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.shared_azureblob import SharedAzureBlobConnector
from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.shared_azurequeues import SharedAzureQueuesConnector
from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.shared_azuretables import SharedAzureTablesConnector
from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.shared_documentdb import SharedDocumentDBConnector
from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.shared_sql import SharedSqlConnector

CONNECTOR_CLS_SET = {
    KeyVaultConnector,
    GitHubConnector,
    GmailConnector,
    ExcelOnlineBusinessConnector,
    SharedSqlConnector,
    SharedDocumentDBConnector,
    SharedAzureTablesConnector,
    SharedAzureBlobConnector,
    SharedAzureQueuesConnector,
}
API_NAME_TO_CONNECTOR_CLS = {connector_cls.api_name(): connector_cls for connector_cls in CONNECTOR_CLS_SET}
