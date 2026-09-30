# Cipher Bridge

Browser extension for [Cipher](https://github.com/steeb-k/cipher), a fork of
[KeePassXC-Browser](https://github.com/keepassxreboot/keepassxc-browser) that
talks to Cipher instead of KeePassXC over the same
[native messaging](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging)
protocol.

## Installing

Cipher Bridge is not yet on addons.mozilla.org or the Chrome Web Store.
Build the extension package from this checkout:

```
tools/package-xpi.py            # -> dist/cipher-bridge-<version>.xpi
```

Firefox ESR, Developer Edition and Nightly install an unsigned XPI once
`xpinstall.signatures.required` is set to `false` in `about:config`; release
Firefox refuses unsigned add-ons, and needs a build signed through
`tools/sign-xpi.sh`. Then open `about:addons`, choose *Install Add-on From
File* from the gear menu, and pick the XPI. For a single session,
`about:debugging` → *Load Temporary Add-on* works on any Firefox.

Chromium loads `keepassxc-browser/` unpacked from `chrome://extensions` with
developer mode on, after `tools/stage-manifest.py chromium`.

### Connecting to Cipher

The browser launches a small proxy that relays messages to Cipher's socket.
Cipher's repository ships it together with an installer for the native
messaging host manifest the browser needs:

```
tools/install-native-host.py --install            # Firefox
tools/install-native-host.py --browser chromium   # see the note it prints
```

Turn browser integration on in Cipher, then press *Connect* in the
extension's toolbar popup and name the association when Cipher asks.

## How it works

Cipher Bridge communicates with Cipher through `cipher-proxy`, which listens
on STDIN/STDOUT and forwards the messages over a Unix domain socket to the
running application. Cipher can be started and used normally; the extension
starts only the proxy, so there is no risk of shutting Cipher down or losing
unsaved changes.

## Requested permissions

| Name  | Reason |
| ----- | ----- |
| `activeTab`               | To get URL of the current tab |
| `contextMenus`            | To show context menu items |
| `cookies`                 | To access browser's internal Public Suffix List |
| `clipboardWrite`          | Allows password to be copied from password generator to clipboard |
| `nativeMessaging`         | Allows communication with the Cipher application |
| `notifications`           | To show browser notifications |
| `offscreen`               | For accessing system theme when setting icon colors (Chrome only) |
| `privacy`                 | For setting the extension as default password manager |
| `storage`                 | For storing extension settings (always stored locally in the browser, they are never synced) |
| `tabs`                    | To request tab URL's and other info |
| `webNavigation`           | To show browser notifications on install or update |
| `webRequest`              | For handling HTTP Basic Auth |
| `webRequestAuthProvider`  | For handling HTTP Basic Auth for Chromium based browsers |
| `webRequestBlocking`      | For handling HTTP Basic Auth |
| `http://*/*`              | To allow using Cipher Bridge on all websites |
| `https://*/*`             | To allow using Cipher Bridge on all websites |
| `https://api.github.com/` | Inherited from upstream's version check; unused by Cipher Bridge |

## Protocol

Check [keepassxc-protocol](keepassxc-protocol.md) for the details of the
messaging protocol, which Cipher implements as KeePassXC does. Cipher adds
one unsolicited signal, `icon-color`, so the toolbar icon can follow the
colour chosen in the application.

## Development

`tools/stage-manifest.py firefox` swaps in the Firefox manifest for loading
the tree unpacked; `--restore` puts the working one back. `npm run lint`
runs ESLint. `tools/generate-icons.py` regenerates every icon from the
artwork under `tools/artwork` and needs `rsvg-convert`.

## Contributing

Bug reports and feature requests go to the
[issue tracker](https://github.com/steeb-k/cipher-browser/issues). See
[CONTRIBUTING](.github/CONTRIBUTING.md) for how pull requests and
translations are handled.

## Origins

Cipher Bridge is a fork of
[KeePassXC-Browser](https://github.com/keepassxreboot/keepassxc-browser) by
the KeePassXC Team, and keeps its history and its contributors' credits.
Licensed under the GPL-3.0; see [LICENSE](LICENSE).
