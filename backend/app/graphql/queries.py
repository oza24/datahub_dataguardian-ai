"""Single source of truth for every read query sent to DataHub GMS."""

SEARCH_DATASETS = """
query search($input: SearchInput!) {
  search(input: $input) {
    searchResults {
      entity {
        urn
        ... on Dataset {
          name
          properties { name }
        }
      }
    }
  }
}
"""

GET_DATASET_SCHEMA = """
query getDatasetSchema($urn: String!) {
  dataset(urn: $urn) {
    urn
    name
    platform { name }
    schemaMetadata {
      fields {
        fieldPath
        nativeDataType
        nullable
        description
      }
    }
  }
}
"""

GET_LINEAGE = """
query getLineage($input: SearchAcrossLineageInput!) {
  searchAcrossLineage(input: $input) {
    searchResults {
      entity {
        urn
        type
      }
    }
  }
}
"""
