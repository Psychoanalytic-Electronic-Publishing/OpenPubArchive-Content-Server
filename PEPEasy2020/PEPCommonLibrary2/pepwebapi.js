// Neil R. Shapiro
// PEP-Web API Support library
// Last update: 2017-11-20
// Some calls assume a Knockout.js (KO) based interface; parameters marked as Observables (per knockout)
// allow the caller to show a status message changed when the asynchronous data is returned.
// 2017-05-12 Made changes to support IE - no defaults for parameters, no iterating objects, have to use loops.

/**
 * @module PEPCommonLibrary - convenience library for PEP-Web API
 * @fileOverview PEPCommonLibrary, a convenience library to make it easier to use the PEP-Web API
 * @author <a href="mailto:neil@mypep.info">Neil R. Shapiro</a>
 * @version 2.1.2017.11.04
 */

/*global window*/
/*global document*/
/*global console*/
/*global location*/
/*global XMLHttpRequest*/
/*global $*/
/*global alert*/
/*global Blob*/
/*exported threePlayScript*/
/*exported getCookie*/
/*exported checkLoginStatus*/
/*exported getSearchAnalysis*/
/*exported loginToServer*/
/*exported logoutFromServer*/
/*exported setFontSize*/
/*exported clearInterval*/
/*exported decodeHtml*/
/*exported setInterval*/
/*exported setCookie*/
/*exported deleteCookie*/
/*exported getListOfcurrAuthorIndexData*/
/*exported getDocumentDownload*/
/*exported getDocumentData*/
/*exported getAbstractNew*/
/*exported getAbstract*/
/*exported fixedEncodeURIComponent*/
/*exported setGlossaryStyle*/
/*exported setJustifyStyle*/
/*exported bookPEPCodesSearchSpec*/
/*exported videoPEPCodesSearchSpec*/
/*exported bookPEPCodesSearchSpec*/
/*exported journalPEPCodeSearchSpec*/

/* eslint-env browser */


var loggedInToServer;
var baseURL; // keep track of baseURL
var fSize = "1.5";
var videoPEPCodesSearchSpec = "afcvs+or+bpsivs+or+ijpvs+or+ipsavs+or+nypsivs+or+pcvs+or+pepgrantvs+or+peptopauthvs+or+pepvs+or+sfcpvs+or+spivs+or+uclvs";
var bookPEPCodesSearchSpec = "gw+or+ipl+or+nlp+or+se+or+zbk";
// note journals here, unlike PEP-Web EXCLUDES videostreams
var journalPEPCodeSearchSpec = "anijp-el+or+adpsa+or+aim+or+ajp+or+anijp-it+or+anijp-fr+or+aop+or+ajrpp+or+bjp+or+bap+or+bafc+or+bip+or+cjp+or+anijp-chi+or+cps+or+cfp+or+dr+or+fd+or+fa+or+gap+or+imago+or+ifp+or+ijaps+or+ijp+or+ijpopen+or+ijp-es+or+ijpsp+or+irp+or+anijp-de+or+izpa+or+anrp+or+jbp+or+jppf+or+joap+or+aps+or+jcptx+or+jcp+or+jicap+or+jaa+or+apa+or+mpsa+or+np+or+opus+or+psp+or+psu+or+psyche+or+pcs+or+pct+or+pah+or+ijpsppsc+or+pd+or+pi+or+ppersp+or+ppsy+or+pptx+or+paq+or+psar+or+psw+or+psc+or+psabew+or+pdpsy+or+apm+or+revapa+or+rbp+or+rpp-cs+or+rrp+or+rpsa+or+rip+or+spr+or+sgs+or+tvpa+or+anijp-tr+or+zpsap+or+zbpa";

String.prototype.format = function () {
    var i = 0,
        args = arguments;
    return this.replace(/{}/g, function () {
        return typeof args[i] != 'undefined' ? args[i++] : '';
    });
};

/**
 * Detect and return internet Explorer version
 *
 * @returns {integer} Microsoft Internet Explorer version
*/
function msieversion() {
    var ua = window.navigator.userAgent;
    var msie = ua.indexOf("MSIE ");
    var retVal = false; // 0 if not ie, otherwise version

    if (msie > 0) // If Internet Explorer, return version number
    {
        return parseInt(ua.substring(msie + 5, ua.indexOf(".", msie)));
    }

    var trident = ua.indexOf('Trident/');
    if (trident > 0) {
        // IE 11 => return version number
        var rv = ua.indexOf('rv:');
        return parseInt(ua.substring(rv + 3, ua.indexOf('.', rv)), 10);
    }

    var edge = ua.indexOf('Edge/');
    if (edge > 0) {
        // Edge (IE 12+) => return version number
        return parseInt(ua.substring(edge + 5, ua.indexOf('.', edge)), 10);
    }

    return retVal;
}

/**
 * VERY Unfinished function to insert working 3play script
 * Not done! Not tested either.
 *
 * @returns {string} Returns the mainDiv html of the inserted section
*/
function threePlayScript(fileID, insertLocSelector) {
    //<script type="text/javascript" src="//static.3playmedia.com/p/projects/11714/files/0mu1eiktak/plugins/10627.js?usevideoid=1"></script>
    var p3_api_key = "";
    var p3_window_wait = true;
    var mainDiv = document.createElement('<div></div>');
    var newDiv = document.createElement('<div id="transcript_p10627_721874"></div>');
    mainDiv.appendChild(newDiv);
    // document.writeln('<div id="transcript_p10627_721874"></div>');
    if (typeof p3_instances == "undefined") p3_instances = {};
    if (fileID === undefined) {
        var fileID = '0mu1eiktak';
    }
    if (!p3_instances["wistia_embed_id"]) {
        p3_instances["wistia_embed_id"] = {
            file_id: fileID, //"0mu1eiktak",
            player_type: "wistia_iframe",
            api_version: "simple",
            project_id: "11714",
            platform_integration: true
        }
    }
    p3_instances["wistia_embed_id"]["transcript"] = {
        target: "transcript_p10627_721874",
        skin: "ice",
        template: "default",
        height: "360",
        width: "350"
    }
    if (typeof p3_is_loading == "undefined" || (!p3_is_loading)) {
        p3_is_loading = true;
        // document.writeln('<div id="p3-js-main-root"></div>');
        var newDiv2 = document.createElement('<div id="p3-js-main-root"></div>');
        var e = document.createElement('script');
        e.async = true;
        e.src = "//p3.3playmedia.com/p3.js";
        newDiv2.appendChild(e);
    }
    mainDiv.appendChild(newDiv2);
    $(insertLocSelector).replaceWith(mainDiv);
    return mainDiv;
}

/**
 * Walk through ajax return status codes and set up return messages
 *
 * @returns {object} Compound of messageID and description, where messageID is a short text string suitable for translation.
 * e.g., {messageID:"authError", description:"Authentication error or timeout.  Please try to load the article again"};
*/

