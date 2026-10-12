# Tracker

`tracker_config` section of `ittup.json`.

ITTup uploads only to **ItaTorrents** (ITT): there is no tracker to choose and no multi-tracker list.

## The three ITT keys

| Key | What it is | Where to find it |
|---|---|---|
| `ITT_URL` | Tracker address | Already prefilled in the default file |
| `ITT_APIKEY` | Your personal API key | On the tracker: user profile → settings → API |
| `ITT_PID` | Your passkey (PID) | On the tracker: profile security page |

```json
"ITT_URL": "https://itatorrents.xyz",
"ITT_APIKEY": "your_api_key",
"ITT_PID": "your_passkey",
```

- **`ITT_APIKEY`** is used for every exchange with the tracker: uploads, searches, duplicate checks
- **`ITT_PID`** is used to build the torrent announce URL: without it the torrent you seed can't announce to the tracker

On startup the bot checks that the tracker responds:

```text
Tracker -> 'ITT' Online
```

!!! note "Leftovers from Unit3Dup"
    If your `ittup.json` was copied from Unit3Dup, it may still contain `SIS_*`, `PTT_*`, `AST_*` and `MULTI_TRACKER`: they are ignored, you can delete them.
