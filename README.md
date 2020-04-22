# sensor.trakt
[Trakt](https://www.trakt.tv) component to feed [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card) with
Trakt's upcoming shows for [Home Assistant](https://www.home-assistant.io/)

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![custom_updater][customupdaterbadge]][customupdater]
[![License][license-shield]](LICENSE.md)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

## Installation:

1. Install this component by copying to your `/custom_components/trakt/` folder.
2. Add the code to your `configuration.yaml` using the config options below.
3. Restart
4. Add the Integration from the UI and setup your options

Note: The redirect_uri will be as follows:
  * With HA cloud configured: https://<cloud-remote-url>/auth/external/callback
  * Without HA cloud configured: http://<local-ip>:<port>/auth/external/callback or if base_url is used in HA -> https://<base-url>:<port>/auth/external/callback

**Example configuration.yaml:**

```yaml
trakt:
  client_id: <client_id>
  client_secret: <client_secret>
```

### Example ui-lovelace.yaml:

```yaml
type: custom:upcoming-media-card
entity: sensor.upcoming_calendar
title: Upcoming Movies
```

**Configuration variables:**

key | type | description
:--- | :--- | :---
**client_id (Required)** | string | Client ID (create new app at https://trakt.tv/oauth/applications - use device auth in redirect and uri urn:ietf:wg:oauth:2.0:oob)
**client_secret (Required)** | string | Client Secret (create new app at https://trakt.tv/oauth/applications - use device auth in redirect)
***

Due to how `custom_components` are loaded, it is normal to see a `ModuleNotFoundError` error on first boot after adding this, to resolve it, restart Home-Assistant.

[buymecoffee]: https://www.buymeacoffee.com/iantrich
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/custom-components/sensor.trakt.svg?style=for-the-badge
[commits]: https://github.com/custom-components/sensor.trakt/commits/master
[customupdater]: https://github.com/custom-components/custom_updater
[customupdaterbadge]: https://img.shields.io/badge/custom__updater-true-success.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/t/trakt-tv-component/111897
[license-shield]: https://img.shields.io/github/license/custom-components/sensor.trakt.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Ian%20Richardson%20%40iantrich-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/custom-components/sensor.trakt.svg?style=for-the-badge
[releases]: https://github.com/custom-components/sensor.trakt/releases
