'use strict';

/**
 * Colour the in-field icons to match the colour chosen in Cipher.
 *
 * The icons live in closed shadow roots created by icon.js, out of reach of
 * any script but their own. Custom properties inherit across that boundary,
 * so the colour is applied by setting one property per icon on the document
 * root and letting css/cipher-icons.css pick it up inside each root.
 *
 * The colour arrives with the settings, which the background stores when
 * Cipher sends it (keepass.setIconColor), and is pushed here directly when it
 * changes while this page is open.
 */
const cipherIcons = {};

cipherIcons.FIELD_ICONS = [ 'unlock', 'totp', 'key' ];
cipherIcons.DARK_SCHEME = window.matchMedia('(prefers-color-scheme: dark)');
cipherIcons.color = undefined;

// The directory under icons/field to draw from. Monochrome follows the page's
// colour scheme the same way the toolbar follows the browser's: "dark" holds
// the light icon, for a dark page, as tools/generate-icons.py explains.
cipherIcons.theme = function(color) {
    if (color === 'monochrome') {
        return cipherIcons.DARK_SCHEME.matches ? 'dark' : 'light';
    }

    return ICON_COLORS.includes(color) ? color : 'colored';
};

cipherIcons.apply = function(color) {
    cipherIcons.color = color;

    const root = document.documentElement;
    if (!root?.style) {
        return;
    }

    const theme = cipherIcons.theme(color);
    for (const name of cipherIcons.FIELD_ICONS) {
        const url = browser.runtime.getURL(`icons/field/${theme}/${name}.svg`);
        root.style.setProperty(`--cipher-icon-${name}`, `url("${url}")`);
    }
};

cipherIcons.init = async function() {
    try {
        const settings = await sendMessage('load_settings');
        cipherIcons.apply(settings?.iconColor);
    } catch (err) {
        logError(`cipherIcons: cannot load settings: ${err}`);
    }

    cipherIcons.DARK_SCHEME.addEventListener('change', () => cipherIcons.apply(cipherIcons.color));

    browser.runtime.onMessage.addListener((req) => {
        if (req?.action === 'cipher_icon_color') {
            cipherIcons.apply(req.color);
        }
    });
};

cipherIcons.init();
