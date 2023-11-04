# iRacing integration for Home Assistant

## Installation

### Using HACS

Add this repository to HACS, then:  
HACS > Integrations > **Iracing**

### Manual install

Copy the `iracing` folder from latest release to the `custom_components` folder in your `config` folder.

## Configuration

Go to :  
Settings > Devices & Sevices > Integrations > Add Integration, and search for "Iracing"

You can add as many driver as you want.

For the first driver, you are required to enter:

* your iRacing login (email address)
* your iRacing password
* The _customer id_ of the driver to monitor

For the subsequent drivers, you are required to enter only the _customer id_.

## Note about iRacing credentials

The iRacing credentials are required to access the official iRacing API. Using this API is totally validated by iRacing, and it is safe to use your credentials for that.

Your credentials are only stored locally on your Home Assistant. They are not used for anything else than API authentication. In case of doubt, you can review the source code.

## Sensors

| Sensor | Description |
|--------|-------------|
| `sensor.DRIVER_NAME_driver` | Driver name + attributes which give the 5 last results |
| `sensor.DRIVER_NAME_CATEGORY_ir` | irating on the category |
| `sensor.DRIVER_NAME_CATEGORY_sr` | safety rating on the category |
| `sensor.DRIVER_NAME_CATEGORY_laps` | total laps completed in the career for the category |
| `sensor.DRIVER_NAME_CATEGORY_starts` | total race starts in the career for the category |
| `sensor.DRIVER_NAME_CATEGORY_wins` | total wins in the career for the category |
| `sensor.DRIVER_NAME_CATEGORY_top5` | total top 5 in the career for the category |

The `CATEGORY` can be: `road`, `dirt_road`, `oval`, `dirt_oval`