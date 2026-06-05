# Memory System

The memory system uses SQLite as the default local-first store.

Scopes:

* company
* client
* project
* decision
* mistake
* agent
* user preference

The interface is intentionally simple so vector-backed memory systems such as Qdrant, Pinecone, or Weaviate can be added later without breaking API consumers.

