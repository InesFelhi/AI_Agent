from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Connexion à Qdrant
client = QdrantClient(url="http://localhost:6333")

# 1️⃣ Créer une collection
client.create_collection(
    collection_name="test_collection",
    vectors_config=VectorParams(size=4, distance=Distance.DOT),
)

print("Collection créée ✅")

# 2️⃣ Ajouter des vecteurs
client.upsert(
    collection_name="test_collection",
    wait=True,
    points=[
        PointStruct(id=1, vector=[0.05, 0.61, 0.76, 0.74], payload={"city": "Berlin"}),
        PointStruct(id=2, vector=[0.19, 0.81, 0.75, 0.11], payload={"city": "London"}),
        PointStruct(id=3, vector=[0.36, 0.55, 0.47, 0.94], payload={"city": "Moscow"}),
    ],
)

print("Vecteurs ajoutés ✅")

# 3️⃣ Recherche
results = client.query_points(
    collection_name="test_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    limit=2,
)

print("Résultats recherche 👇")
print(results.points)
