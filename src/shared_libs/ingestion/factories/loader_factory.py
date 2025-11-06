from typing import Dict, Type, List
import logging
import os
from shared_libs.ingestion.base.base_loader import BaseLoader
from shared_libs.ingestion.loaders.pdf_loader import PDFLoader 
from shared_libs.ingestion.loaders.docx_loader import DocxLoader 
from shared_libs.utils.exceptions import GenAIFactoryError

logger = logging.getLogger(__name__)

class LoaderFactory:
    """
    A production-grade factory for creating BaseLoader instances.
    
    It manages the registry of supported file types and ensures the correct loader 
    is instantiated for the file type being processed.
    """
    
    # Hardening 1: Registry mapping supported file types to their concrete Loader classes
    _registry: Dict[str, Type[BaseLoader]] = {
        "pdf": PDFLoader,
        "docx": DocxLoader,
        # Thêm các Loader khác tại đây (ví dụ: "txt": TXTLoader, "xlsx": XlsxLoader)
    }

    @classmethod
    def get_supported_loaders(cls, file_types: List[str]) -> Dict[str, Type[BaseLoader]]:
        """
        Hardening 2: Returns a subset of the registry based on the configured file types.
        """
        supported = {}
        unsupported = set(file_types) - set(cls._registry.keys())
        
        if unsupported:
            logger.warning(f"Configuration includes unsupported file types: {list(unsupported)}. Skipping them.")
            
        for file_type in file_types:
            if file_type in cls._registry:
                supported[file_type] = cls._registry[file_type]
                
        if not supported:
            raise GenAIFactoryError("LoaderFactory failed: No configured file types are supported by any available loader.")
            
        return supported

    @classmethod
    def create_loader(cls, file_type: str, **kwargs) -> BaseLoader:
        """
        Hardening 3: Creates a BaseLoader instance based on the file type.
        
        Args:
            file_type: Loại file (ví dụ: 'pdf').
            **kwargs: Tham số cấu hình cho Loader (hiện tại không cần).
            
        Returns:
            An instance of a class inheriting from BaseLoader.
        """
        if file_type not in cls._registry:
            logger.error(f"LoaderFactory error: Unsupported file type '{file_type}'.")
            raise ValueError(f"Unsupported file type: '{file_type}'.")
            
        loader_class = cls._registry[file_type]
        
        try:
            logger.debug(f"Creating loader instance for type: {file_type}.")
            # Instantiation (Loaders hiện tại không cần tham số)
            return loader_class(**kwargs) 
        except Exception as e:
            error_msg = f"Failed to instantiate {file_type} Loader."
            logger.critical(error_msg, exc_info=True)
            raise RuntimeError(f"{error_msg}. Critical error: {e}") from e