# OrcidId

Response model for a resolved ORCID iD

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**orcid** | **str** | The resolved ORCID iD | 

## Example

```python
from orcid_service_client.models.orcid_id import OrcidId

# TODO update the JSON string below
json = "{}"
# create an instance of OrcidId from a JSON string
orcid_id_instance = OrcidId.from_json(json)
# print the JSON string representation of the object
print(OrcidId.to_json())

# convert the object into a dict
orcid_id_dict = orcid_id_instance.to_dict()
# create an instance of OrcidId from a dict
orcid_id_from_dict = OrcidId.from_dict(orcid_id_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