function ajaxCallErrorMessages(oReq, loggedInToServer, exception) {
  //console.error(oReq.response.error + " " + oReq.response.error_description);
  var statusMessageObj;
  var reqStatus = oReq.status;
  if (reqStatus === 400) {
    if (loggedInToServer === false) {
      statusMessageObj = {messageID:"ajaxAuthError", description:"Authentication error or timeout.  Please try to load the article again"};
    } else {
      statusMessageObj = {messageID:"ajaxAuthErrorLogin", description:"Authentication error or timeout.  Please login again"};
    }
  } else if (reqStatus === 404) { // pageNotFound
      statusMessageObj = {messageID:"ajaxError404", description:"Requested page not found."};
  } else if (reqStatus === 500) { // internalServerError
      statusMessageObj = {messageID:"ajaxError500", description:"Internal Server Error [500]."};
  } else if (exception === 'parsererror') { // data return error JSONParseFailed
      statusMessageObj = {messageID:"ajaxParserError", description:"Server data parse failed"};
  } else if (exception === 'timeout') {
      statusMessageObj = {messageID:"ajaxTimeout", description:"Server Timeout error."};
  } else if (exception === 'abort') {
      statusMessageObj = {messageID:"ajaxAbort", description:"Server request aborted."};
  } else {
      var errText;
      if (oReq.responseType === '') {
        errText = 'Uncaught Error: ' + oReq.responseText
      } else {
        errText = 'Uncaught Error: ' + reqStatus
      }
      console.error(errText);
      statusMessageObj = {messageID:"ajaxUncaught", description:errText};
  }

return statusMessageObj;
}

/**
 *  Encodes a Uniform Resource Identifier (URI) component by replacing each instance of certain characters by one, two, three, or four escape sequences representing the UTF-8 encoding of the character (will only be four escape sequences for characters composed of two "surrogate" characters).
 *
 * @param {string} str String to encode
 * @returns {void}
*
*/

function fixedEncodeURIComponent(str) {
    return encodeURIComponent(str).replace(/[!'()*]/g, function (c) {
        return '%' + c.charCodeAt(0).toString(16);
    });
}

/**
 * Change whether glossary items should show (css class glossaryHighlight)
 * Stores state in a cookie.  If parameter is excluded, defaults to true.
 *
 * @param {boolean} onOffSwitch Set highlight glossary items on (true) or off (false)
 * @returns {boolean} Selected state of glossary highlight, or the default (true)
*/
function setGlossaryStyle(onOffSwitch) {
    var retVal = onOffSwitch;
    var defaultVal = true;
    if (onOffSwitch === true) {
        $('body').addClass('glossaryHighlight');
        setCookie("showGlossaryTerms", true, 1);
    } else if (onOffSwitch === false) {
        $('body').removeClass('glossaryHighlight');
        setCookie("showGlossaryTerms", false, 1);
    } else { //e.g., "cookie"
        retVal = getCookie("showGlossaryTerms");
        if (retVal === "true") {
            retVal = setGlossaryStyle(true);
        } else if (retVal === "false") {
            // self.showGlossaryTerms(terms);
            retVal = setGlossaryStyle(false);
        } else {
            setGlossaryStyle(defaultVal);
            retVal = defaultVal;
        }
    }
    return retVal;
}

/**
 * Change whether the text should be justified (css class justifyText)
 * Stores state in a cookie.  If parameter is excluded, defaults to true.
 *
 * @param {boolean} onOffSwitch Set justify on (true) or off (false)
 * @returns {boolean} Selected state of justify, or the default (true)
*/
function setJustifyStyle(onOffSwitch) {
    var retVal = onOffSwitch;
    var defaultVal = true;
    if (onOffSwitch === true) {
        $('body').addClass('justify');
        setCookie("justifyText", true, 1);
    } else if (onOffSwitch === false) {
        $('body').removeClass('justify');
        setCookie("justifyText", false, 1);
    } else {
        retVal = getCookie("justifyText");
        if (retVal === "true") {
            retVal = setJustifyStyle(true);
        } else if (retVal === "false") {
            // self.showGlossaryTerms(terms);
            retVal = setJustifyStyle(false);
        } else {
            retVal = setJustifyStyle(defaultVal);
        }
    }
    return retVal;
}

/**
 * This callback is used by the checkLoginStatus function.
 *    e.g., loginStatusCallback(loggedInToServer, statusMessage);
 * @callback loginStatusCallback
 * @param {integer} loggedInToServer calls with integer equivalent to true, false, or the error value (>100)
 * @param {string} statusMessage Current status of login in text form
 *
 * @todo May be a good idea to make three parameters, and separate loggedIn state as true false from an error value.
*/

/**
 * Check whether or not the user is logged in.
 *
 * @param {string} baseURL base of url, version and rest of api call added in function
 * @param {string} accessToken Server supplied token from Token API call.  Keeps track of session.
 * @param {loginStatusCallback} loginStatusCallback Function to interpret login status results from server
 * @returns {boolean} Returns true if accessToken was supplied.  Not really meaningful.  You need to judge login status via the callback
*/
function checkLoginStatus(baseURL, accessToken, loginStatusCallback) {
    var apiCall = baseURL + "/v1/License/Status/Login";
    var oReq = new XMLHttpRequest();
    oReq.open("GET", apiCall, true);
    oReq.withCredentials = true;
    oReq.responseType = "json";
    var statusMessage = null;

    // since IE doesn't support defaults for paramaters, have to do it this way.
    if (typeof accessToken === 'undefined') {
        accessToken = "";
    }

    if (typeof loginStatusCallback === 'undefined') {
        loginStatusCallback = null;
    }

    // oReq.setRequestHeader('Content-Type', 'application/epub+zip');
    // don't get it if the token isn't set
    if (1) {
        if (accessToken !== "" && accessToken !== "IPLogin") {
          oReq.setRequestHeader('Authorization', 'Bearer ' + accessToken);
        }

        //console.log("Check Login Request with accessToken: " + accessToken);
        oReq.onload = function (oEvent, exception) {
            if (oReq.status !== 200) {
                if (oReq.status === 400) {
                    statusMessage = "Authentication error or timeout.  Please try again";
                } else if (oReq.status === 404) {
                    statusMessage  = 'Requested page not found. [404]';
                } else if (oReq.status === 500) {
                    statusMessage = 'Internal Server Error [500].';
                } else if (exception === 'parsererror') {
                    statusMessage = 'Requested JSON parse failed.';
                } else if (exception === 'timeout') {
                    statusMessage = 'Time out error.';
                } else if (exception === 'abort') {
                    statusMessage = 'Ajax request aborted.';
                } else {
                    statusMessage = oReq.response.error + " " + oReq.response.error_description;
                }
                if (loginStatusCallback !== null) {
                    loginStatusCallback(oReq.status, statusMessage);
                }
            } else { //success
                var browserVer = msieversion();
                var data;
                if (browserVer === false) {
                    data = oReq.response; // NOT IE.  Others don't seem to need the parse here.
                } else if (browserVer >= 12) {
                    // browser is Edge
                    data = oReq.response; // NOT IE.  Others don't seem to need the parse here.
                } else {
                    data = JSON.parse(oReq.response); // for IE.  Others don't seem to need the parse here.
                }

                try {
                    loggedInToServer = data.licenseInfo.responseInfo.loggedIn;
                } catch (err) {
                    alert("Error: " + err);
                }

                if (loggedInToServer) {
                    statusMessage = "PEPWebAPI: You are currently logged in.";
                } else {
                    statusMessage = "PEPWebAPI: You are not logged in";
                }

                if (loginStatusCallback !== null) {
                    loginStatusCallback(loggedInToServer, statusMessage);
                }
            }
        };
        // send it, response comes in the onload event.
        oReq.send();
    } else {
        loggedInToServer = false;
        statusMessage = "PEPWebAPI: You are not logged in";
        //console.log(statusMessage);
        if (loginStatusCallback !== null) {
            loginStatusCallback(loggedInToServer, statusMessage);
        }
    }

    // this is really not going to be accurate.  Need to use callback value
    return loggedInToServer;

}

