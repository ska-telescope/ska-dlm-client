# openapi_client_dlm.GatewayApi

All URIs are relative to *http://localhost:8080*

Method | HTTP request | Description
------------- | ------------- | -------------
[**auth_callback_auth_callback_get**](GatewayApi.md#auth_callback_auth_callback_get) | **GET** /auth_callback | Auth Callback
[**has_scope_scope_get**](GatewayApi.md#has_scope_scope_get) | **GET** /scope | Has Scope
[**heartbeat_heartbeat_get**](GatewayApi.md#heartbeat_heartbeat_get) | **GET** /heartbeat | Heartbeat
[**login_login_get**](GatewayApi.md#login_login_get) | **GET** /login | Login
[**token_token_get**](GatewayApi.md#token_token_get) | **GET** /token | Token


# **auth_callback_auth_callback_get**
> object auth_callback_auth_callback_get()

Auth Callback

Called when user gives authorisation. Swap a code for token

### Example


```python
import openapi_client_dlm
from openapi_client_dlm.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client_dlm.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with openapi_client_dlm.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client_dlm.GatewayApi(api_client)

    try:
        # Auth Callback
        api_response = api_instance.auth_callback_auth_callback_get()
        print("The response of GatewayApi->auth_callback_auth_callback_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GatewayApi->auth_callback_auth_callback_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **has_scope_scope_get**
> object has_scope_scope_get(token, permission)

Has Scope

Get UMA scopes

### Example


```python
import openapi_client_dlm
from openapi_client_dlm.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client_dlm.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with openapi_client_dlm.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client_dlm.GatewayApi(api_client)
    token = 'token_example' # str | 
    permission = 'permission_example' # str | 

    try:
        # Has Scope
        api_response = api_instance.has_scope_scope_get(token, permission)
        print("The response of GatewayApi->has_scope_scope_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GatewayApi->has_scope_scope_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **token** | **str**|  | 
 **permission** | **str**|  | 

### Return type

**object**

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

# **heartbeat_heartbeat_get**
> object heartbeat_heartbeat_get()

Heartbeat

Endpoint to check if Gateway is contactable

### Example


```python
import openapi_client_dlm
from openapi_client_dlm.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client_dlm.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with openapi_client_dlm.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client_dlm.GatewayApi(api_client)

    try:
        # Heartbeat
        api_response = api_instance.heartbeat_heartbeat_get()
        print("The response of GatewayApi->heartbeat_heartbeat_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GatewayApi->heartbeat_heartbeat_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **login_login_get**
> object login_login_get()

Login

Redirect to IDP for user authorisation

### Example


```python
import openapi_client_dlm
from openapi_client_dlm.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client_dlm.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with openapi_client_dlm.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client_dlm.GatewayApi(api_client)

    try:
        # Login
        api_response = api_instance.login_login_get()
        print("The response of GatewayApi->login_login_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GatewayApi->login_login_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **token_token_get**
> object token_token_get(username, password)

Token

Get OAUTH token based on username and password

### Example


```python
import openapi_client_dlm
from openapi_client_dlm.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost:8080
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client_dlm.Configuration(
    host = "http://localhost:8080"
)


# Enter a context with an instance of the API client
with openapi_client_dlm.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client_dlm.GatewayApi(api_client)
    username = 'username_example' # str | 
    password = 'password_example' # str | 

    try:
        # Token
        api_response = api_instance.token_token_get(username, password)
        print("The response of GatewayApi->token_token_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GatewayApi->token_token_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **username** | **str**|  | 
 **password** | **str**|  | 

### Return type

**object**

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

