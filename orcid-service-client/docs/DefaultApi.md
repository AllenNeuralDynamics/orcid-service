# orcid_service_client.DefaultApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_content_example_arg_get**](DefaultApi.md#get_content_example_arg_get) | **GET** /{example_arg} | Get Content


# **get_content_example_arg_get**
> Content get_content_example_arg_get(example_arg)

Get Content

## Example content
Return either the raw content or the number of characters.

### Example


```python
import orcid_service_client
from orcid_service_client.models.content import Content
from orcid_service_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = orcid_service_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with orcid_service_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = orcid_service_client.DefaultApi(api_client)
    example_arg = 'example_arg_example' # str | 

    try:
        # Get Content
        api_response = api_instance.get_content_example_arg_get(example_arg)
        print("The response of DefaultApi->get_content_example_arg_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_content_example_arg_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **example_arg** | **str**|  | 

### Return type

[**Content**](Content.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

