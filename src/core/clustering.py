from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
import umap
from ..models.legal_schemas import LegalEntity


class LegalHierarchicalClustering:
    """Hierarchical clustering for legal entities"""

    def __init__(self, max_clusters: int = 10, min_cluster_size: int = 3):
        self.max_clusters = max_clusters
        self.min_cluster_size = min_cluster_size

    async def perform_clustering(
        self, entity_vdb, global_config: Dict[str, Any], entities: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Perform hierarchical clustering on legal entities"""

        if len(entities) < self.min_cluster_size:
            return [entities]

        # Get embeddings for entities
        embeddings = await self._get_entity_embeddings(entity_vdb, entities)

        if embeddings is None or len(embeddings) == 0:
            return [entities]

        # Perform multi-level clustering
        hierarchical_clusters = []

        # Level 1: Coarse clustering
        level1_clusters = self._cluster_entities(
            embeddings, entities, n_clusters=min(5, len(entities) // 2)
        )

        for cluster in level1_clusters:
            if len(cluster) >= self.min_cluster_size:
                # Level 2: Fine clustering within each coarse cluster
                cluster_embeddings = await self._get_entity_embeddings(
                    entity_vdb, cluster
                )
                if cluster_embeddings is not None:
                    level2_clusters = self._cluster_entities(
                        cluster_embeddings,
                        cluster,
                        n_clusters=min(3, len(cluster) // 2),
                    )
                    hierarchical_clusters.extend(level2_clusters)
                else:
                    hierarchical_clusters.append(cluster)
            else:
                hierarchical_clusters.append(cluster)

        return hierarchical_clusters

    async def _get_entity_embeddings(
        self, entity_vdb, entities: List[Dict[str, Any]]
    ) -> np.ndarray:
        """Get embeddings for entities from vector database"""
        try:
            entity_names = [entity.get("entity_name", "") for entity in entities]

            if not entity_names:
                return np.array([])

            # Query embeddings from ChromaDB
            embeddings = []
            for name in entity_names:
                # Query similar entities to get embedding
                results = await entity_vdb.query(name, top_k=1)
                if results and len(results) > 0:
                    # Get embedding from the exact match or closest match
                    entity_data = results[0]
                    if "embedding" in entity_data:
                        embeddings.append(entity_data["embedding"])
                    else:
                        # Generate embedding if not stored
                        embedding = await entity_vdb.embedding_func([name])
                        embeddings.append(embedding[0])
                else:
                    # Generate new embedding for unknown entity
                    embedding = await entity_vdb.embedding_func([name])
                    embeddings.append(embedding[0])

            return np.array(embeddings) if embeddings else None

        except Exception as e:
            print(f"Error getting embeddings: {e}")
            return None

    def _cluster_entities(
        self, embeddings: np.ndarray, entities: List[Dict[str, Any]], n_clusters: int
    ) -> List[List[Dict[str, Any]]]:
        """Cluster entities using GMM or KMeans"""

        if len(entities) <= n_clusters:
            return [[entity] for entity in entities]

        try:
            # Reduce dimensionality if needed
            if embeddings.shape[1] > 50:
                reducer = umap.UMAP(n_components=min(50, embeddings.shape[1]))
                embeddings = reducer.fit_transform(embeddings)

            # Use GMM for clustering
            optimal_clusters = self._get_optimal_clusters(
                embeddings, max_clusters=n_clusters
            )

            if optimal_clusters > 1:
                gmm = GaussianMixture(n_components=optimal_clusters, random_state=42)
                cluster_labels = gmm.fit_predict(embeddings)
            else:
                cluster_labels = np.zeros(len(entities))

            # Group entities by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(entities[i])

            return list(clusters.values())

        except Exception as e:
            print(f"Error in clustering: {e}")
            return [entities]  # Return all entities as single cluster

    def _get_optimal_clusters(
        self, embeddings: np.ndarray, max_clusters: int = 10
    ) -> int:
        """Determine optimal number of clusters using BIC"""

        if len(embeddings) <= 2:
            return 1

        max_clusters = min(max_clusters, len(embeddings) - 1)

        try:
            bic_scores = []
            cluster_range = range(1, max_clusters + 1)

            for n_clusters in cluster_range:
                gmm = GaussianMixture(n_components=n_clusters, random_state=42)
                gmm.fit(embeddings)
                bic_scores.append(gmm.bic(embeddings))

            # Find optimal number of clusters (minimum BIC)
            optimal_idx = np.argmin(bic_scores)
            return cluster_range[optimal_idx]

        except Exception as e:
            print(f"Error determining optimal clusters: {e}")
            return min(3, max_clusters)
