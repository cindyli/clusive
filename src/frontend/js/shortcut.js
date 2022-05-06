/* global clusiveTTS, contextLookup, contextTransform, d2reader, hotkeys, shortcut */

// Uses `hotkeys-js`
// Repo: https://github.com/jaywcjlove/hotkeys

(function($) {
    'use strict';

    var HOTKEY_SHORTCUTS = 'alt+k';
    var HOTKEY_TOC = 'alt+t';
    var HOTKEY_HIGHLIGHT = 'alt+h';
    var HOTKEY_SETTINGS_DISPLAY = 'alt+,';
    var HOTKEY_SETTINGS_READ = 'alt+.';
    var HOTKEY_TTS_TOGGLE = 'alt+a';
    var HOTKEY_TTS_PAUSE = 'space';
    var HOTKEY_SEARCH_FOCUS = 'alt+f';
    var HOTKEY_READER_FOCUS = 'alt+r';
    // var HOTKEY_PAGE_PREV = 'left';
    // var HOTKEY_PAGE_NEXT = 'right';
    var HOTKEY_SECTION_PREV = 'alt+pageup';
    var HOTKEY_SECTION_NEXT = 'alt+pagedown';
    var HOTKEY_LIBRARY = 'alt+l';
    var HOTKEY_CONTEXT_LOOKUP = 'alt+d';
    var HOTKEY_CONTEXT_TRANSFORM = 'alt+s';

    var SELECTOR_SHORTCUTS_BTN = '#shortcutsLocator';
    var SELECTOR_SHORTCUTS_DIALOG = '#shortcutsPop';

    var SELECTOR_READER_FRAME = '#frameReader';

    var SELECTOR_TOC_BTN = '#tocButton';
    var SELECTOR_TOC_MODAL = '#modalToc';
    var SELECTOR_TOC_TAB = '#tocTab';
    var SELECTOR_TOC_PANEL = '#tocPanel';
    var SELECTOR_HIGHLIGHT_TAB = '#notesTab';
    var SELECTOR_HIGHLIGHT_PANEL = '#notesPanel';

    var SELECTOR_SETTINGS_BTN = '#settingsButton';
    var SELECTOR_SETTINGS_MODAL = '#modalSettings';
    var SELECTOR_SETTINGS_DISPLAY_TAB = '[data-cfw-tab-target="#setting0"]';
    var SELECTOR_SETTINGS_DISPLAY_PANEL = '#setting0';
    var SELECTOR_SETTINGS_READ_TAB = '[data-cfw-tab-target="#setting1"]';
    var SELECTOR_SETTINGS_READ_PANEL = '#setting1';

    var SELECTOR_READ_ALOUD_REGIONS = '.sidebar-tts, .dialog-tts';

    var SELECTOR_GLOSSARY_DIALOG = '#glossaryPop';
    var SELECTOR_SIMPLIFY_DIALOG = '#simplifyPop';

    var shortcutModule = function() {
        this.readerDocument = null;
        this.readerFound = false;
        this.readerFrame = null;
        this.readerOwner = null;
    };

    shortcutModule.prototype = {
        attachReaderFrame : function() {
            var that = this;

            this.readerFrame = document.querySelector(SELECTOR_READER_FRAME);
            if (this.readerFrame !== null) {
                this.readerFound = true;
                // Pass keydown from reader frame to parent document
                this.readerOwner = this.readerFrame.ownerDocument;
                this.readerDocument = this.readerFrame.contentDocument;
                $(this.readerDocument)
                    .off('keydown.clusive.shortcut')
                    .on('keydown.clusive.shortcut', function(event) {
                        that.ownerDispatchEvent(event);
                    });
            }
        },

        process : function() {
            $(document.body).trigger('process.shortcut');
        },

        processAdd : function(callback) {
            var that = this;
            $(document.body)
                .off('process.shortcut')
                .one('process.shortcut', function() {
                    that._execute(callback);
                });
        },

        hasReader : function() {
            return this.readerFound;
        },

        ownerDispatchEvent : function(event) {
            var editable = false;

            // Filter out editable items
            // [contenteditable="true"], input, textarea, select - unless readonly
            var target = event.target;
            var tagName = target.tagName;
            if (target.isContentEditable || (tagName === 'INPUT' || tagName === 'TEXTAREA' || tagName === 'SELECT') && !target.readOnly) {
                editable = true;
            }

            if (!editable) {
                var eventProperties = {
                    bubbles : true,
                    cancelable : true,
                    key: event.key,
                    code: event.code,
                    location: event.location,
                    ctrlKey: event.ctrlKey,
                    shiftKey: event.shiftKey,
                    altKey: event.altKey,
                    metaKey: event.metaKey,
                    repeat: event.repeat,
                    isComposing: event.isComposing,
                    charCode: event.charCode,
                    keyCode: event.keyCode,
                    which: event.which,
                    getModifierState: event.getModifierState
                };

                this.triggerKeyboardEvent(this.readerOwner, 'keydown', eventProperties);
                // Force keyup to 'clear' the presses  in hotkeys-js.
                // Needed for Firefox due to frame document changing on reader resource change.
                // When document changes, keyup is not typically not dispatched before change
                // or after keyup handler is re-attached, causing loss of update to hotkey-js.
                this.triggerKeyboardEvent(this.readerOwner, 'keyup', eventProperties);
            }
        },

        triggerKeyboardEvent : function(element, eventName, extraData) {
            var e = new KeyboardEvent(eventName, extraData);
            element.dispatchEvent(e);
        },

        tabOpenFocus : function(tabBtn, tabPanel) {
            var panel = document.querySelector(tabPanel);
            if (panel.classList.contains('in')) {
                panel.focus();
                return;
            }
            $(tabBtn)
                .off('afterShow.cfw.tab.shortcut')
                .one('afterShow.cfw.tab.shortcut', function() {
                    panel.focus();
                })
                .CFW_Tab('show');
        },

        filterElementsForVisible : function(items) {
            var itemsArr = Array.from(items);
            var result = itemsArr.filter(function(element) {
                return $.CFW_isVisible(element);
            });
            return result;
        },

        getVisibleModal : function() {
            var items = document.querySelectorAll('.modal');
            var result = this.filterElementsForVisible(items);
            return $.CFW_getElement(result[0]);
        },

        modalCloseOther : function(selector, callback) {
            var that = this;
            var modalVis = this.getVisibleModal();
            if (modalVis && (!modalVis.matches(selector) || selector === null)) {
                $(modalVis)
                    .off('afterHide.cfw.modal.shortcut')
                    .one('afterHide.cfw.modal.shortcut', function() {
                        that._execute(callback);
                    })
                    .CFW_Modal('hide');
            }
            this._execute(callback);
        },

        modalOpen : function(modalBtn, modalDialog, callback) {
            var that = this;

            var modalOpenCallback = function() {
                var dialog = document.querySelector(modalDialog);
                if (dialog.classList.contains('in')) {
                    that._execute(callback);
                    return;
                }
                $(dialog)
                    .off('afterShow.cfw.modal.shortcut')
                    .one('afterShow.cfw.modal.shortcut', function() {
                        that._execute(callback);
                    });
                $(modalBtn).CFW_Modal('show');
            };

            this.modalCloseOther(modalDialog, modalOpenCallback);
        },

        popoverOpen : function(popoverBtn, popoverDialog, callback) {
            var that = this;

            var dialog = document.querySelector(popoverDialog);
            if (dialog.classList.contains('in')) {
                that._execute(callback);
                return;
            }
            $(popoverBtn)
                .off('afterShow.cfw.popover.shortcut')
                .one('afterShow.cfw.popover.shortcut', function() {
                    that._execute(callback);
                })
                .CFW_Popover('show');
        },

        updateTabIndex : function(element) {
            var tabindex = null;
            if (element.hasAttribute('tabindex')) {
                tabindex = element.getAttribute('tabindex');
            }
            if (tabindex === null) {
                element.setAttribute('tabindex', -1);
            }
        },

        getReaderBody : function() {
            var readerIframe = document.querySelector('#D2Reader-Container iframe');
            var readerDocument = readerIframe.contentDocument || readerIframe.contentWindow.document;
            return readerDocument.body;
        },

        focusReaderBody : function() {
            var that = this;
            var focusReaderCallback = function() {
                var readerBody = that.getReaderBody();
                that.updateTabIndex(readerBody);
                setTimeout(function() {
                    readerBody.focus();
                });
            };

            this.modalCloseOther(null, focusReaderCallback);
        },

        isSelection : function(selection) {
            if (selection === null) {
                return false;
            }
            return !(selection.type === 'None' || selection.type === 'Caret');
        },

        getClusiveSelection : function() {
            return window.getSelection();
        },

        hasClusiveSelection : function() {
            return this.isSelection(this.getClusiveSelection());
        },

        clearClusiveSelection : function() {
            window.getSelection().removeAllRanges();
        },

        getReaderSelection : function() {
            return this.readerDocument.getSelection();
        },

        hasReaderSelection : function() {
            return this.isSelection(this.getReaderSelection());
        },

        clearReaderSelection : function() {
            this.readerDocument.getSelection().removeAllRanges();
        },

        clearAllSelection : function() {
            this.clearClusiveSelection();
            this.clearReaderSelection();
        },

        addEvent : function(eventControl, eventValue) {
            window.clusiveEvents.addCaliperEventToQueue(
                window.clusiveEvents.caliperEventTypes.TOOL_USE_EVENT,
                eventControl,
                eventValue,
                window.clusiveEvents.caliperEventActions.USED
            );
        },

        _execute : function(callback) {
            if (typeof callback === 'function') {
                callback();
            }
        }
    };

    // Keyboard shortcuts popover
    hotkeys(HOTKEY_SHORTCUTS, function(event) {
        if (document.querySelector(SELECTOR_SHORTCUTS_BTN)) {
            event.preventDefault();
            shortcut.addEvent('hotkey-shortcuts-dialog', HOTKEY_SHORTCUTS);
            var callback = function() {
                document.querySelector(SELECTOR_SHORTCUTS_DIALOG).focus();
            };
            shortcut.popoverOpen(SELECTOR_SHORTCUTS_BTN, SELECTOR_SHORTCUTS_DIALOG, callback);
        }
    });

    // TOC list
    hotkeys(HOTKEY_TOC, function(event) {
        if (document.querySelector(SELECTOR_TOC_BTN)) {
            event.preventDefault();
            shortcut.addEvent('hotkey-toc-panel', HOTKEY_TOC);
            var callback = function() {
                shortcut.tabOpenFocus(SELECTOR_TOC_TAB, SELECTOR_TOC_PANEL);
            };
            shortcut.modalOpen(SELECTOR_TOC_BTN, SELECTOR_TOC_MODAL, callback);
        }
    });

    // Highlight list - or create highlight
    hotkeys(HOTKEY_HIGHLIGHT, function(event) {
        if (shortcut.readerFound && shortcut.hasReaderSelection()) {
            // Create highlight
            if (typeof d2reader === 'object') {
                event.preventDefault();
                shortcut.addEvent('hotkey-highlight-create', HOTKEY_HIGHLIGHT);
                d2reader.highlighter.doHighlight();
                shortcut.clearAllSelection();
                d2reader.highlighter.toolboxHide();
            }
        } else if (document.querySelector(SELECTOR_TOC_BTN)) {
            // Open highlight panel
            event.preventDefault();
            shortcut.addEvent('hotkey-highlight-panel', HOTKEY_HIGHLIGHT);
            var callback = function() {
                shortcut.tabOpenFocus(SELECTOR_HIGHLIGHT_TAB, SELECTOR_HIGHLIGHT_PANEL);
            };
            shortcut.modalOpen(SELECTOR_TOC_BTN, SELECTOR_TOC_MODAL, callback);
        }
    });

    // Settings - display panel
    hotkeys(HOTKEY_SETTINGS_DISPLAY, function(event) {
        if (document.querySelector(SELECTOR_SETTINGS_BTN)) {
            event.preventDefault();
            shortcut.addEvent('hotkey-settings-display', HOTKEY_SETTINGS_DISPLAY);
            var callback = function() {
                shortcut.tabOpenFocus(SELECTOR_SETTINGS_DISPLAY_TAB, SELECTOR_SETTINGS_DISPLAY_PANEL);
            };
            shortcut.modalOpen(SELECTOR_SETTINGS_BTN, SELECTOR_SETTINGS_MODAL, callback);
        }
    });

    // Settings - reading panel
    hotkeys(HOTKEY_SETTINGS_READ, function(event) {
        if (document.querySelector(SELECTOR_SETTINGS_BTN)) {
            event.preventDefault();
            shortcut.addEvent('hotkey-settings-read-aloud', HOTKEY_SETTINGS_READ);
            var callback = function() {
                shortcut.tabOpenFocus(SELECTOR_SETTINGS_READ_TAB, SELECTOR_SETTINGS_READ_PANEL);
            };
            shortcut.modalOpen(SELECTOR_SETTINGS_BTN, SELECTOR_SETTINGS_MODAL, callback);
        }
    });

    // Read-aloud - play/stop
    hotkeys(HOTKEY_TTS_TOGGLE, function(event) {
        // Check for selection within reader
        if (shortcut.readerFound && shortcut.hasReaderSelection()) {
            // Read only selected text
            if (typeof d2reader === 'object') {
                event.preventDefault();
                shortcut.addEvent('hotkey-tts-play-reader-selection', HOTKEY_TTS_TOGGLE);
                d2reader.highlighter.speak();
                shortcut.clearAllSelection();
                d2reader.highlighter.toolboxHide();
                return;
            }
        }

        var ttsRegions = document.querySelectorAll(SELECTOR_READ_ALOUD_REGIONS);
        var result = shortcut.filterElementsForVisible(ttsRegions);
        event.preventDefault();

        if (result.length) {
            // Default to 'global' play button
            var ttsBtn = document.querySelector('.sidebar-end .tts-play');
            if (!$.CFW_isVisible(ttsBtn)) {
                ttsBtn = null;
            }
            // Find current activeElement to determine location
            var activeElm = document.activeElement;
            // Check for parent dialog and find it's play button
            var dialog = activeElm.closest('.modal, .popover');
            if (dialog !== null) {
                ttsBtn = dialog.querySelector('.tts-play');
            }
            if (ttsBtn !== null) {
                shortcut.addEvent('hotkey-tts-toggle', HOTKEY_TTS_TOGGLE);
                clusiveTTS.toggle({
                    currentTarget: ttsBtn
                });
                return;
            }
        }

        shortcut.addEvent('hotkey-tts-stop', HOTKEY_TTS_TOGGLE);
        clusiveTTS.stop();
    });

    // Read-aloud - pause/resume
    hotkeys(HOTKEY_TTS_PAUSE, function(event) {
        var ttsRegions = document.querySelectorAll(SELECTOR_READ_ALOUD_REGIONS);
        var result = shortcut.filterElementsForVisible(ttsRegions);

        if (result.length && clusiveTTS.isReadingState) {
            event.preventDefault();
            if (clusiveTTS.isPausedState) {
                shortcut.addEvent('hotkey-tts-resume', HOTKEY_TTS_PAUSE);
                clusiveTTS.resume();
            } else {
                shortcut.addEvent('hotkey-tts-pause', HOTKEY_TTS_PAUSE);
                clusiveTTS.pause();
            }
        }
    });

    // Search - focus on search field
    // - currently only library and bookshare - not at same time
    hotkeys(HOTKEY_SEARCH_FOCUS, function(event) {
        var searchElm = document.querySelector('input[type="search"]');
        if (searchElm !== null) {
            event.preventDefault();
            shortcut.addEvent('hotkey-search-focus', HOTKEY_SEARCH_FOCUS);
            searchElm.focus();
        }
    });

    // Reader - focus content
    hotkeys(HOTKEY_READER_FOCUS, function(event) {
        if (shortcut.readerFound && typeof d2reader === 'object') {
            event.preventDefault();
            shortcut.addEvent('hotkey-reader-focus', HOTKEY_READER_FOCUS);
            shortcut.focusReaderBody();
        }
    });

    /*
    // Reader navigation - previous page
    hotkeys(HOTKEY_PAGE_PREV, function(event) {
        if (shortcut.readerFound && typeof d2reader === 'object') {
            event.preventDefault();
            shortcut.addEvent('hotkey-reader-navigation-pagination-previous', HOTKEY_PAGE_PREV);
            d2reader.previousPage();
        }
    });

    // Reader navigation - next page
    hotkeys(HOTKEY_PAGE_NEXT, function(event) {
        if (shortcut.readerFound && typeof d2reader === 'object') {
            event.preventDefault();
            shortcut.addEvent('hotkey-reader-navigation-pagination-next', HOTKEY_PAGE_NEXT);
            d2reader.nextPage();
        }
    });
    */

    // Reader navigation - previous section/resource
    hotkeys(HOTKEY_SECTION_PREV, function(event) {
        if (shortcut.readerFound && typeof d2reader === 'object') {
            event.preventDefault();
            shortcut.addEvent('hotkey-reader-navigation-section-previous', HOTKEY_SECTION_PREV);
            shortcut.processAdd(function() {
                shortcut.focusReaderBody();
            });
            d2reader.previousResource();
        }
    });

    // Reader navigation - next section/resource
    hotkeys(HOTKEY_SECTION_NEXT, function(event) {
        if (shortcut.readerFound && typeof d2reader === 'object') {
            event.preventDefault();
            shortcut.addEvent('hotkey-reader-navigation-section-next', HOTKEY_SECTION_NEXT);
            shortcut.processAdd(function() {
                shortcut.focusReaderBody();
            });
            d2reader.nextResource();
        }
    });

    // Library
    hotkeys(HOTKEY_LIBRARY, function(event) {
        event.preventDefault();
        shortcut.addEvent('hotkey-library', HOTKEY_LIBRARY);
        window.location.href = '/reader';
    });

    // Context menu - word lookup (definition)
    hotkeys(HOTKEY_CONTEXT_LOOKUP, function(event) {
        if (shortcut.readerFound) {
            if (shortcut.hasReaderSelection()) {
                // Do lookup
                event.preventDefault();
                shortcut.addEvent('hotkey-lookup', HOTKEY_CONTEXT_LOOKUP);
                contextLookup(shortcut.getReaderSelection().toString());
                shortcut.clearReaderSelection();
                if (typeof d2reader === 'object') {
                    d2reader.highlighter.toolboxHide();
                }
            } else if ($.CFW_isVisible(document.querySelector(SELECTOR_GLOSSARY_DIALOG))) {
                // Focus the glossary popover
                event.preventDefault();
                document.querySelector(SELECTOR_GLOSSARY_DIALOG).focus();
            }
        }
    });

    // Context menu - transform (simplifiy, translate, ...)
    hotkeys(HOTKEY_CONTEXT_TRANSFORM, function(event) {
        if (shortcut.readerFound) {
            if (shortcut.hasReaderSelection()) {
                // Do transform
                event.preventDefault();
                shortcut.addEvent('hotkey-transform', HOTKEY_CONTEXT_TRANSFORM);
                contextTransform(shortcut.getReaderSelection().toString());
                shortcut.clearReaderSelection();
                if (typeof d2reader === 'object') {
                    d2reader.highlighter.toolboxHide();
                }
            } else if ($.CFW_isVisible(document.querySelector(SELECTOR_SIMPLIFY_DIALOG))) {
                // Focus the simplify/transform popover
                event.preventDefault();
                document.querySelector(SELECTOR_SIMPLIFY_DIALOG).focus();
            }
        }
    });

    window.shortcut = shortcutModule.prototype;
}(jQuery));
