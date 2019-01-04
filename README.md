[![Version](https://img.shields.io/badge/version-0.0.4-green.svg?style=for-the-badge)](#) [![mantained](https://img.shields.io/maintenance/yes/2018.svg?style=for-the-badge)](#)

[![maintainer](https://img.shields.io/badge/maintainer-Ian%20Richardson%20%40iantrich-blue.svg?style=for-the-badge)](#)

## Support
Hey dude! Help me out for a couple of :beers: or a :coffee:!

[![coffee](https://www.buymeacoffee.com/assets/img/custom_images/black_img.png)](https://www.buymeacoffee.com/zJtVxUAgH)

# sensor.trakt
[Trakt](https://www.trakt.tv) component to feed [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card) with
Trakt's upcoming shows for [Home Assistant](https://www.home-assistant.io/)

## Installation:

1. Install this component by copying to your `/custom_components/sensor/` folder.
2. Install the card: [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card)
3. Add the code to your `configuration.yaml` using the config options below.
4. Add the code for the card to your `ui-lovelace.yaml`. 
5. **You will need to restart after installation for the component to start working.**

* If you're having issues, check out the [troubleshooting guide](https://github.com/custom-cards/upcoming-media-card/blob/master/troubleshooting.md) before posting an issue or asking for help on the forums.

**Example configuration.yaml:**

```yaml
sensor:
  platform: trakt
  id: 'sakdfjawioehrw3985728935uksdf'
  secret: 'sdfoiwahjeflkaswjefi83q7829045uoijksldf'
  username: iantrich
  days: 10
```

**Configuration variables:**

key | description
:--- | :---
**platform (Required)** | `trakt`
**id (Required)** | Client ID (create new app at https://trakt.tv/oauth/applications)
**secret (Required)** | Client Secret (create new app at https://trakt.tv/oauth/applications)
**username (Required)** | trakt.tv username
**days (Optional)** | How many days to look forward for movies/shows. Default `30`
**name (Optional)** | Sensor name. Default `Trakt Upcoming Calendar`

***

Due to how `custom_components` are loaded, it is normal to see a `ModuleNotFoundError` error on first boot after adding this, to resolve it, restart Home-Assistant.
