'use strict';

const browserActionWrapper = browser.action || browser.browserAction;
const browserAction = {};

browserAction.show = async function(tab, popupData) {
    popupData ??= page.popupData;
    page.popupData = popupData;

    browserActionWrapper.setIcon({
        path: await browserAction.generateIconName(popupData.iconType)
    });

    if (popupData.popup && tab?.id) {
        browserActionWrapper.setPopup({
            tabId: tab.id,
            popup: `popups/${popupData.popup}.html`
        });

        let badgeText = '';
        const currentTab = tabs.getTabFromId(tab.id);
        if (popupData.popup === 'popup_login') {
            badgeText = currentTab?.loginList.length;
        } else if (popupData.popup === 'popup_httpauth') {
            badgeText = currentTab?.basicAuthLogins?.loginList?.length;
        }

        browserAction.setBadgeText(tab?.id, badgeText);
    }
};

browserAction.showDefault = async function(tab) {
    const popupData = {
        iconType: 'normal',
        popup: 'popup'
    };

    const response = await keepass.isConfigured().catch((err) => {
        logError('Cannot show default popup: ' + err);
    });

    if (!response && !keepass.isKeePassXCAvailable) {
        popupData.iconType = 'cross';
    } else if (!keepass.isAssociated() && !keepass.isDatabaseClosed) {
        popupData.iconType = 'bang';
    } else if (keepass.isKeePassXCAvailable && keepass.isDatabaseClosed) {
        popupData.iconType = 'locked';
    }

    // Get the current tab if no tab given
    tab ??= await getCurrentTab();
    if (!tab) {
        return;
    }

    const currentTab = tabs.getTabFromId(tab?.id);
    if (currentTab?.loginList.length > 0) {
        popupData.iconType = 'normal';
        popupData.popup = 'popup_login';
        browserAction.setBadgeText(tab?.id, currentTab?.loginList.length);
    }

    await browserAction.show(tab, popupData);
};

browserAction.setBadgeText = function(tabId, badgeText) {
    if (!tabId) {
        return;
    }

    browserActionWrapper.setBadgeBackgroundColor({ color: '#666666' });
    browserActionWrapper.setBadgeText({ text: String(badgeText), tabId: tabId });
};

browserAction.generateIconName = async function(iconType) {
    let name = 'icon_';
    name += (await keepass.keePassXCUpdateAvailable()) ? 'new_' : '';
    name += (!iconType || iconType === 'normal') ? 'normal' : iconType;

    // The colour comes from Cipher rather than from this extension's options,
    // so the toolbar icon and the tray icon agree. 'colored' remains the
    // fallback for an installation that has never heard from the application.
    const iconColor = page?.settings?.iconColor;
    let style = ICON_COLORS.includes(iconColor) ? iconColor : 'colored';

    // Monochrome is the one choice this extension can serve better than the
    // tray can: a panel gets a fixed pixmap, but here the browser's own colour
    // scheme is readable, so the icon can follow it instead of committing to
    // one shade. useMonochromeToolbarIcon stays honoured as an override for
    // anyone who set it before the colour was Cipher's to choose.
    if (style === 'monochrome' || page?.settings?.useMonochromeToolbarIcon) {
        style = page?.settings?.colorTheme === 'system' || !page?.settings?.colorTheme
            ? await retrieveColorScheme()
            : page.settings.colorTheme;
    }
    const filetype = (page.isFirefox || page.isSafari) ? 'svg' : 'png';
    return `/icons/toolbar/${style}/${name}.${filetype}`;
};

browserAction.ignoreSite = async function(url) {
    await browser.windows.getCurrent();
    const tab = await getCurrentTab();

    // Send the message to the current tab's content script
    if (tab?.id) {
        browser.tabs.sendMessage(tab.id, {
            action: 'ignore_site',
            args: [ url ]
        });
    }
};
