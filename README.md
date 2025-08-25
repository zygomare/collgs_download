# CollGS Download
A Python utility for downloading satellite imagery from the CollGS (Collaborative Ground Segment) catalog service. This tool enables searching for and downloading Sentinel data using configurable parameters.
## Features

* Search for satellite imagery using customizable parameters
* Download multiple image files in ZIP format
* Resume interrupted downloads
* Skip existing files
* Configure connection parameters
* JSON-based configuration


## Installation

```bash
# Clone the repository
git clone https://github.com/zygomare/collgs_download.git
cd collgs_download

# Install dependencies
pip install requests
```
## Usage

```bash
python collgs_download.py --config config.json
```
If no configuration file is provided, a sample configuration will be generated.

## Configuration

The configuration file is in JSON format and contains the following parameters:
```json
{
  "base_url": "https://collgs.lu/catalog/oseo/search",
  "parameters": {
    "parentIdentifier": "S2_MSIL1C",
    "box": "-73.43753408585016,45.73021716999517,-73.2071785066827,45.898202104983724",
    "timeStart": "2025-04-01T00:00:00.000Z",
    "timeEnd": "2025-08-26T00:00:00.000Z",
    "cloudCover": "[0,47]",
    "httpAccept": "json",
    "count": 50
  },
  "output_directory": "downloads",
  "connection": {
    "timeout": 120,
    "retries": 3,
    "user_agent": "eo-downloader/1.0"
  },
  "download_options": {
    "chunk_size": 65536,
    "skip_existing": true
  }
}
```
## Parameters

### Search Parameters
* parentIdentifier: Product collection ID  
    * S2_MSIL1C: Sentinel-2 Level-1C products
  * S2_MSIL2A: Sentinel-2 Level-2A products
  * S1_SAR_GRD: Sentinel-1 Ground Range Detected products
  * S1_SAR_SLC: Sentinel-1 Single Look Complex products
  * S3_OL_1_EFR: Sentinel-3 OLCI Level-1 Full Resolution products
  * S3_OL_2_LFR: Sentinel-3 OLCI Level-2 Land Full Resolution products
  * See CollGS documentation for the complete list: https://collgs.lu/support

* box: Geographic bounding box in format "west,south,east,north"  

* timeStart: Start date in ISO format  
* timeEnd: End date in ISO format  
* cloudCover: Cloud coverage filter range in format "[min,max]"  
* count: Maximum number of results to return  
* platform: Satellite platform  
  * Sentinel-1, Sentinel-2, Sentinel-3
* productType: Product type  
  * For S2: S2MSI1C, S2MSI2A
  * For S1: GRD, SLC
  * For S3: OL_1_EFR, OL_2_LFR
* orbitDirection: Direction of satellite orbit
  * ASCENDING, DESCENDING


### Connection Settings
* timeout: Connection timeout in seconds
* retries: Number of connection retry attempts
* user_agent: User agent string for requests


### Download Options
* chunk_size: Size of download chunks in bytes
* skip_existing: Whether to skip already downloaded files


## Example
1. Create a configuration file named config.json
2. Run the script:

```bash
python collgs_download.py --config config.json
```

## License
This project is licensed under the MIT License. See the LICENSE file for details.