/**
 * This callback is used by the loginToServer function.
 *    e.g., loginToServerCallback (status, statusMessage, statusCode, accessToken)
 * @callback loginToServerCallback
 * @param {boolean} status true if logged in
 * @param {string} statusMessage Current status of login in text form
 * @param {integer} statusCode Ajax status code of server request
 * @param {string} accessToken Token used to verify permissions and track session
 *
*/

/**
 * Check whether or not the user is logged in.
 *
 * @param {string} baseURL base of url, version and rest of api call added in function
 * @param {string} username the registered username of an account
 * @param {string} password corresponding password for the registered username of an account
 * @param {boolean} keepAlive Keep the connection alive (this may limit the number of users on a shared account that can connect)
 * @param {loginToServerCallback} loginToServerCallback Function to interpret login status results from server
 * @returns {void}
*/
//=============================================================================
function loginToServer(baseURL, username, password, loginToServerCallback, keepAlive) {
  var keepAliveAddOn = "";
  if (keepAlive === true) {
    keepAliveAddOn = "&ka=true";
  }

  var apiCall = baseURL + "/v1/Token?grant_type=password&username=" + username + "&password=" + password + keepAliveAddOn;

  if (typeof loginToServerCallback === 'undefined' || loginToServerCallback === null) {
      loginToServerCallback = null;
  }

  // jquery global option set to true
  $.ajaxSetup({
              xhrFields: {
                withCredentials: true
              }
  });

  $.ajax({
    dataType: "json",
    url: apiCall,
    success: function (data) {
      //accessTokenObserv("" + data.access_token);
      //tokenType = data.token_type;
      setCookie("PHPSESSID", data.access_token, 200);
      loggedInToServer = true;
      if (loginToServerCallback === null) {
          console.log("Logged in!");
      } else {
          loginToServerCallback(true, "Logged in!", 200, data.access_token);
      }
    },
    error: function (jqXHR, exception) {
      var msg = '';
      if (jqXHR.status === 0) {
          msg = 'Not connected.\n Verify Network.';
      } else if (jqXHR.status == 404) {
          msg = 'Requested page not found. [404]';
      } else if (jqXHR.status == 500) {
          msg = 'Internal Server Error [500].';
      } else if (exception === 'parsererror') {
          msg = 'Requested JSON parse failed.';
      } else if (exception === 'timeout') {
          msg = 'Time out error.';
      } else if (exception === 'abort') {
          msg = 'Ajax request aborted.';
      } else {
          msg = 'Uncaught Error.\n' + jqXHR.responseText;
      }
      loggedInToServer = false;

      if (loginToServerCallback === null) {
          alert("Login failed.  Please check your username and password and try again.");
          console.log(msg);
      } else {
          loginToServerCallback(false, JSON.parse(jqXHR.responseText), jqXHR.status, null);
      }
    }
  });
}

/**
 * This callback is used by the loginToServer function.
 *    e.g., loginToServerCallback (status, statusMessage, statusCode, accessToken)
 * @callback logoutFromServerCallback
 * @param {boolean} status true if logged in
 * @param {string} statusMessage Current status of login in text form
 *
*/

/**
 * Log out the user.
 *
 * @param {string} baseURL base of url, version and rest of api call added in function
 * @param {logoutFromServerCallback} loginToServerCallback Function to interpret login status results from server
 * @param {boolean} keepAlive Keep the connection alive (this may limit the number of users on a shared account that can connect)
 * @returns {void}
*/
function logoutFromServer(baseURL, logoutFromServerCallback, keepAlive) {
  var keepAliveAddOn = "";
  if (keepAlive === true) {
    keepAliveAddOn = "?ka=true";
  }

  var apiCall = baseURL + "/v1/Logout" + keepAliveAddOn;

  if (typeof logoutFromServerCallback === 'undefined') {
        logoutFromServerCallback = null;
  }

  $.ajax({
    dataType: "json",
    url: apiCall,
    success: function (data) {
      loggedInToServer = false;

      if (logoutFromServerCallback === null) {
        alert("Logged Out");
      } else {
        logoutFromServerCallback(false, "Logged out!");
      }
    },
    error: function (jqXHR, exception) {
      var msg;
      msg = 'Error.\n' + jqXHR.responseText;
      loggedInToServer = false;

      if (logoutFromServerCallback === null) {
          alert("Logout failed.  MSG:" + msg);
      } else {
          logoutFromServerCallback(false, msg);
      }
    }
  });
}


/**
 * This callback is used by the getDocumentData function.
 *    e.g., getDocumentDataCallback (status, statusMessage, statusCode, accessToken)
 * @callback getDocumentDataCallback
 * @param {boolean} status true if logged in
 * @param {object} statusMessage Current status of login as textual code for l10n translation, and English text, e.g., {messageID:"pageNotFound", description:"Requested page not found. [404]"};
 * @param {integer} statusCode Ajax status code of server request
 * @param {string} accessToken Token used to verify permissions and track session (null if )
 *
*/

