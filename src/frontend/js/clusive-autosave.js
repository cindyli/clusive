/* Code for comprehension and affect assessments */
/* global clusive, clusiveContext, PAGE_EVENT_ID, DJANGO_CSRF_TOKEN, fluid, D2Reader */
/* exported clusiveAutosave */

var clusiveAutosave = {
    queue: clusive.djangoMessageQueue({
            config: {                        
                localStorageKey: "clusive.messageQueue.autosave",
                lastQueueFlushInfoKey: "clusive.messageQueue.autosave.log.lastQueueFlushInfo"
            }
        }),
    save: function(url, data) {        
        var lastData = clusiveAutosave.lastDataCache[url];
        var isNewData = (lastData !== data);        
        console.log("comparison of data and lastData: ", data, lastData, isNewData);
        if(isNewData) {
            console.log("adding changed data to autosave queue");
            clusiveAutosave.queue.add({"type": "AS", "url": url, "data": JSON.stringify(data)});
            clusiveAutosave.lastDataCache[url] = data; 
        } else {
            console.log("data has not changed, not adding to autosave queue");
        }
    },
    retrieve: 
        function(url, callback) {
            var hasLocal = false;                
            var autosaveMessages = [].concat(clusiveAutosave.queue.getMessages()).filter(function (item) {                    
                    if(item.content.type === "AS" && item.content.url === url) {
                        return true;
                    }                    
            });
            
            if(autosaveMessages.length > 0) {                                        
                var latestLocalData = JSON.parse(autosaveMessages.pop().content.data);
                console.log("local data for url: " + url + " found", latestLocalData);
                callback(latestLocalData);
                clusiveAutosave.lastDataCache[url] = latestLocalData;
            } else {                   
                console.log("No local data for url: " + url + ", trying to get from server");
                $.get(url, function(data) {
                    console.log("Found data on server for url: " + url);
                    callback(data);                    
                    clusiveAutosave.lastDataCache[url] = data;
                }).fail(function(error) {
                    if (error.status === 404) {
                        console.debug('No matching data on server for url: ' + url);
                    } else {
                        console.warn('failed to get data: ', error.status);
                    }
                });
            }                 
        },
    // Maintains per-url record of data to avoid unneeded autosaving
    lastDataCache: {

    }
};