"""Single source of truth for every write mutation sent to DataHub GMS."""

UPDATE_DESCRIPTION = """
mutation updateDescription($input: DescriptionUpdateInput!) {
  updateDescription(input: $input)
}
"""
