# sensor.trakt

[Trakt](https://www.trakt.tv) component to feed [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card) with
Trakt's upcoming shows for [Home Assistant](https://www.home-assistant.io/)

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![hacs_badge][hacsbadge]][hacs]
[![License][license-shield]](LICENSE.md)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

## Setup Trakt application on Trakt website

1. Create new app at https://trakt.tv/oauth/applications
2. Use the following redirect_uri:
   - With HA cloud configured: https://\<cloud-remote-url>/auth/external/callback
   - Without HA cloud configured: http://\<local-ip>:<port>/auth/external/callback
3. Save the application and then note down the `client_id` and `client_secret`

## Installation in Home Assistant:

1. Install this component by copying `custom_components/trakt` to your `config` folder (or install using `hacs`).
2. Restart Home Assistant
3. Add the Integration from the UI and setup your options

### Example ui-lovelace.yaml:

```yaml
type: custom:upcoming-media-card
entity: sensor.upcoming_calendar
title: Upcoming Movies
```

Due to how `custom_components` are loaded, it is normal to see a `ModuleNotFoundError` error on first boot after adding this, to resolve it, restart Home-Assistant.

[buymecoffee]: https://www.buymeacoffee.com/iantrich
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/custom-components/sensor.trakt.svg?style=for-the-badge
[commits]: https://github.com/custom-components/sensor.trakt/commits/master
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/t/trakt-tv-component/111897
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/custom-components/sensor.trakt.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Ian%20Richardson%20%40iantrich-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/custom-components/sensor.trakt.svg?style=for-the-badge
[releases]: https://github.com/custom-components/sensor.trakt/releases
