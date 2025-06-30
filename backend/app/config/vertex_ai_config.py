import os
from typing import Optional

class VertexAIConfig:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
    REGION = os.getenv("GCP_REGION", "us-central1")
    INDEX_ID = os.getenv("VERTEX_AI_INDEX_ID", "your-index-id")
    ENDPOINT_ID = os.getenv("VERTEX_AI_ENDPOINT_ID", "your-endpoint-id")
    DEPLOYED_INDEX_ID = os.getenv("VERTEX_AI_DEPLOYED_INDEX_ID", "your-deployed-index-id")
    
    # Storage buckets
    VECTOR_DATA_BUCKET = os.getenv("VECTOR_DATA_BUCKET", "your-vector-data-bucket")
    STAGING_BUCKET = os.getenv("STAGING_BUCKET", "your-staging-bucket")
    
    # Embedding settings
    EMBEDDING_DIMENSION = 1536
    APPROXIMATE_NEIGHBORS = 100
    
    # Search settings
    DEFAULT_TOP_K = 10
    DEFAULT_FILTER_DISTANCE = 0.8
    
    @classmethod
    def get_index_endpoint_uri(cls) -> str:
        return f"projects/{cls.PROJECT_ID}/locations/{cls.REGION}/indexEndpoints/{cls.ENDPOINT_ID}"
    
    @classmethod
    def get_index_uri(cls) -> str:
        return f"projects/{cls.PROJECT_ID}/locations/{cls.REGION}/indexes/{cls.INDEX_ID}"