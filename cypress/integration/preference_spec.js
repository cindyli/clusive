var readerSelector = 'iframe[data-cy="reader-frame"]'

    var openPanel = function() {
        cy.get('a#djHideToolBarButton').click();                
        cy.get('span.icon-settings').first().click()   
    }

    var logIn = function(username, password) {
        cy.visit('http://localhost:8000')                
        cy.get('input#id_username').type(username)
        cy.get('input#id_password').type(password)
        cy.get('button').contains('Log in').click()        
    }
    
    var preferenceControls = {
        fontFamily: {            
            setAction: function (selector) {               
                cy.get('fieldset[data-cy="preference-fontFamily"]').find(selector).click({force: true})                
            },
            options: {
                default: 'input[value=default]',
                times: 'input[value=times]',
                comic: 'input[value=comic]',
                arial: 'input[value=arial]',
                verdana: 'input[value=verdana]',                
                openDyslexic: 'input[value=open-dyslexic]'
            }         
        },
        theme: {
            setAction: function (selector) {
                cy.get('fieldset[data-cy="preference-theme"]').find(selector).click({force: true})                                
            },
            options: {
                default: 'input[value=default]',
                night: 'input[value=night]',
                sepia: 'input[value=sepia]'
            }            
        }
    }

var setPref = function (pref, value) {
    var selector = preferenceControls[pref].options[value];
    preferenceControls[pref].setAction(selector);
}

    var preferenceExpects = {
        fontFamily: {
            reader: {
                prop: '--USER__fontFamily',
                values: {
                    default: 'Original',
                    times: 'Georgia, Times, Times New Roman, serif',                    
                    comic: 'Comic Sans MS, sans-serif',
                    arial: 'Arial, Helvetica',
                    verdana: 'Verdana',
                    openDyslexic: 'OpenDyslexicRegular'
                }
            },
            ui: {
                values: {
                    default: false,
                    times: 'fl-font-times',  
                    comic: 'fl-font-comic-sans',
                    arial: 'fl-font-arial',
                    verdana: 'fl-font-verdana',
                    openDyslexic: 'fl-font-open-dyslexic'
                }
            },    
        },
        theme: {
            reader: {
                prop: '--USER__appearance',
                values: {
                    default: 'readium-default-on',
                    night: 'clusive-night',
                    sepia: 'clusive-sepia'
                }
            },
            ui: {
                values: {
                    default: 'clusive-theme-default',
                    night: 'clusive-theme-night',
                    sepia: 'clusive-theme-sepia'
                }
            }
        },        
    }

    var checkClusiveUIPreferenceClass = function(pref, expectedValueKey) {        
        var expectedValue = preferenceExpects[pref].ui.values[expectedValueKey]
        if(expectedValue) {
            cy.get('body').should('have.class', preferenceExpects[pref].ui.values[expectedValueKey])   
        }
    }

    var checkReaderPreferenceProp = function(pref, expectedValueKey) {
        cy.iframe(readerSelector).should('have.css', preferenceExpects[pref].reader.prop, preferenceExpects[pref].reader.values[expectedValueKey])        
    }

    var checkPref = function(pref, expectedValue) {
        checkClusiveUIPreferenceClass(pref, expectedValue);
        checkReaderPreferenceProp(pref, expectedValue);
    }


// Relies on user accounts created by `python manage.py createrostersamples`

describe('While logged in as user samstudent', () => {    
    
    // Logs in as the samstudent user
    before(() => {
        logIn('samstudent', 'samstudent_pass')
    })

    // Preserve the session cookie so we don't have to log in multiple times, 
    // and the local storage for the message queue
    beforeEach(() => {        
        Cypress.Cookies.preserveOnce('sessionid', 'csrftoken')
        cy.restoreLocalStorage();
      })

    afterEach(() => {
        cy.saveLocalStorage();
    })

    // Clear the cookies and local storage at the end of the whole test suite
    after(() => {
        cy.clearCookies()
        cy.clearLocalStorage()
    })

    it('Visits the Clues to Clusive article, and sets the font to comic sans and the theme to dark', () => {   
        cy.visit('http://localhost:8000/reader/6/2')                                
        
        cy.frameLoaded(readerSelector)
        
        cy.iframe(readerSelector).contains('Clusive is a learning environment')

        openPanel();
        
        setPref('fontFamily', 'comic')        
        setPref('theme', 'night')

        checkPref('fontFamily', 'comic')
        checkPref('theme', 'night')        
    })              

    it('Reloads the page; the font is still set to comic sans, the page theme is still dark', () => {
        cy.reload()
        cy.frameLoaded(readerSelector)
        checkPref('fontFamily', 'comic')
        checkPref('theme', 'night')
    })

    it('Changes theme to sepia', () => {
        setPref('theme', 'sepia')
        checkPref('theme', 'sepia')
    })        

    it('Changes theme to default', () => {
        setPref('theme', 'default')
        checkPref('theme', 'default')
    })     


    it('Changes font to Times', () => {
        setPref('fontFamily', 'times')
        checkPref('fontFamily', 'times')
    })

    it('Changes font to Arial', () => {
        setPref('fontFamily', 'arial')
        checkPref('fontFamily', 'arial')
    })

    it('Changes font to Verdana', () => {
        setPref('fontFamily', 'verdana')
        checkPref('fontFamily', 'verdana')
    })

    it('Changes font to Open Dyslexic', () => {
        setPref('fontFamily', 'openDyslexic')
        checkPref('fontFamily', 'openDyslexic')
    })

    it('Resets the display settings', () => {
        cy.get('button.cislc-modalSettings-reset-display').click({force: true})
        cy.wait(2000)
        checkPref('theme', 'default')        
        checkPref('fontFamily', 'default')        
    })

  })
  