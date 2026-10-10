# Requested Iconscout animations

`requests.json` records the exact assets selected by the user. The five supplied
video previews in `assets/animations/` are integrated in a separate signal strip
on Overview and Live. These files have `.mp4` names but WebM containers; the player
detects their actual type. They are supplied previews, not Lottie source JSON.
The static official logos remain in the customer metric cards.

Place downloaded `.lottie`, Lottie `.json`, `.zip`, `.mp4`, or `.webm` files here,
in the project root, or in `assets/animations/`, together with any
required image assets and the accompanying license/attribution information.
Suggested filenames: `jio`, `airtel`, `vi`, `bsnl`, and `china-telecom-signal`.
These assets have their own terms; the Unicons license does not cover them.

Overview and Live check these locations every three seconds. Complete supported
files appear automatically; incomplete downloads are retried. Lottie JSON and
archives take precedence over videos for the same provider. ZIP images are read
in memory without extracting files. Text should be exported as shapes.

Playback is local, respects reduced-motion preferences, pauses offscreen, and
runs outside the one-second data fragment. The player has its own pause button.
China Telecom is labeled as an illustration, not a fifth analytics provider.

The optional Lottie runtime in `player/` is Airbnb lottie-web 5.12.2 (light SVG
build), distributed under the bundled MIT license. Source:
https://github.com/airbnb/lottie-web/tree/v5.12.2
It is loaded only when a Lottie file is present; videos use native playback.
