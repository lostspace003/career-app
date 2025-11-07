"""
Azure Blob Storage utilities for file management
Handles uploads and generated files storage
"""

import os
from typing import Optional
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.identity import DefaultAzureCredential
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class AzureStorageManager:
    """
    Manages file storage using Azure Blob Storage
    Falls back to local storage if Azure is not configured
    """
    
    def __init__(self):
        self.use_azure = False
        self.blob_service_client = None
        self.storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "false").lower() == "true"
        
        # Initialize Azure Blob Storage if configured
        if self.storage_account_name or self.storage_connection_string:
            self._initialize_azure_storage()
        else:
            logger.info("Azure Storage not configured. Using local filesystem.")
            self._ensure_local_directories()
    
    def _initialize_azure_storage(self):
        """Initialize Azure Blob Storage client with Managed Identity or Connection String"""
        try:
            if self.use_managed_identity and self.storage_account_name:
                # Use Managed Identity (recommended for production)
                logger.info("Initializing Azure Storage with Managed Identity")
                account_url = f"https://{self.storage_account_name}.blob.core.windows.net"
                credential = DefaultAzureCredential()
                self.blob_service_client = BlobServiceClient(account_url, credential=credential)
            elif self.storage_connection_string:
                # Use Connection String (for development/testing)
                logger.info("Initializing Azure Storage with Connection String")
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    self.storage_connection_string
                )
            else:
                logger.warning("Azure Storage credentials not properly configured")
                self._ensure_local_directories()
                return
            
            # Create containers if they don't exist
            self._ensure_containers()
            self.use_azure = True
            logger.info("Azure Blob Storage initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure Storage: {str(e)}")
            logger.info("Falling back to local filesystem")
            self._ensure_local_directories()
    
    def _ensure_containers(self):
        """Ensure required containers exist"""
        containers = ["uploads", "generated"]
        for container_name in containers:
            try:
                container_client = self.blob_service_client.get_container_client(container_name)
                if not container_client.exists():
                    container_client.create_container()
                    logger.info(f"Created container: {container_name}")
            except Exception as e:
                logger.error(f"Error creating container {container_name}: {str(e)}")
    
    def _ensure_local_directories(self):
        """Ensure local directories exist for fallback storage"""
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("generated", exist_ok=True)
    
    async def save_file(self, file_content: bytes, filename: str, folder: str) -> str:
        """
        Save file to Azure Blob Storage or local filesystem
        
        Args:
            file_content: File content as bytes
            filename: Name of the file
            folder: Target folder ('uploads' or 'generated')
        
        Returns:
            File path or blob URL
        """
        if self.use_azure:
            try:
                # Upload to Azure Blob Storage
                blob_client = self.blob_service_client.get_blob_client(
                    container=folder,
                    blob=filename
                )
                blob_client.upload_blob(file_content, overwrite=True)
                blob_url = blob_client.url
                logger.info(f"File saved to Azure Blob: {blob_url}")
                return blob_url
                
            except Exception as e:
                logger.error(f"Error uploading to Azure Blob: {str(e)}")
                logger.info("Falling back to local storage")
                return self._save_local(file_content, filename, folder)
        else:
            return self._save_local(file_content, filename, folder)
    
    def _save_local(self, file_content: bytes, filename: str, folder: str) -> str:
        """Save file to local filesystem"""
        file_path = os.path.join(folder, filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        logger.info(f"File saved locally: {file_path}")
        return file_path
    
    async def get_file(self, filename: str, folder: str) -> Optional[bytes]:
        """
        Retrieve file from Azure Blob Storage or local filesystem
        
        Args:
            filename: Name of the file
            folder: Source folder ('uploads' or 'generated')
        
        Returns:
            File content as bytes or None if not found
        """
        if self.use_azure:
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=folder,
                    blob=filename
                )
                download_stream = blob_client.download_blob()
                return download_stream.readall()
                
            except Exception as e:
                logger.error(f"Error downloading from Azure Blob: {str(e)}")
                return self._get_local(filename, folder)
        else:
            return self._get_local(filename, folder)
    
    def _get_local(self, filename: str, folder: str) -> Optional[bytes]:
        """Get file from local filesystem"""
        file_path = os.path.join(folder, filename)
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None
    
    def get_file_path(self, filename: str, folder: str) -> str:
        """
        Get file path for local storage or blob URL for Azure
        
        Args:
            filename: Name of the file
            folder: Folder name
        
        Returns:
            Local path or Azure blob URL
        """
        if self.use_azure:
            blob_client = self.blob_service_client.get_blob_client(
                container=folder,
                blob=filename
            )
            return blob_client.url
        else:
            return os.path.join(folder, filename)
    
    async def delete_file(self, filename: str, folder: str) -> bool:
        """
        Delete file from Azure Blob Storage or local filesystem
        
        Args:
            filename: Name of the file
            folder: Folder name
        
        Returns:
            True if successful, False otherwise
        """
        if self.use_azure:
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=folder,
                    blob=filename
                )
                blob_client.delete_blob()
                logger.info(f"Deleted blob: {folder}/{filename}")
                return True
            except Exception as e:
                logger.error(f"Error deleting blob: {str(e)}")
                return False
        else:
            try:
                file_path = os.path.join(folder, filename)
                os.remove(file_path)
                logger.info(f"Deleted local file: {file_path}")
                return True
            except Exception as e:
                logger.error(f"Error deleting local file: {str(e)}")
                return False


# Global storage manager instance
storage_manager = AzureStorageManager()
