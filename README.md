# sensor.trakt
[Trakt](https://www.trakt.tv) component to feed [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card) with
Trakt's upcoming shows for [Home Assistant](https://www.home-assistant.io/)

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE.md)

![Project Maintenance][maintenance-shield]
[![GitHub Activity][commits-shield]][commits]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

## Support
Hey dude! Help me out for a couple of :beers: or a :coffee:!

[![coffee](https://www.buymeacoffee.com/assets/img/custom_images/black_img.png)](https://www.buymeacoffee.com/zJtVxUAgH)

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
  exclude:
    'The Bachelor'
```

**Configuration variables:**

key | type | description
:--- | :--- | :---
**platform (Required)** | string | `trakt`
**id (Required)** | sring | Client ID (create new app at https://trakt.tv/oauth/applications)
**secret (Required)** | string | Client Secret (create new app at https://trakt.tv/oauth/applications)
**username (Required)** | string | trakt.tv username
**days (Optional)** | number | How many days to look forward for movies/shows. Default `30`
**name (Optional)** | string | Sensor name. Default `Trakt Upcoming Calendar`
**exclude (Optional)** | array | List of show titles to exclude as Trakt does not allow removal of shows from its service

***

Due to how `custom_components` are loaded, it is normal to see a `ModuleNotFoundError` error on first boot after adding this, to resolve it, restart Home-Assistant.

[commits-shield]: https://img.shields.io/github/commit-activity/y/custom-components/sensor.trakt.svg?style=for-the-badge
[commits]: https://github.com/custom-components/sensor.trakt/commits/master
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/478094546522079232.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/t/lovelace-upcoming-media-card/66562
[license-shield]: https://img.shields.io/github/license/custom-components/sensor.trakt.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Ian%20Richardson%20%40iantrich-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/custom-components/sensor.trakt.svg?style=for-the-badge
[releases]: https://github.com/custom-components/sensor.trakt/releases
