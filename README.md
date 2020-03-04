# Azure Function App for traffic information collection

These Azure Functions are using a `TimerTrigger` which schedules Python scripts executions every 15 minutes. 

This Function App is split up into two functions. One is the `RandomRouteGenerator`, which generates a number of random route itineraries within a polygon definition of a city area to provide a sampling of the general traffic delay at a given time, and the other is the `TrafficTileGenerator`, which downloads the traffic tiles for a city to provide data on the intensity of traffic across areas of each city. The functions have separate `__init__.py` files but share common utilities for storage ([`blobutils.py`](Shared/blobutils.py)), which has shared methods for downloading and outputting to blob storage, and map queries ([`maputils.py`](Shared/maputils.py)), which aggregates methods for preparing and executing queries to get data from Azure Maps APIs.

A polygon string for each of the cities to query is required in the form of a polygons array JSON file stored in Blob storage, which the function app pulls in at runtime and uses to define the route & tile generation parameters.

## What it does

### RandomRouteGenerator function

This function first pulls in a `cities.json` file from blob storage to get the array of city polygon strings to process (A [sample](./sample_cities.json) of what this should look like is stored in this repository for reference). The blob URL for this is defined in config and once a cities file has been uploaded this should be amended to reflect where you've stored it. The function iterates over this array, and for each it uses regex to extract the coordinates from the polygon string, converts to a Shapely polygon object and uses the [Shapely library](https://pypi.org/project/Shapely/) to generate random coordinates within this polygon area by utilising rejection sampling.

> The number of coordinates to generate is determined by the specified number of routes desired per run * 2, which is set in configuration as the `NUM_OF_ROUTES_PER_CITY` value (see set up section of readme for more info).

For each pair of random coordinates the function then calls the Azure Maps `GET route directions` [API](https://docs.microsoft.com/en-us/rest/api/maps/route/getroutedirections) with the route parameters, and the result is stored as a (Gzipped) JSON file in an Azure Blob storage with the current DateTime as the folder paths and sequential numbers for filenames to prevent naming conflicts i.e. `randomroutes/cityId=1/year=2020/month=2/day=11/hour=11/minute=37/17179870486.json.gz`). Some of the collected fields in the `RouteDirectionSummary` are: 

| Name | Description |
| --- | --- |
| arrivalTime | Arrival Time property |
| departureTime | Departure Time property |
| lengthInMeters | Length In Meters property |
| trafficDelayInSeconds | Estimated delay in seconds caused by the real-time incident(s) according to traffic information. For routes planned with departure time in the future, delays is always 0. To return additional travel times using different types of traffic information, parameter computeTravelTimeFor=all needs to be added. |
| travelTimeInSeconds | Estimated travel time in seconds property that includes the delay due to real-time traffic. Note that even when traffic=false travelTimeInSeconds still includes the delay due to traffic. If DepartAt is in the future, travel time is calculated using time-dependent historic traffic data. |
| noTrafficTravelTimeInSeconds | Estimated travel time calculated as if there are no delays on the route due to traffic conditions (e.g. congestion). Included only if computeTravelTimeFor = all is used in the query.|
| historicTrafficTravelTimeInSeconds | Estimated travel time calculated using time-dependent historic traffic data. Included only if computeTravelTimeFor = all is used in the query. |
| liveTrafficIncidentsTravelTimeInSeconds | Estimated travel time calculated using real-time speed data. Included only if computeTravelTimeFor = all is used in the query. |

### RandomTileGenerator function

This function also iterates over the `cities.json` file to determine the areas of interest. For each city polygon, it:
- Calculates the MAX-X and MAX-Y values of the polygon along with the appropriate zoom level to capture the whole city area

- Uses the [`Get Traffic Flow Tile`](https://docs.microsoft.com/en-us/rest/api/maps/traffic/gettrafficflowtile) to download real-time traffic tiles for the area

- Saves these images to blob storage

## How to set up and deploy

To deploy the required infrastructure, a Terraform script can be found in the [Terraform](./terraform) folder. You can view more info on deploying via Terraform in their [docs](https://www.terraform.io/docs/index.html). Specify the required variables as described in the `variables.tf` file when running the terraform deployment commands. 

Once the infrastructure is deployed, you have several options on how you wish to deploy to Azure. Follow the Function App deployment processes outlined in the Azure Functions docs [here](https://docs.microsoft.com/en-us/azure/azure-functions/functions-continuous-deployment) for more info.

### Local debugging

- Create a `local.settings.json` file at the root (`__app__` directory) level with the below content and populate with the appropriate values:
```
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_MAPS_ENDPOINT": "https://atlas.microsoft.com/",
    "NUM_OF_ROUTES_PER_CITY": "100",
    "CITIES_CONFIG_URL": "https://{YOUR_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{YOUR_CONTAINER_NAME}/{FILE_NAME}.json",
    "TRAFFICTILES_OUTPUT_URL": "https://{YOUR_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{TRAFFIC_TILES_CONTAINER_NAME}",
    "TRAFFICROUTES_OUTPUT_URL": "https://{YOUR_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{TRAFFIC_ROUTES_CONTAINER_NAME}",
    "SCHEDULE": "0 */15 * * * *",
    "KEY_VAULT": "https://{YOUR_KEYVAULT_NAME}.vault.azure.net/",
    "AZURE_CLIENT_ID": "{YOUR_CLIENT_ID}",
    "AZURE_TENANT_ID": "{YOUR_TENANT_ID}"
  }
}
```

> The CRON trigger for each function is configured above in the App Settings in 'SCHEDULE', so if you wish to change the recurrence from every 15 minutes to a different schedule for a function, you will need to modify its value.

- Set up your environment to run Python and the Azure Functions tools by following [these instructions](https://docs.microsoft.com/en-us/azure/python/tutorial-vs-code-serverless-python-01)

- Set up authentication to be able to use Managed Service Identity locally (how our Azure Function talks to blob and keyvault without using keys directly). [Follow guidance here](https://docs.microsoft.com/en-us/azure/key-vault/service-to-service-authentication#local-development-authentication).

- Run `pip install -r requirements.txt` in the AzureFunction directory of the repo in your command line to install the required packages

- Run `func host start` to start debugging or use the [debugger in VS Code](https://docs.microsoft.com/en-us/azure/python/tutorial-vs-code-serverless-python-04)

## Monitoring the Functions

Once your Functions is deployed, you can access the Functions resource from the Azure Portal. Each deployed function has a monitoring feature based on Azure Application Insights. 

<img width="90%" src="../images/monitor_functions.jpg" alt="monitor_functions">

From there, you can explore the run's results. Click on one of them to get all the log's details.

Access `Run in Application Insights` to monitor the function further. From there, you can build queries to quickly retrieve, consolidate, and analyze collected logs. You can also save queries for use with visualizations or alert rules.

The queries are based on the [Kusto](https://docs.microsoft.com/en-us/azure/azure-monitor/log-query/log-query-overview) language. For instance, to get the 20 last level 3 exceptions:
```
exceptions
| where severityLevel == 3
| order by timestamp desc 
| take 20
```


### Stop the data collection
From the Azure Portal and the Azure CLI, you also have the possibility to pause the Functions when you want to stop the data collection. There are 2 options:
- **Disabling the Functions** to ignore the trigger for a specific function;
- **Stopping the Functions app** to stop all the functions;

Check how to disable a function in the [documentation](https://docs.microsoft.com/en-us/azure/azure-functions/disable-function).

Click [here](https://docs.microsoft.com/en-us/azure/python/tutorial-vs-code-serverless-python-01) for more information on Azure Functions in Python.
