// This is the Javascript file that is injected into all R2D2BC frames.

import hotkeys from 'script-loader!hotkeys-js/dist/hotkeys.js';

// Reference from within the iframe to the clusivePrefs global in the parent window
var clusivePrefs = window.parent.window.clusivePrefs;

// Reference from within the iframe to the clusiveEvents global in the parent window
var clusiveEvents = window.parent.window.clusiveEvents;

// Reference from within the iframe to the clusiveAssessment global

var clusiveAssessment = window.parent.window.clusiveAssessment;

if (!window.debug) {
    console.log = function () {};
}

$(function() {
    var $body = $('body');
    // $body.on('click touchstart keydown', 'span[data-gloss]', function(e) {
    //     if (e.type === 'keydown') {
    //         // Respond to Enter and Space keys, ignore anything else.
    //         if (e.which !== 13 && e.which !== 32) {
    //             return;
    //         }
    //     }
    //     e.preventDefault();
    //     e.stopPropagation();
    //     openGlossaryForCue($(this));
    // });
    window.parent.setUpImageDetails($body);
});


// // Additional actions when popover opens
// scope.on("beforeShow.cfw.popover", "a.gloss",
//     function () {
//         var word = $(this).data("word");
//         console.log("clicked: ", word);
//         // Hide other popovers
//         scope.find("a.gloss").CFW_Popover("hide");
//         // Show other matches
//         scope.mark(word, secondaryMarkOptions);
//     });
//
// // Additional actions when popover closes
// scope.on("afterHide.cfw.popover", "a.gloss",
//     function () {
//         console.log("Closed: ", $(this).data("word"));
//         scope.unmark({ element: "span" });
//     });

// TODO: make preferences editor properly aware of page changes
if(clusivePrefs && clusivePrefs.prefsEditorLoader && clusivePrefs.prefsEditorLoader.prefsEditor) {
    console.info('getting settings')
    var prefsPromise = clusivePrefs.prefsEditorLoader.getSettings();
    prefsPromise.then(function (prefs) {
        console.debug('prefs received', prefs)
    }, function (e) {
        console.error('error fetching prefs', e)
    })
}

function blockHotkeys(keyArray) {
    // Unbind all hotkeys
    window.hotkeys.unbind();
    // Block each hotkey - will propagate artificially through
    // keydown/keyup creation provided for in `shortcut.js`
    keyArray.forEach(function(item) {
        window.hotkeys(item.keys, function(event) {
            if (window.parent.shortcut.doBlockInternal(item.blocker)) {
                event.preventDefault();
                event.stopPropagation();
            }
        });
    });
}
// Keep webpack from removing the function
window.blockHotkeys = blockHotkeys;