/**
 * Get the fulltext of the document
 *
 * @param {string} documentID the PEP locator of the article, plus any legal qualifiers.  That includes a subdocument location.
 * @param {string} accessToken Token used to verify permissions and track session
 * @param {getDocumentDataCallback} finishedCallback Function to interpret login status results from server
 * @example <caption>Looks up glossary term and jumps to location in document</caption>
 *
 *    getDocumentData(self.currGlossaryTermID(), self.accessToken(), self.glossaryEntryHTMLCallback);
 *
 * @todo
 *   ResponseSet is used inconsistently in the API.  Unlike other responseSet returns, it's not an array.  It should eventually be
 *         changed for this api return to an array, even if we are only going to use the one, in order to be used consistently.
 * @todo
 *   It might be a good idea later to have some of the HTML transformations which are done in this routine to be done at the
 *         server level so the less well-equipped client processor doesn't have to spend the time.
 * @returns {void}
*/
//=============================================================================
function getDocumentData(documentID, accessToken, getDocumentDataCallback) {
    // Get the fulltext of the document.
    var oReq = new XMLHttpRequest();
    var apiCall = baseURL + "/v1/Documents/" + documentID + "/";
    oReq.open("GET", apiCall, true);
    oReq.responseType = "json";
    oReq.withCredentials = true;
    var statusMessageObj = null;

    // since IE doesn't support defaults for paramaters, have to do it this way.
    if (accessToken !== "") {
        $("html").addClass("waiting");
        if (accessToken !== "IPLogin") {
          oReq.setRequestHeader('Authorization', 'Bearer ' + accessToken);
        }
        //console.log("GetDocumentData Request with accessToken: " + accessToken);
        oReq.onload = function (oEvent, exception) {
            var data = null;
            if (oReq.status !== 200) { //failure
                statusMessageObj = ajaxCallErrorMessages(oReq, loggedInToServer, exception);
                $("html").removeClass("waiting");
                if (typeof getDocumentDataCallback !== 'undefined') {
                    //documentHTMLReadyCallback = function (responseInfoObject, retStatusCode, retStatusMessage, document)
                    getDocumentDataCallback(null, oReq.status, statusMessageObj, null);
                } // end of failure
            } else {
                // success
                var browserVer = msieversion();
                if (browserVer === false) {
                    data = oReq.response; // NOT IE.  Others don't seem to need the parse here.
                } else if (browserVer >= 12) {
                    // browser is Edge
                    data = oReq.response; // NOT IE.  Others don't seem to need the parse here.
                } else {
                    data = JSON.parse(oReq.response); // for IE.  Others don't seem to need the parse here.
                }
                var responseSet = data.documents.responseSet;
                var newContent = responseSet.document;
                // shouldn't need these later, since part of object
                //var accessLimited = responseSet.accessLimited;
                //var accessLimitedDescription = responseSet.accessLimitedDescription;
                //              documentID = responseSet.documentID;
                //              console.log("Document request was: " + documentID);
                //              console.log("Access limit flag is: " + accessLimited);
                //              console.log("Description: " + accessLimitedDescription);

                //newContent = newContent.replace(/href=\"document\.php\?id\=/g, 'data-bind="click:documentCrossRef" href=#/Document/"');
                //newContent = decodeHtml(newContent);
                //newContent = newContent.replace(/href=\"\#JStyleTOC([^\"]+)\"/g, "href='#'");
                // reference
                newContent = newContent.replace(/href=\"document\.php\?id\=([^\"]+)\"/g, "href=#/Document/$1");
                // newContent = newContent.replace(/href=\"search\.php\?artqual\=([^\"]+)\"/g, "href=#/Search/?artqual=$1");
                // newContent = newContent.replace(/href=\"search\.php\?origrx\=([^\"]+)\"/g, "href=#/Search/?origrx=$1");
                newContent = newContent.replace(/href=\"search\.php\?([^\"]+)\"/g, "href=#/Search/?$1");
                // The title link which normally brings up the volume TOC
                newContent = newContent.replace(/href=\"toc\.php\?journal=([^\&]+).*volume=([^\#]+)\#p?([0-9]+)\"/g, "href=#/ArticleList/?journal=$1&amp;vol=$2&amp;page=$3");
                // handle embedded download links
                newContent = newContent.replace(/href=\"[ ]?\/v1\/Documents\/Downloads\/PDF\/([^\"]+)\"/g, "href=''");
                //newContent = newContent.replace(/href=\"#p([^\"]+)\"/g, "href='#/Document/" + responseSet.documentID + "#p$1'");
                newContent = newContent.replace(/href=\"#(p?)([^\"]+)\"/g, "href='#/Document/" + responseSet.documentID + "#$1$2'");

                responseSet.document = newContent;  // so we can pass back changed string data in responseSet

                // if (videoTranscription !== undefined) {
                //   videoTranscription = decodeHtml(videoTranscription);
                //   console.log(videoTranscription);
                //   postscribe($(".video-container div:nth-child(2)"), videoTranscription);
                // }
                // just for now
                if (responseSet.accessLimited === true) {
                    statusMessageObj = {messageID: "limited", description: responseSet.accessLimitedDescription};
                } else {
                    if (apiCall.search("/Abstract") !== -1) {
                        statusMessageObj = {messageID:"abstract", description: "This is the abstract or summary.  Use the buttons below to read or download the full document."};
                    } else if (apiCall.search("/Document") !== -1) {
                        statusMessageObj = {messageID:"fullDocument", description: "This is the full document."};
                    } else {
                        statusMessageObj = {messageID:"unknownError", description: "An unknown error retrieving the document has occurred!"};
                    }
                }

              $("html").removeClass("waiting");

              if (typeof getDocumentDataCallback !== 'undefined') {
                //documentHTMLReadyCallback = function (responseInfoObject, retStatusCode, retStatusMessage, documentID) {
                // we want to pass by reference, so pass as object data.documents.responseInfo and responseSet
                getDocumentDataCallback(data.documents.responseInfo, oReq.status, statusMessageObj, responseSet);
              }
            } // end of success
        };

        oReq.send();
    } // end if accessToken !== ""
}

function getAbstractWithCred(documentID, accessToken, finishedCallback) {
    // Get the fulltext of the document.
    var oReq = new XMLHttpRequest();
    var apiCall = baseURL + "/v1/Documents/Abstracts/" + documentID + "/";

    oReq.open("GET", apiCall, true);
    oReq.responseType = "json";
    oReq.withCredentials = true;
    var statusMessageObj = null;
    if (accessToken === undefined) {
      accessToken === "";
    }

    if (accessToken !== "" && accessToken !== "IPLogin") {
        oReq.setRequestHeader('Authorization', 'Bearer ' + accessToken);
    } else {
      if (loggedInToServer) {
        console.log("Logged into server but accessToken not supplied in API call getAbstract. The value of accessLimited will not be accurate.");
      }
    } // no access token, but still can make the call

    //console.log("GetDocumentData Request with accessToken: " + accessToken);
    oReq.onload = function (oEvent, exception) {
        var data = null;
        if (oReq.status !== 200) { //failure
            statusMessageObj = ajaxCallErrorMessages(oReq, loggedInToServer, exception);
            if (typeof finishedCallback !== 'undefined') {
                //finishedCallback(null, oReq.status, statusMessageObj, null);
                statusMessage = "There was an error retrieving the abstract for document: " + documentID;
                if (finishedCallback !== null) {
                    // callback structure: (statusMessage, documentID, abstractObject)
                    finishedCallback(statusMessage, documentID, null);
                }
            } // end of failure
        } else {
            // success
            var statusMessage = null;
            //statusMessageObj = ajaxCallErrorMessages(oReq, loggedInToServer, exception);
            var browserVer = msieversion();
            if (browserVer === false) {
                data = oReq.response; // NOT IE.  Others don't seem to need the parse here.
            } else if (browserVer >= 12) {
                // browser is Edge
                data = oReq.response; // NOT IE.  Others don't seem to need the parse here.
            } else {
                data = JSON.parse(oReq.response); // for IE.  Others don't seem to need the parse here.
            }
            if (data.documents.responseInfo.count === 1) {
                var abstract = data.documents.responseSet[0].abstract;
                abstract = abstract.replace(/<script.*<\/script>/g, "");
                abstract = abstract.replace(/<\/?span.*?>/g, "");
                // get rid of Freud SE/GW lgids now just next to the text!
                abstract = abstract.replace(/\[(SE|GW)[A-Z][0-9]{1,4}[a-z][0-9]{1,4}\]/g, "");
                abstract = abstract.replace(/href=\"document\.php\?id\=([^\"]+)\"/g,  "href=#/Document/$1");
                abstract = abstract.replace(/href=\"toc\.php\?journal=([^\&]+).*volume=([^\#]+)\#p?([0-9]+)\"/g, "class='disabled'");
                // remove icons from titles
                abstract = abstract.replace(/src=\"images\/.*\"/g, 'src=""');
                data.documents.responseSet[0].abstract = abstract;

                if (data.documents.responseSet[0].accessLimitedDescription !== undefined) {
                  statusMessage = data.documents.responseSet[0].accessLimitedDescription;
                }

                if (data.documents.responseSet[0].accessLimited) {
                  // user does not have access.
                  data.documents.responseSet[0].accessPermitted = false;
                }
                else {
                  data.documents.responseSet[0].accessPermitted = true;
                }

                if (finishedCallback !== null) {
                    // pass back status, and the responseSet portion of the first abstract
                    // (this function only returns one, even though abstracts can return multiples)
                    // callback structure: (statusMessage, documentID, abstractObject)
                    finishedCallback(statusMessageObj, documentID, data.documents.responseSet[0]);
                } else {
                  alert("There was an error retrieving the abstract for document: " + documentID);
                }
            }

        } // end of success
        $("html").removeClass("waiting");
    }; // end of onload

    $("html").addClass("waiting");
    oReq.send();
}


/**
 * This callback is used by the getAbstract function.
 * @callback finishedCallback
 * @param {string} statusMessage Message from server about status of the call
 * @param {string} documentID PEP Locator (documentID) requested
 * @param {object} abstractObject Object containing documentID, documentRef, abstract
*/

/**
 * Get a single abstract for a documentID (PEP Locator) from server and return it to the callback
 *
 * @param  {string} documentID PEP Locator (e.g., IJP.075.0119a) for document to get abstract
 * @param {finishedCallback} finishedCallback Declare: function finishedCallback(statusMessage, documentID, abstractObject)
 * @returns {void}
*/
function getAbstract(documentID, finishedCallback) {

  // callback return structure: finishedCallback(statusMessage, documentID, abstractObject)

  if (typeof finishedCallback === 'undefined') {
      finishedCallback = null;
  }

  $("html").addClass("waiting");
  var apiCall = baseURL + "/v1/Documents/Abstracts/" + documentID + "/";
  console.log("apiCall:" + apiCall);
  $.getJSON(apiCall, function (data, status) {
      var statusMessage = null;
      if (data.documents.responseInfo.count === 1) {
          console.log(data.documents.responseSet);
          //var abstract = decodeHtml(data.documents.responseSet[0].abstract);
          var abstract = data.documents.responseSet[0].abstract;

          abstract = abstract.replace(/<script.*<\/script>/g, "");
          abstract = abstract.replace(/<\/?span.*?>/g, "");
          // get rid of Freud SE/GW lgids now just next to the text!
          abstract = abstract.replace(/\[(SE|GW)[A-Z][0-9]{1,4}[a-z][0-9]{1,4}\]/g, "");
          abstract = abstract.replace(/href=\"document\.php\?id\=([^\"]+)\"/g,  "href=#/Document/$1");
          abstract = abstract.replace(/href=\"toc\.php\?journal=([^\&]+).*volume=([^\#]+)\#p?([0-9]+)\"/g, "class='disabled'");
          // remove icons from titles
          abstract = abstract.replace(/src=\"images\/.*\"/g, 'src=""');


          data.documents.responseSet[0].abstract = abstract;

          if (data.documents.responseSet[0].accessLimitedDescription !== undefined) {
            statusMessage = data.documents.responseSet[0].accessLimitedDescription;
          }

          if (data.documents.responseSet[0].accessLimited) {
            data.documents.responseSet[0].accessPermitted = false;
          }
          else {
            data.documents.responseSet[0].accessPermitted = true;
          }

//          console.log("API StatusMessage: " + statusMessage);
          if (finishedCallback !== null) {
              // pass back status, and the responseSet portion of the first abstract
              // (this function only returns one, even though abstracts can return multiples)
              // callback structure: (statusMessage, documentID, abstractObject)
              finishedCallback(statusMessage, documentID, data.documents.responseSet[0]);
          } else {
            statusMessage = "There was an error retrieving the abstract for document: " + documentID;
            if (finishedCallback !== null) {
                // callback structure: (statusMessage, documentID, abstractObject)
                finishedCallback(statusMessage, documentID, null);
            }
          }
      }
      $("html").removeClass("waiting");
  }, "json");
  return;
}

//=============================================================================
/**
 * This callback is used by the getDocumentDownload function.
 *    e.g., getDocumentDataCallback (status, statusMessage, statusCode, accessToken)
 * @callback getDocumentDataCallback
 * @param {boolean} status true if logged in
 * @param {object} statusMessage Current status of login as textual code for l10n translation, and English text, e.g., {messageID:"pageNotFound", description:"Requested page not found. [404]"};
 * @param {integer} statusCode Ajax status code of server request
 * @param {string} accessToken Token used to verify permissions and track session (null if )
 *
*/

/**
 * Get the fulltext of the document
 *
 * @param {string} apiCall baseURL + "/v1/Documents/Downloads/" + "PDF" + "/" + documentID + apiAddOn where optionally apiAddon is ?option=embed1.
 * @param {string} documentID the PEP locator of the article, plus any legal qualifiers.  That includes a subdocument location.
 * @param {string} accessToken Token used to verify permissions and track session
 * @param {getDocumentDownloadCallback} finishedCallback Function to interpret login status results from server
 * @example <caption>Looks up glossary term and jumps to location in document</caption>
 *
 *    getDocumentDownload(documentID, accessToken, documentDownloadCallback);
 *
 * @returns {void}
*/

function getDocumentDownload(apiCall, documentID, documentExtension, accessToken, getDocumentDownloadCallback) {
    // Get the ePub or PDF document.  Should not be called for anything else.
    var oReq = new XMLHttpRequest();
    var documentSaveName = documentID;
    oReq.open("GET", apiCall, true);
    oReq.responseType = "arraybuffer";
    oReq.withCredentials = true;

    if (typeof getDocumentDownloadCallback === 'undefined') {
        getDocumentDownloadCallback = null;
    }

    if (accessToken !== "") {
        if (accessToken !== "IPLogin") {
          oReq.setRequestHeader('Authorization', 'Bearer ' + accessToken);
        }
        oReq.onload = function (oEvent, exception) {
            var msg = '';
            var downloadLocation;
            var statusMessageObj;
            var isIE11 = !!window.MSInputMethodContext && !!document.documentMode;
            var iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

            if (oReq.status !== 200) {
                statusMessageObj = ajaxCallErrorMessages(oReq, loggedInToServer, exception);
                if (getDocumentDownloadCallback !== null) {
                    getDocumentDownloadCallback(null, oReq.status, statusMessageObj, documentID, null);
                }
            } else { // success
                if (oReq.response.byteLength === 0) {
                    // download essentially failed, logged in but probably not licensed to download.
                    msg = "Download unsuccessful.  Current content is not available on PEP-Web but may be available to journal subscribers on the publisher's website.  If not current content, your subscription may not include downloads of this document.";
                    statusMessageObj = {messageID:"DownloadFailed", description:msg};
                    if (getDocumentDownloadCallback !== null) {
                        // documentDownloadReadyCallback = function (responseLength, retStatusCode, retStatusMessage, documentID)
                        // as close an error as I can find, 415 Unsupported Media Type
                        getDocumentDownloadCallback(0, 415, statusMessageObj, documentID, null);
                    }
                } else {
                    var blob;
                    if (documentExtension === "pdf") {
                      blob = new Blob([oReq.response], {type: 'application/pdf'});
                    }
                    else {
                      blob = new Blob([oReq.response], {type: 'application/epub+zip'});
                    }

                    if (isIE11) {
//                      console.log("ie11");
                      window.navigator.msSaveBlob(blob, documentSaveName + "." + documentExtension);
                      var link = document.createElement('a');
                      link.href = window.URL.createObjectURL(blob);
                      link.download = documentSaveName + "." + documentExtension;
                      downloadLocation = link.download;
                      msg = "Download successful.  Document saved to " + link.download + ".";
                      statusMessageObj = {messageID:"downloadSuccess", description:msg};
                    }
                    else if (iOS) {
//                      console.log("iOS");

                      downloadLocation = "browser";
                      msg = "Download successful.  Document opened.";
                      statusMessageObj = {messageID:"downloadSuccess", description:msg};
                      var reader = new FileReader();
                      reader.onload = function(e){
                        window.location.href = reader.result;
                      }
                      reader.readAsDataURL(blob);

                    }
                    else {
//                      console.log("else");
                      var link = document.createElement('a');
                      link.href = window.URL.createObjectURL(blob);
                      link.download = documentSaveName + "." + documentExtension;
                      downloadLocation = link.download;
                      msg = "Download successful.  Document saved to " + link.download + ".";
                      statusMessageObj = {messageID:"downloadSuccess", description:msg};

                      // required for firefox and ie
                      document.body.appendChild(link);
                      link.target = "_blank";
                      link.click();
                    }

                    if (getDocumentDownloadCallback !== null) {
                        // documentDownloadReadyCallback = function (responseLength, retStatusCode, retStatusMessage, documentID)
                        getDocumentDownloadCallback(blob.length, 200, statusMessageObj, documentID, downloadLocation);
                    }
                }
            } // end success processing
        };
        // send it, response comes in the onload event.
        oReq.send();
    }
    return;
}

//=============================================================================
function getListOfWhatsNew(arrObj) {
    $("html").addClass("waiting");
    // var apiURL = baseURL + "/v1/Database/WhatsNew/?limit=10&dayssince=7";
    var apiURL = baseURL + "/v1/Database/WhatsNew/";
    var obj;
    $.getJSON(apiURL, function (data, status) {
        arrObj([]);
        for (var i = 0, n = data.whatsNew.responseSet.length; i < n; i++) {
            obj = data.whatsNew.responseSet[i];
            arrObj.push({
                volumeURL: "" + obj.PEPCode + "/" + obj.volume,
                PEPCode: obj.PEPCode.toUpperCase(),
                srcTitleSeries: decodeHtml(obj.srcTitle),
                displayTitle: decodeHtml(obj.displayTitle),
                vol: obj.volume,
                issueInfo: obj.issue,
                updated: obj.updated.substring(0, 10)
            });
        }
        $("html").removeClass("waiting");
    }, "json");

    return;
}

/**
 * Get the list of the most cited or viewed publications on PEP (based on apiURL from caller)
 *
 * @param {string} apiURL
 * @param {string} arrObj
 * @param {string} statusMessageObservable
 * @param {string} serverFlag
 * @param {boolean} journalsOnly
 * @example <caption>Most cited</caption>
 *    getListOfMost(baseURL + "/v1/Database/Search/?citecount=100&limit=10", self.currMostCitedData, self.statusMessageLocal, serverFlag = false);
 *
 * @example <caption>Most viewed</caption>
 *    getListOfMost(baseURL + "/v1/Database/Search/?viewcount=90&viewperiod=month&limit=90", self.currMostDownloadedData, self.statusMessageLocal, serverFlag = true);
 *
 * @todo Needs to be rewritten to eliminate the observable, with a callback instead
 *  also would be good to use a simpler call syntax that doesn't require the apiURL,
 *  since the idea of the library is to make it easy to use the API without worrying about API details
 *
 * @returns {void}
*/
function getListOfMost(apiURL, arrObj, statusMessageObservable, serverFlag, journalsOnly) {
    // this version of the most list doesn't expect the specific getMost call, it uses search
    // which returns a documentList
    $("html").addClass("waiting");
    var bookCodes = ["ZBK", "IPL", "NLP", "SE", "GW"];

    //console.log("Get List Of Most.  Server call: " + apiURL);

    if (typeof statusMessageObservable === 'undefined') {
        statusMessageObservable = null;
    }

    if (typeof serverFlag === 'undefined') {
        serverFlag = null;
    }

    if (typeof journalsOnly === 'undefined' || journalsOnly === null) {
        journalsOnly = true;
    }

    if (serverFlag) {
        statusMessageObservable("...Waiting for Server...");
    } else if (statusMessageObservable !== null) {
        statusMessageObservable("");
    }

    $.getJSON(apiURL, function (data, status) {
            arrObj([]);
            var obj, vol;
            var documentIDSplit;
            var PEPCodeUpper;

            // console.log("Status: " + status);
            // This syntax doesn't work in IE 11!  Need to use loop
            // for (var obj of data.documentList.responseSet) {
            // IE compatible syntax
            for (var i = 0, n = data.documentList.responseSet.length; i < n; i++) {
                obj = data.documentList.responseSet[i];
                //  only store journals, not books and videos
                PEPCodeUpper = obj.PEPCode.toUpperCase();
                documentIDSplit = obj.documentID.split(".");
                vol = documentIDSplit[1];
                vol.replace(/^0+/, '');
                // console.log("Vol split from ID: " + vol)
                if (bookCodes.indexOf(PEPCodeUpper) == -1 && PEPCodeUpper.slice(-2) != "VS") {
                    arrObj.push({
                        documentID: obj.documentID,
                        documentRef: decodeHtml(obj.documentRef),
                        vol: vol,
                        PEPCode: obj.PEPCode.toUpperCase()
                    });
                }
            }
            if (serverFlag) {
                statusMessageObservable('');
            }
        }, "json")
        .success(function () {
            // console.log("There are " + matchCount + " matches");
            // console.log("There were " + arrObj().length + " matches stored");
            $("html").removeClass("waiting");
            //alert("success 2");
        })
        .error(function (jqXHR, textStatus, errorThrown) {
            // console.log("error " + textStatus);
            // console.log("incoming Text " + jqXHR.responseText);
            $("html").removeClass("waiting");
        });

    return;
}

//=============================================================================
// function to reuse server call for various source loads
function getListOfSources(apiCall, arrObj, finishedCallback) {
    // Load journals, books, videos from server call
    // self.currentAPICall(apiCall);
    // Sample Calls
    // getListOfSources(baseURL + "/v1/Metadata/Journals/", self.journals);
    // getListOfSources(baseURL + "/v1/Metadata/Books/", self.books);
    // getListOfSources(baseURL + "/v1/Metadata/Videos/", self.videos);

    var singleBookCodes = ["ZBK"]; //Only one, but could be expanded.
    var multivolumeBooks = ["IPL", "NLP"];
    var obj;
    var documentIDSplit;
    //    var documentIDUpper;

    //console.log("Get List Of Sources.  Server call: " + apiCall);

    $.getJSON(apiCall, function (data, status) {
        //console.log("Data: " + data.titles.length + "\nStatus: " + status);
        // for (var obj of data.sourceInfo.responseSet) {
        for (var i = 0, n = data.sourceInfo.responseSet.length; i < n; i++) {
            obj = data.sourceInfo.responseSet[i];
            var sourceType;
            var documentIDUpper = "";
            var docRef = "";

            //var contentsAPIURL;
            var volume = null;
            obj.displayTitle = decodeHtml(obj.displayTitle);
            var PEPCodeUpper = obj.PEPCode.toUpperCase();
            // PEP2020 had to add and obj.documentID !== null
            if (obj.documentID !== undefined and obj.documentID !== null) {
                documentIDSplit = obj.documentID.split(".");
                documentIDUpper = documentIDSplit[0].toUpperCase() + "." + documentIDSplit[1];
                // temp fix for GVPI Changes
                obj.PEPCode = documentIDSplit[0].toUpperCase();
                PEPCodeUpper = obj.PEPCode;
                volume = documentIDSplit[1];
            } else { // journals
                documentIDUpper = PEPCodeUpper;
            }
            if (singleBookCodes.indexOf(PEPCodeUpper) != -1) {
                // it's a ZBK
                // contentsAPIURL = "/v1/Metadata/Contents/Books/" + documentIDUpper.substring(0,7);
                // volListURL = null;
                sourceType = "Book";
            } else if (multivolumeBooks.indexOf(PEPCodeUpper) != -1) {
                // it's a multivolumeBook  like SE, IPL, NLP
                // contentsAPIURL = "/v1/Metadata/Contents/Books/" + documentIDUpper.substring(0,7);
                sourceType = "BookSerial";
                // volListURL = "/v1/Metadata/Contents/" + PEPCodeUpper.slice(6);
            } else {
                // It's a journal
                // not sure yet where to put videos! So they fall here now.
                //contentsAPIURL = null;
                sourceType = "Serial";
                // volListURL = "/v1/Metadata/Contents/" + PEPCodeUpper;
            }
            if (obj.PEPCode === "SE") {
                // special SE code
                docRef = "The Standard Edition of the Complete Psychological Works of Sigmund Freud, Vols 1-24 \
                                <ul> \
                                   <li><a href=\"#Books/BookContents/cSE/v1\">Volume 1</a></li> \
                                   <li><a href=\"#Books/BookContents/cSE/v2\">Volume 2</a></li> \
                                </ul> \
                            ";
                obj.displayTitle = docRef;
            }

            if (obj.PEPCode === "GW") {
                // special GW code
                docRef = "Gesammelte Werke: Chronologisch Geordnet, Vols 1-18<ul> \
                                <li data-bind=\"attr: {id: documentID, sourceType: sourceType}, \
                                           click: $root.goToTOCDirect\"> \
                                    <a href=\"#Books/BookContents/cGW.v1\">Volume 1</a></li> \
                                <li><a href=\"#Books.BookContents.cGW.v2\">Volume 2</a></li></ul>";
                obj.displayTitle = docRef;
            }

            arrObj.push({
                sourceType: sourceType,
                title: obj.PEPCode + ": " + obj.displayTitle,
                PEPCode: obj.PEPCode,
                volume: volume,
                //contentsAPIURL: contentsAPIURL,
                // volListURL: volListURL,
                documentID: documentIDUpper,
                issn: obj.issn,
                isbn: obj.ISBN - 10
            });
        }

        if (typeof finishedCallback !== 'undefined') {
            finishedCallback(arrObj, data.sourceInfo.responseInfo);
        }

    }, "json");

    return;
}

//=============================================================================
function getSearchAnalysis(apiCall, arrObj, finishedCallback) {

    var obj;
    // console.log("Get Search Analysis: " + apiCall);
    $.getJSON(apiCall, function (data, status) {
        arrObj([]);
        if (data.documentList.responseInfo.count > 0) {
            // for (var obj of data.volumeList.responseSet) {
            for (var i = 0, n = data.documentList.responseSet.length; i < n; i++) {
                obj = data.documentList.responseSet[i];
                arrObj.push({
                    term: obj.term,
                    termCount: obj.termCount,
                    combined: obj.combined,
                    combinedCount: obj.combinedCount
                });
                //console.log(obj);
            }
        }

        if (typeof finishedCallback !== 'undefined') {
            finishedCallback(data.documentList.responseInfo);
        }
    }, "json");
}

//=============================================================================
function getListOfVols(apiCall, arrObj) {
    // Load list of volumes from server call
    // Sample Calls:
    // var apiCall = baseURL + "/v1/Metadata/Volumes/" + PEPCode;
    //  getListOfVols(apiCall, self.listOfVols);

    var obj;

    $.getJSON(apiCall, function (data, status) {
        arrObj([]);
        // for (var obj of data.volumeList.responseSet) {
        for (var i = 0, n = data.volumeList.responseSet.length; i < n; i++) {
            obj = data.volumeList.responseSet[i];
            arrObj.push({
                PEPCode: obj.PEPCode,
                vol: obj.vol,
                year: obj.year
            });
        }
    }, "json");
}

//=============================================================================
function getListOfArticles(apiCallFull, arrObj, finishedCallback) {
    // self.currentAPICall(apiCallFull);
    var obj;
    var kwicSep;
    $("html").addClass("waiting");
    // clear status variable.
    $.getJSON(apiCallFull, function (data, status) {
        arrObj([]);
        var hasKWIC = false;
        // for (var obj of data.documentList.responseSet) {
        for (var i = 0, n = data.documentList.responseSet.length; i < n; i++) {
            obj = data.documentList.responseSet[i];
            //var jsobj = obj;
            obj.documentRef = decodeHtml(obj.documentRef);
            kwicSep = obj.kwic;
            if (kwicSep !== "") {
                hasKWIC = true;
                if (kwicSep.substr(kwicSep.length - 5) === '. . .') {
                    kwicSep = kwicSep.substr(0, kwicSep.length - 6);
                }
                kwicSep = kwicSep.replace(/\. \. \./g, "</li><li>");
            }

            arrObj.push({
                documentRef: obj.documentRef,
                documentID: obj.documentID,
                vol: obj.vol,
                searchRank: obj.rank,
                kwic: kwicSep,
                PEPCode: obj.PEPCode.toUpperCase()
            });
        }
        //console.log("# items loaded: " + self.listOfContents().length);
        $("html").removeClass("waiting");
        if (typeof finishedCallback !== 'undefined') {
            data.documentList.responseInfo["hasKWIC"] = hasKWIC;
            finishedCallback(data.documentList.responseInfo);
        }
    }, "json");
}

//=============================================================================
function getListOfcurrAuthorIndexData(apiURL, arrObj) {
    // self.currentAPICall(apiURL);
    $("html").addClass("waiting");
    $.getJSON(apiURL, function (data, status) {
        var obj;
        // arrObj([]);
        // console.log("# items returned: " + data.authorIndex.responseSet.length);
        // for (var obj of data.authorIndex.responseSet) {
        for (var i = 0, n = data.authorIndex.responseSet.length; i < n; i++) {
            obj = data.authorIndex.responseSet[i];
            //var jsobj = obj;
            arrObj.push({
                authorID: obj.authorID,
                publicationURL: obj.publicationsURL
            });
        }
        // console.log("# items loaded: " + arrObj.length);
        // console.log("Length of authorIndexData: " + self.indexResults.currAuthorIndexData().length);
        $("html").removeClass("waiting");
    }, "json");
}

//=============================================================================
function getListOfcurrAuthorPublications(apiURL, arrObj) {
    $("html").addClass("waiting");
    $.getJSON(apiURL, function (data, status) {
        var obj;
        arrObj([]);
        // for (var obj of data.authorPubList.responseSet) {
        for (var i = 0, n = data.authorPubList.responseSet.length; i < n; i++) {
            obj = data.authorPubList.responseSet[i];
            //var jsobj = obj;
            obj.documentRef = decodeHtml(obj.documentRef);
            obj.authorID = decodeHtml(obj.authorID);
            arrObj.push({
                authorID: obj.authorID,
                documentID: obj.documentID,
                documentRef: obj.documentRef,
                documentURL: obj.documentURL
            });
        }
        // console.log("# Author Pubs loaded: " + data.authorPubList.responseInfo.count);
        $("html").removeClass("waiting");
    }, "json");
}

//=============================================================================
function isABook(PEPCode) {
    var books = ["ZBK", "IPL", "NLP"];
    if (books.indexOf(PEPCode) !== -1) {
        return true;
    } else {
        return false;
    }
}

/**
 * Converts an html characterSet into its original character.
 *
 * @param {String} str htmlSet entities
 **/
function decode(str) {
    return str.replace(/&#(\d+);/g, function(match, dec) {
        return String.fromCharCode(dec);
    });
}

function decodeHtml(html) {
    var txt = document.createElement("textarea");
    txt.innerHTML = html;
    return txt.value;
}

function setCookie(cname, cvalue, exdays, domainName) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    var expires = "expires=" + d.toUTCString();

    if (typeof domainName === 'undefined') {
      document.cookie = cname + "=" + cvalue + ";" + expires;
    }
    else {
      //console.log("Cookie domain name specified for " + cname);
      document.cookie = cname + "=" + cvalue + ";" + expires+"; path=/" + "; domain=" + domainName;
    }

    //  console.log("Cookie set..." + cname + "=" + cvalue + ";" + expires);
    //  console.log("Cookies..." + document.cookie);
}

function getCookie(cname, defaultVal) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    if (typeof defaultVal === 'undefined' || defaultVal === null) {
        defaultVal = "";
    }

    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return defaultVal;
}

function deleteCookie(cname) {
    // to delete a cookie set an expiration date in the past.
    setCookie(cname, "", -1)
}

function make_base_auth(user, password) {
    var tok = user + ':' + password;
    var hash = btoa(tok);
    return "Basic " + hash;
}

function setup(defaultVal) {
    if (typeof defaultVal === 'undefined' || defaultVal === null) {
        defaultVal = "1.5";
    }
    fSize = getCookie("fontSize", defaultVal);
    //console.log("Setting default font size: " + fSize + "em");
    // fSize = parseFloat(fSize);
    document.body.style.fontSize = fSize + "em";
}

function setFontSize(fontSize) {
    if (typeof fontSize === 'undefined' || fontSize === null) {
        fontSize = "1.5";
    }
    fSize = fontSize;
    document.body.style.fontSize = fontSize + "em";
    setCookie("fontSize", fontSize, 100);
}

function enlargeFont() {
    fSize += 0.1;
    document.body.style.fontSize = fSize + "em";
}

function reduceFont() {
    fSize -= 0.1;
    document.body.style.fontSize = fSize + "em";
}

function popupReferenceBox(refHTML) {
    // modal pop-up with reference
    if (typeof refHTML === undefined) {
        alert("Can't display reference because it's not loaded.");
    } else {
        $("#refModal.modal-body").innerHTML = refHTML;
        $("#refModal").modal('show');
    }
}

$(document).ready(function () {
    setup();
    // $('p').qtip();

    // this supposedly is a way to test if it's a touch device.
    function isTouchDevice() {
        return !!('ontouchstart' in window) || !!('msmaxtouchpoints' in window.navigator);
    }

    // console.log("Is this a touch device? " + isTouchDevice());

    // Attach a delegated event handler
    $("body").on("click", "[data-docid]", function (event) {
        var elem = $(this);
        // if ( elem.is( "[href^='http']" ) ) {
        //     elem.attr( "target", "_blank" );
        var termID = elem.attr("data-docid");
        //        console.log("Show! " + termID);
        showGlossaryModal(termID);
    });

    $("body").on("click", ".bibtip", function (event) {
        var okToDisplay = false;
        var retVal = "";
        var elem = $(this);
        var bibid = elem.attr("data-element");

        // Escape any dots...jquery thinks they are class selectors.
        bibid = bibid.replace(/\./g, "\\\.");
        var bibContent = elem.attr("data-content");
        if (bibContent === undefined) {
            var bibtxt = $("#" + bibid).html();
            if (bibtxt !== undefined) {
                retVal = decodeHtml(bibtxt);
                okToDisplay = true;
            }
            // console.log("Bibtext: " + retVal);
        } else {
            retVal = decodeHtml(bibContent);
            okToDisplay = true;
        }
        if (okToDisplay) {
            // $("#refContent").innerHTML = "<p>retVal</p>";
            document.getElementById("refContent").innerHTML = retVal;
            // console.log("RefContent: " + $("#refContent").html());
            $("#refModal").modal('show');
        }

        return retVal;
    });

    $("body").on("click", ".ftntip", function (event) {
        var elem = $(this);
        var ftnid = elem.attr("data-element");
        var ftn = $("#" + ftnid).html();
        var retVal = decodeHtml(ftn);
        // console.log("Bibtext: " + retVal);
        // $("#refContent").innerHTML = "<p>retVal</p>";
        document.getElementById("ftnContent").innerHTML = retVal;
        // console.log("ftnContent: " + $("#ftnContent").html());
        $("#ftnModal").modal('show');
        event.stopPropagation();
        return false;
    });

    $("body").on("click", ".notetip", function (event) {
        var elem = $(this);
        var noteid = elem.attr("data-element");
        var note = $("#" + noteid).html();
        var retVal = decodeHtml(note);
        // console.log("Bibtext: " + retVal);
        // $("#refContent").innerHTML = "<p>retVal</p>";
        document.getElementById("noteContent").innerHTML = retVal;
        // console.log("ftnContent: " + $("#ftnContent").html());
        $("#noteModal").modal('show');
        event.stopPropagation();
        return false;
    });

    $("body").on("click", ".authortip", function (event) {
        var elem = $(this);
        var authorInfo = elem.attr("data-content");
        var retVal = decodeHtml(authorInfo);
        //console.log("AuthorInfo html: " + retVal);
        // $("#refContent").innerHTML = "<p>retVal</p>";
        document.getElementById("autContent").innerHTML = retVal;
        // console.log("ftnContent: " + $("#ftnContent").html());
        $("#autModal").modal('show');
        return retVal;
    });

    $("body").on("click", ".booktip", function (event) {
        var elem = $(this);
        var info = elem.attr("data-content");
        var retVal = decodeHtml(info);
        document.getElementById("moreInfoContent").innerHTML = retVal;
        // console.log("ftnContent: " + $("#ftnContent").html());
        $("#moreInfoModal").modal('show');
        return retVal;
    });

    // var enableHover = false;
    // $( function() {
    //     if (isTouchDevice() === false && enableHover === true) {
    //         $( document ).tooltip({
    //           track:true,
    //           items: "img, .ftntip, .bibtip, [title]",
    //           content: function() {
    //             var element = $( this );
    //
    //             if ( element.is( "[title]" ) ) {
    //               return element.attr( "title" );
    //             }
    //
    //             if ( element.is( "img" ) ) {
    //               if (element.parent().is( "span" ) ) {
    //                 return element.parent().attr( "data-content" );
    //               }
    //             }
    //
    //             if ( element.is( ".ftntip" ) ) {
    //               var ftnid = element.attr("data-element");
    //               var ftn = $("#" + ftnid).html();
    //               var retVal = ftn;
    //               return retVal;
    //             }
    //           }
    //         })
    //         .on( "click", function(theEvent){
    //               //element.tooltip( 'open' );
    //               // var term = element.text();
    //               var element = $( this );
    //               // var termID = element.attr( "data-docid" );
    //               // var docid = theEvent.originalEvent.path[0].dataset.docid;
    //             })
    //         // .off( "mouseover" )
    //         .attr( "title", "" ).css({ cursor: "pointer" });
    //     }
    // } );  // end function declaration
}); //end ready function
