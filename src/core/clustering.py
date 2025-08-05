from typing import List, Dict, Any, Tuple, Set
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
import umap
from collections import defaultdict
from ..models.legal_schemas import LegalEntity, LegalLevel, LegalProvision


class LegalHierarchicalClustering:
    """Enhanced hierarchical clustering for legal entities using legal structure"""

    def __init__(self, max_clusters: int = 10, min_cluster_size: int = 3):
        self.max_clusters = max_clusters
        self.min_cluster_size = min_cluster_size

        # Legal hierarchy weights (higher = more important for clustering)
        self.level_weights = {
            LegalLevel.PHAN: 1.0,
            LegalLevel.CHUONG: 2.0,
            LegalLevel.MUC: 3.0,
            LegalLevel.DIEU: 4.0,
            LegalLevel.KHOAN: 5.0,
        }

        # Cross-reference boost factor
        self.cross_ref_boost = 1.5

    async def perform_clustering(
        self,
        entity_vdb,
        global_config: Dict[str, Any],
        entities: List[Dict[str, Any]],
        provisions: List[LegalProvision] = None,
    ) -> List[List[Dict[str, Any]]]:
        """Perform enhanced hierarchical clustering using legal structure"""

        if len(entities) < self.min_cluster_size:
            return [entities]

        # Step 1: Pre-cluster by legal hierarchy structure
        structure_clusters = self._cluster_by_legal_structure(entities, provisions)

        # Step 2: Apply semantic clustering within structure clusters
        final_clusters = []

        for structure_cluster in structure_clusters:
            if len(structure_cluster) < self.min_cluster_size:
                final_clusters.append(structure_cluster)
                continue

            # Get embeddings for semantic clustering
            embeddings = await self._get_entity_embeddings(
                entity_vdb, structure_cluster
            )

            if embeddings is None or len(embeddings) == 0:
                final_clusters.append(structure_cluster)
                continue

            # Apply semantic clustering with legal structure awareness
            semantic_clusters = await self._cluster_with_legal_context(
                embeddings, structure_cluster, entity_vdb, provisions
            )

            final_clusters.extend(semantic_clusters)

        return final_clusters

    def _cluster_by_legal_structure(
        self, entities: List[Dict[str, Any]], provisions: List[LegalProvision] = None
    ) -> List[List[Dict[str, Any]]]:
        """Pre-cluster entities based on legal hierarchy structure"""

        # Create provision lookup for quick access
        provision_lookup = {}
        if provisions:
            for provision in provisions:
                provision_lookup[provision.id] = provision

        # Group entities by hierarchy path and level
        hierarchy_groups = defaultdict(list)

        for entity in entities:
            # Get hierarchy info from entity
            level = entity.get("level", "unknown")
            source_id = entity.get("source_id", "")

            # Try to get hierarchy path from related provision
            hierarchy_path = []
            if source_id in provision_lookup:
                provision = provision_lookup[source_id]
                hierarchy_path = provision.hierarchy_path

            # Create clustering key based on legal structure
            if hierarchy_path:
                # Group by parent hierarchy (e.g., same Điều for Khoản entities)
                if level == LegalLevel.KHOAN.value and len(hierarchy_path) > 1:
                    # Khoản entities: cluster by parent Điều
                    key = tuple(hierarchy_path[:-1])
                elif level == LegalLevel.DIEU.value and len(hierarchy_path) > 2:
                    # Điều entities: cluster by parent Chương
                    key = tuple(hierarchy_path[:-2])
                else:
                    # Higher levels: cluster by immediate parent
                    key = (
                        tuple(hierarchy_path[:-1])
                        if len(hierarchy_path) > 1
                        else tuple(hierarchy_path)
                    )
            else:
                # No hierarchy info: group by level only
                key = (level,)

            hierarchy_groups[key].append(entity)

        return list(hierarchy_groups.values())

    async def _cluster_with_legal_context(
        self,
        embeddings: np.ndarray,
        entities: List[Dict[str, Any]],
        entity_vdb,
        provisions: List[LegalProvision] = None,
    ) -> List[List[Dict[str, Any]]]:
        """Apply semantic clustering enhanced with legal context"""

        if len(entities) <= 1:
            return [entities]

        try:
            # Calculate legal-aware similarity matrix
            legal_similarity = self._calculate_legal_similarity_matrix(
                entities, provisions
            )

            # Combine semantic and legal similarities
            semantic_similarity = self._calculate_semantic_similarity(embeddings)

            # Weighted combination (60% semantic, 40% legal structure)
            combined_similarity = 0.6 * semantic_similarity + 0.4 * legal_similarity

            # Convert similarity to distance for clustering
            distance_matrix = 1.0 - combined_similarity

            # Apply clustering
            optimal_clusters = self._get_optimal_clusters_from_distance(
                distance_matrix, max_clusters=min(5, len(entities) // 2)
            )

            if optimal_clusters <= 1:
                return [entities]

            # Use KMeans on distance matrix
            kmeans = KMeans(n_clusters=optimal_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(distance_matrix)

            # Group entities by cluster
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                clusters[label].append(entities[i])

            return list(clusters.values())

        except Exception as e:
            print(f"Error in legal-aware clustering: {e}")
            return [entities]

    def _calculate_legal_similarity_matrix(
        self, entities: List[Dict[str, Any]], provisions: List[LegalProvision] = None
    ) -> np.ndarray:
        """Calculate similarity matrix based on legal structure"""

        n = len(entities)
        similarity_matrix = np.eye(n)  # Identity matrix as base

        if not provisions:
            return similarity_matrix

        # Create provision lookup
        provision_lookup = {p.id: p for p in provisions}

        for i in range(n):
            for j in range(i + 1, n):
                entity_i = entities[i]
                entity_j = entities[j]

                similarity = self._calculate_entity_legal_similarity(
                    entity_i, entity_j, provision_lookup
                )

                similarity_matrix[i, j] = similarity
                similarity_matrix[j, i] = similarity  # Symmetric

        return similarity_matrix

    def _calculate_entity_legal_similarity(
        self,
        entity1: Dict[str, Any],
        entity2: Dict[str, Any],
        provision_lookup: Dict[str, LegalProvision],
    ) -> float:
        """Calculate legal similarity between two entities"""

        # Base similarity
        similarity = 0.0

        # Same level bonus
        if entity1.get("level") == entity2.get("level"):
            level = entity1.get("level", "")
            level_weight = (
                self.level_weights.get(LegalLevel(level), 1.0)
                if level in [l.value for l in LegalLevel]
                else 1.0
            )
            similarity += 0.3 * level_weight / 5.0  # Normalize by max weight

        # Hierarchy path similarity
        source1 = entity1.get("source_id", "")
        source2 = entity2.get("source_id", "")

        if source1 in provision_lookup and source2 in provision_lookup:
            prov1 = provision_lookup[source1]
            prov2 = provision_lookup[source2]

            path_sim = self._calculate_hierarchy_path_similarity(
                prov1.hierarchy_path, prov2.hierarchy_path
            )
            similarity += 0.4 * path_sim

            # Cross-reference bonus
            if self._has_cross_reference_connection(prov1, prov2):
                similarity += 0.2 * self.cross_ref_boost

        # Entity type similarity
        if entity1.get("entity_type") == entity2.get("entity_type"):
            similarity += 0.1

        return min(similarity, 1.0)  # Cap at 1.0

    def _calculate_hierarchy_path_similarity(
        self, path1: List[str], path2: List[str]
    ) -> float:
        """Calculate similarity between two hierarchy paths"""

        if not path1 or not path2:
            return 0.0

        # Find common prefix length
        common_length = 0
        min_length = min(len(path1), len(path2))

        for i in range(min_length):
            if path1[i] == path2[i]:
                common_length += 1
            else:
                break

        # Calculate similarity based on common prefix
        max_length = max(len(path1), len(path2))

        if max_length == 0:
            return 1.0

        return common_length / max_length

    def _has_cross_reference_connection(
        self, prov1: LegalProvision, prov2: LegalProvision
    ) -> bool:
        """Check if two provisions have cross-reference connections"""

        # Check if prov1 references prov2 or vice versa
        return prov2.id in prov1.cross_references or prov1.id in prov2.cross_references

    def _calculate_semantic_similarity(self, embeddings: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity matrix from embeddings"""

        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        normalized_embeddings = embeddings / norms

        # Calculate cosine similarity
        similarity_matrix = np.dot(normalized_embeddings, normalized_embeddings.T)

        return similarity_matrix

    def _get_optimal_clusters_from_distance(
        self, distance_matrix: np.ndarray, max_clusters: int = 10
    ) -> int:
        """Determine optimal number of clusters from distance matrix"""

        n_samples = distance_matrix.shape[0]

        if n_samples <= 2:
            return 1

        max_clusters = min(max_clusters, n_samples - 1)

        try:
            # Use inertia/WCSS to find optimal clusters
            inertias = []
            cluster_range = range(1, max_clusters + 1)

            for k in cluster_range:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(distance_matrix)
                inertias.append(kmeans.inertia_)

            # Find elbow using rate of change
            if len(inertias) < 3:
                return min(2, max_clusters)

            # Calculate second derivative (curvature)
            second_derivatives = []
            for i in range(1, len(inertias) - 1):
                second_deriv = inertias[i - 1] - 2 * inertias[i] + inertias[i + 1]
                second_derivatives.append(second_deriv)

            # Find maximum curvature (elbow)
            elbow_idx = (
                np.argmax(second_derivatives) + 2
            )  # +2 because we start from index 1

            return min(elbow_idx, max_clusters)

        except Exception as e:
            print(f"Error determining optimal clusters from distance: {e}")
            return min(3, max_clusters)

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
        """Legacy method - kept for backward compatibility"""

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

    def get_cluster_summary(
        self, clusters: List[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Generate summary statistics for clustering results"""

        total_entities = sum(len(cluster) for cluster in clusters)

        level_distribution = defaultdict(int)
        type_distribution = defaultdict(int)

        for cluster in clusters:
            for entity in cluster:
                level = entity.get("level", "unknown")
                entity_type = entity.get("entity_type", "unknown")
                level_distribution[level] += 1
                type_distribution[entity_type] += 1

        return {
            "total_clusters": len(clusters),
            "total_entities": total_entities,
            "avg_cluster_size": total_entities / len(clusters) if clusters else 0,
            "min_cluster_size": min(len(c) for c in clusters) if clusters else 0,
            "max_cluster_size": max(len(c) for c in clusters) if clusters else 0,
            "level_distribution": dict(level_distribution),
            "type_distribution": dict(type_distribution),
        }
