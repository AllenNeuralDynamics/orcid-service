# Content

Response model for querying example content

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**info** | **str** | Example Info | 
**arg** | **str** | Argument passed into request | 

## Example

```python
from orcid_service_client.models.content import Content

# TODO update the JSON string below
json = "{}"
# create an instance of Content from a JSON string
content_instance = Content.from_json(json)
# print the JSON string representation of the object
print(Content.to_json())

# convert the object into a dict
content_dict = content_instance.to_dict()
# create an instance of Content from a dict
content_from_dict = Content.from_dict(content_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


