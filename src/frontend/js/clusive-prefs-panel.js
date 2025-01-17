/* global cisl, fluid_3_0_0, DJANGO_STATIC_ROOT, clusiveTTS */

/*
    This code defines canonical representations of the various preference settings,
    how they are stored, and enactors for preferences that are not done through Readium.
 */

(function(fluid) {
    'use strict';

    // This removes the tableOfContents and
    // enhanceInputs preferences from the
    // default Infusion starter auxiliary schema
    fluid.defaults('cisl.prefs.auxSchema.starter', {
        gradeNames: ['fluid.prefs.auxSchema.starter'],
        mergePolicy: {
            'auxiliarySchema.tableOfContents': 'replace',
            'auxiliarySchema.enhanceInputs': 'replace'
        },
        auxiliarySchema: {
            tableOfContents: null,
            enhanceInputs: null,
            contrast: {
                classes: {
                    default: 'clusive-theme-default',
                    night: 'clusive-theme-night',
                    sepia: 'clusive-theme-sepia'
                },
                panel: null,
                alias: null
            },
            textFont: {
                panel: null,
                alias: null
            },
            textSize: {
                panel: null,
                alias: null
            },
            lineSpace: {
                panel: null,
                alias: null
            },
            glossary: {
                type: 'cisl.prefs.glossary',
                panel: null
            },
            animations: {
                type: 'cisl.prefs.animations',
                enactor: {
                    type: 'cisl.prefs.enactor.animations'
                },
                panel: null
            },
            scroll: {
                type: 'cisl.prefs.scroll',
                panel: null
            },
            readSpeed: {
                type: 'cisl.prefs.readSpeed',
                enactor: {
                    type: 'cisl.prefs.enactor.readSpeed'
                },
                panel: null
            },
            readVoices: {
                type: 'cisl.prefs.readVoices',
                panel: null
            },
            translationLanguage: {
                type: 'cisl.prefs.translation.language',
                panel: null
            }

        }
    });

    // Redefine the existing contrast schema used by the starter
    fluid.defaults('fluid.prefs.schemas.contrast', {
        gradeNames: ['fluid.prefs.schemas'],
        schema: {
            'fluid.prefs.contrast': {
                type: 'string',
                default: 'default',
                enum: ['default', 'night', 'sepia']
            }
        }
    });

    fluid.defaults('fluid.prefs.schemas.lineSpace', {
        gradeNames: ['fluid.prefs.schemas'],
        schema: {
            'fluid.prefs.lineSpace': {
                type: 'number',
                default: 1.6,
                minimum: 0.7,
                maximum: 2,
                multipleOf: 0.1
            }
        }
    });

    // Add a voice speed preference for TTS
    fluid.defaults('cisl.prefs.schemas.readSpeed', {
        gradeNames: ['fluid.prefs.schemas'],
        schema: {
            'cisl.prefs.readSpeed': {
                type: 'number',
                default: 1,
                mininum: 0.5,
                maximum: 2,
                multipleOf: 0.25

            }
        }
    });

    // Enactor for TTS voice speed
    fluid.defaults('cisl.prefs.enactor.readSpeed', {
        gradeNames: ['fluid.prefs.enactor'],
        preferenceMap: {
            'cisl.prefs.readSpeed': {
                'model.readSpeed': 'value'
            }
        },
        modelListeners: {
            readSpeed: {
                listener: '{that}.enactReadSpeed',
                args: ['{that}.model.readSpeed'],
                namespace: 'enactReadSpeed'
            }
        },
        invokers: {
            enactReadSpeed: {
                funcName: 'cisl.prefs.enactor.readSpeed.enactReadSpeed',
                args: '{arguments}.0'
            }
        }
    });

    cisl.prefs.enactor.readSpeed.enactReadSpeed = function(readSpeed) {
        console.debug('cisl.prefs.enactor.readSpeed.enactReadSpeed', readSpeed);
        clusiveTTS.updateSettings({
            rate: readSpeed
        });
    };

    // Add a preferred voices preference for TTS
    fluid.defaults('cisl.prefs.schemas.readVoices', {
        gradeNames: ['fluid.prefs.schemas'],
        schema: {
            'cisl.prefs.readVoices': {
                type: 'array',
                default: []
            }
        }
    });

    // Preference for paged vs. scrolled layout
    fluid.defaults('cisl.prefs.schemas.scroll', {
        gradeNames: ['fluid.prefs.schemas'],
        schema: {
            'cisl.prefs.scroll': {
                type: 'boolean',
                default: true
            }
        }
    });

    // Add a boolean preference for the glossary
    fluid.defaults('cisl.prefs.schemas.glossary', {
        gradeNames: ['fluid.prefs.schemas'],
        schema: {
            'cisl.prefs.glossary': {
                type: 'boolean',
                default: true
            }
        }
    });

    // Add a language preference for the translation functionality
    fluid.defaults('cisl.prefs.schemas.translation.language', {
        gradeNames: ['fluid.prefs.schemas'],
        schema: {
            'cisl.prefs.translation.language': {
                type: 'string',
                default: 'default'
            }
        }
    });

    // Add a boolean preference for reducing motion effects
    fluid.defaults('cisl.prefs.schemas.animations', {
        gradeNames: ['fluid.prefs.schemas'],
        schema: {
            'cisl.prefs.animations': {
                type: 'boolean',
                default: true
            }
        }
    });

    fluid.defaults('cisl.prefs.enactor.animations', {
        gradeNames: ['fluid.prefs.enactor.styleElements'],
        cssClass: 'clusive-reduced-motion',
        elementsToStyle: $('body'),     // must be a jquery instance
        preferenceMap: {
            'cisl.prefs.animations': {
                'model.value': 'value'
            }
        },
        invokers: {
            // Override to flip the use of applyStyle() and removeStyle()
            handleStyle: {
                funcName: "cisl.prefs.enactor.animations.handleStyle",
                args: ["{arguments}.0", "{that}.options.elementsToStyle", "{that}.options.cssClass", "{that}.applyStyle", "{that}.resetStyle"]
            }
        }
    });

    cisl.prefs.enactor.animations.handleStyle = function (value, elements, cssClass, applyStyleFunc, resetStyleFunc) {
        var func = value ? resetStyleFunc : applyStyleFunc;
        func(elements, cssClass);
    };

    fluid.defaults('cisl.prefs.composite.separatedPanel', {
        gradeNames: ['fluid.prefs.separatedPanel'],
        iframeRenderer: {
            markupProps: {
                src: DJANGO_STATIC_ROOT + 'shared/html/SeparatedPanelPrefsEditorFrame.html'
            }
        }
    });

    fluid.defaults('cisl.prefs.auxSchema.letterSpace', {
        gradeNames: ['fluid.prefs.auxSchema.letterSpace'],
        auxiliarySchema: {
            letterSpace: {
                panel: null
            }
        }
    });

    cisl.prefs.getSettings = function(that) {
        console.debug('calling CISL prefs Editor fetch impl');
        return that.getSettings();
    };

    // Fire a non-Infusion document event that non-Infusion
    // code can hook into to respond to preference changes
    cisl.prefs.dispatchPreferenceUpdateEvent = function() {
        var event = new Event('update.cisl.prefs');
        document.dispatchEvent(event);
    };

    // Reduced motion interactions
    cisl.prefs.userPrefersReducedMotion = function() {
        // Clusive setting - check class
        var setting = document.body.classList.contains('clusive-reduced-motion');
        // System preference - check CSS media query
        var system = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        return system || setting;
    };
}(fluid_3_0_0));
