'use strict';

const MIN_ICON_SIZE = 14;
const MAX_ICON_SIZE = 24;

// Basic icon class
class Icon {
    constructor(field, databaseState = DatabaseState.DISCONNECTED, segmented = false) {
        this.databaseState = databaseState;
        this.icon = null;
        this.inputField = null;
        this.rtl = kpxcUI.isRTL(field);
        this.segmented = segmented;

        try {
            this.observer = new IntersectionObserver((entries) => {
                kpxcIcons.updateFromIntersectionObserver(this, entries);
            });
        } catch (err) {
            logError(err);
        }
    }

    // Size the icon dynamically, but not greater than 24 or smaller than 14
    calculateIconSize(field) {
        return Math.max(Math.min(MAX_ICON_SIZE, field.offsetHeight - 4), MIN_ICON_SIZE);
    }

    // Creates a wrapper div that has the icon in Shadow DOM
    createWrapper(styleSheetFilename) {
        const styleSheet = createStylesheet(styleSheetFilename);
        // Cipher: the icon's colour follows the application's choice. The
        // override has to sit inside this shadow root to reach the icon; see
        // css/cipher-icons.css and content/cipher-icons.js.
        const cipherStyleSheet = createStylesheet('css/cipher-icons.css');
        const wrapper = document.createElement('div');
        wrapper.style.all = 'unset';
        wrapper.style.display = 'none';

        // Make sure the wrapper is positioned correctly without CSS styles affecting to it
        wrapper.style.position = 'absolute';
        wrapper.style.top = Pixels(0);
        wrapper.style.left = Pixels(0);

        // Waits for both stylesheets to load before displaying the element,
        // so the icon never flashes the fallback colour. A failed load counts
        // too: an icon in the wrong colour beats no icon at all.
        let pending = 2;
        const reveal = () => {
            if (--pending === 0) {
                wrapper.style.display = 'block';
            }
        };
        for (const sheet of [ styleSheet, cipherStyleSheet ]) {
            sheet.addEventListener('load', reveal);
            sheet.addEventListener('error', reveal);
        }

        this.shadowRoot = wrapper.attachShadow({ mode: 'closed' });
        this.shadowRoot.append(styleSheet);
        this.shadowRoot.append(cipherStyleSheet);
        this.shadowRoot.append(this.icon);
        document.body.append(wrapper);
        kpxcUI.observeWrapper(wrapper);
    }

    removeIcon() {
        this.shadowRoot.removeChild(this.icon);
        document.body.removeChild(this.shadowRoot.host);
    }

    switchIcon(state, uuid) {
        if (!this.icon) {
            return;
        }

        if (state === DatabaseState.UNLOCKED) {
            this.icon.style.filter = kpxc.credentials.length === 0 && !uuid ? 'saturate(0%)' : 'saturate(100%)';
        } else {
            this.icon.style.filter = 'saturate(0%)';
        }
    }
}
