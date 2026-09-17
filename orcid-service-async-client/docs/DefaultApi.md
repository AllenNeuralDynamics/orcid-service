# orcid_service_async_client.DefaultApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_orcid**](DefaultApi.md#get_orcid) | **GET** /orcid/{name} | Get Orcid


# **get_orcid**
> OrcidId get_orcid(name)

Get Orcid

## ORCID
Return an Allen Institute researcher's ORCID iD, or 404 when the
match is not definitive.

We require the full name to match the name on the record, ignoring
case, accents, and the order of the name parts, plus one of the
following must be true:

- ORCID lists an Allen institution or a public Allen email address on
  the record. We ask for this in the search itself rather than
  filtering afterwards, so the answer stays exact even for a name
  shared by hundreds of people.
- The record summary lists a verified Allen email domain. ORCID does
  not index that, so finding it takes a second search on the name
  alone followed by one request per candidate.

Those per-candidate requests are capped at MAX_DOMAIN_CHECKS, which
defaults to 10, so someone with a common name and no affiliation may
never reach that check. Setting the affiliation to an Allen
institution or a public Allen email address will guarantee a match on
the first search, which is preferred.

### Example


```python
import orcid_service_async_client
from orcid_service_async_client.models.orcid_id import OrcidId
from orcid_service_async_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = orcid_service_async_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
async with orcid_service_async_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = orcid_service_async_client.DefaultApi(api_client)
    name = 'name_example' # str | A researcher's given and family name.

    try:
        # Get Orcid
        api_response = await api_instance.get_orcid(name)
        print("The response of DefaultApi->get_orcid:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_orcid: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| A researcher&#39;s given and family name. | 

### Return type

[**OrcidId**](OrcidId.md)

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

