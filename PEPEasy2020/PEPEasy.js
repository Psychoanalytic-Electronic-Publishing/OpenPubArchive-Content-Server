// PEP Easy Search
// Prototype/Demonstration of PEP-Web API v1
// Code: Neil R. Shapiro, scilab Inc.
// Version: .80
// +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
// Still to be done:
//
//   1) Needs to show matches. Currently a bug report
//   2) Maybe show the analyze function?
//   3) Tool tips on click rather than hover
// +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

// EDITED SLIGHTLY FOR TEST THE NEW SERVER - 2019-07-15

/*global ga*/
/*global window*/
/*global document*/
/*global console*/
/*global location*/
/*global $*/
/*global ko*/
/*global getCookie*/
/*global checkLoginStatus*/
/*global getSearchAnalysis*/
/*global loginToServer*/
/*global logoutFromServer*/
/*global setFontSize*/
/*global clearInterval*/
/*global setInterval*/
/*global setCookie*/
/*global decodeHtml*/
/*global deleteCookie*/
/*global getListOfcurrAuthorIndexData*/
/*global getListOfArticles*/
/*global getListOfMost*/
/*global getListOfSources*/
/*global getDocumentDownload*/
/*global getDocumentData*/
/*global getAbstract*/
/*global getAbstractWithCred*/
/*global fixedEncodeURIComponent*/
/*global setGlossaryStyle*/
/*global setJustifyStyle*/
/*global alert*/
/*global Sammy*/
/*global videoPEPCodesSearchSpec*/
/*global bookPEPCodesSearchSpec*/
/*global journalPEPCodeSearchSpec*/
/*exported openStart*/
/*exported showGlossaryModal*/
/*exported openTopMenu*/
/*exported openStart*/
/*exported openSearchTab*/
/*exported openStart*/
/*exported gotoArticleListTab*/
/*exported openAbstractTab*/
/*exported gotoOptionsDialog*/
/*exported gotoAboutPEPEasy*/
/*exported gotoHelpSearchDialog*/
/*exported gotoNewSearch*/
/*exported gotoSelectSortOrder*/

//###########################################################
//# Lookups that are not directly in index.html, in js code
//###########################################################
//Author-input.placeholder                                               = Enter the author to search for
//FullSet                                                                = (Max: {{virtualItemCount}})
//LogIn                                                                  = Log in
//LogOut                                                                 = Log out
//SearchListingIss                                                       = Listing for {{jrnlCode}} Vol {{jrnlVol}} Iss {{jrnlIss}}
//SearchListing                                                          = Listing for {{jrnlCode}} Vol {{jrnlVol}}
//Viewing                                                                = Items {{currItem}} to {{lastItem}} of {{itemCount}}
//Year-input.placeholder                                                 = Year or Range, e.g., 1970, <1980, >1980, or ^1960-1970

var snd1 = new Audio("data:audio/wav;base64,//uQRAAAAWMSLwUIYAAsYkXgoQwAEaYLWfkWgAI0wWs/ItAAAGDgYtAgAyN+QWaAAihwMWm4G8QQRDiMcCBcH3Cc+CDv/7xA4Tvh9Rz/y8QADBwMWgQAZG/ILNAARQ4GLTcDeIIIhxGOBAuD7hOfBB3/94gcJ3w+o5/5eIAIAAAVwWgQAVQ2ORaIQwEMAJiDg95G4nQL7mQVWI6GwRcfsZAcsKkJvxgxEjzFUgfHoSQ9Qq7KNwqHwuB13MA4a1q/DmBrHgPcmjiGoh//EwC5nGPEmS4RcfkVKOhJf+WOgoxJclFz3kgn//dBA+ya1GhurNn8zb//9NNutNuhz31f////9vt///z+IdAEAAAK4LQIAKobHItEIYCGAExBwe8jcToF9zIKrEdDYIuP2MgOWFSE34wYiR5iqQPj0JIeoVdlG4VD4XA67mAcNa1fhzA1jwHuTRxDUQ//iYBczjHiTJcIuPyKlHQkv/LHQUYkuSi57yQT//uggfZNajQ3Vmz+Zt//+mm3Wm3Q576v////+32///5/EOgAAADVghQAAAAA//uQZAUAB1WI0PZugAAAAAoQwAAAEk3nRd2qAAAAACiDgAAAAAAABCqEEQRLCgwpBGMlJkIz8jKhGvj4k6jzRnqasNKIeoh5gI7BJaC1A1AoNBjJgbyApVS4IDlZgDU5WUAxEKDNmmALHzZp0Fkz1FMTmGFl1FMEyodIavcCAUHDWrKAIA4aa2oCgILEBupZgHvAhEBcZ6joQBxS76AgccrFlczBvKLC0QI2cBoCFvfTDAo7eoOQInqDPBtvrDEZBNYN5xwNwxQRfw8ZQ5wQVLvO8OYU+mHvFLlDh05Mdg7BT6YrRPpCBznMB2r//xKJjyyOh+cImr2/4doscwD6neZjuZR4AgAABYAAAABy1xcdQtxYBYYZdifkUDgzzXaXn98Z0oi9ILU5mBjFANmRwlVJ3/6jYDAmxaiDG3/6xjQQCCKkRb/6kg/wW+kSJ5//rLobkLSiKmqP/0ikJuDaSaSf/6JiLYLEYnW/+kXg1WRVJL/9EmQ1YZIsv/6Qzwy5qk7/+tEU0nkls3/zIUMPKNX/6yZLf+kFgAfgGyLFAUwY//uQZAUABcd5UiNPVXAAAApAAAAAE0VZQKw9ISAAACgAAAAAVQIygIElVrFkBS+Jhi+EAuu+lKAkYUEIsmEAEoMeDmCETMvfSHTGkF5RWH7kz/ESHWPAq/kcCRhqBtMdokPdM7vil7RG98A2sc7zO6ZvTdM7pmOUAZTnJW+NXxqmd41dqJ6mLTXxrPpnV8avaIf5SvL7pndPvPpndJR9Kuu8fePvuiuhorgWjp7Mf/PRjxcFCPDkW31srioCExivv9lcwKEaHsf/7ow2Fl1T/9RkXgEhYElAoCLFtMArxwivDJJ+bR1HTKJdlEoTELCIqgEwVGSQ+hIm0NbK8WXcTEI0UPoa2NbG4y2K00JEWbZavJXkYaqo9CRHS55FcZTjKEk3NKoCYUnSQ0rWxrZbFKbKIhOKPZe1cJKzZSaQrIyULHDZmV5K4xySsDRKWOruanGtjLJXFEmwaIbDLX0hIPBUQPVFVkQkDoUNfSoDgQGKPekoxeGzA4DUvnn4bxzcZrtJyipKfPNy5w+9lnXwgqsiyHNeSVpemw4bWb9psYeq//uQZBoABQt4yMVxYAIAAAkQoAAAHvYpL5m6AAgAACXDAAAAD59jblTirQe9upFsmZbpMudy7Lz1X1DYsxOOSWpfPqNX2WqktK0DMvuGwlbNj44TleLPQ+Gsfb+GOWOKJoIrWb3cIMeeON6lz2umTqMXV8Mj30yWPpjoSa9ujK8SyeJP5y5mOW1D6hvLepeveEAEDo0mgCRClOEgANv3B9a6fikgUSu/DmAMATrGx7nng5p5iimPNZsfQLYB2sDLIkzRKZOHGAaUyDcpFBSLG9MCQALgAIgQs2YunOszLSAyQYPVC2YdGGeHD2dTdJk1pAHGAWDjnkcLKFymS3RQZTInzySoBwMG0QueC3gMsCEYxUqlrcxK6k1LQQcsmyYeQPdC2YfuGPASCBkcVMQQqpVJshui1tkXQJQV0OXGAZMXSOEEBRirXbVRQW7ugq7IM7rPWSZyDlM3IuNEkxzCOJ0ny2ThNkyRai1b6ev//3dzNGzNb//4uAvHT5sURcZCFcuKLhOFs8mLAAEAt4UWAAIABAAAAAB4qbHo0tIjVkUU//uQZAwABfSFz3ZqQAAAAAngwAAAE1HjMp2qAAAAACZDgAAAD5UkTE1UgZEUExqYynN1qZvqIOREEFmBcJQkwdxiFtw0qEOkGYfRDifBui9MQg4QAHAqWtAWHoCxu1Yf4VfWLPIM2mHDFsbQEVGwyqQoQcwnfHeIkNt9YnkiaS1oizycqJrx4KOQjahZxWbcZgztj2c49nKmkId44S71j0c8eV9yDK6uPRzx5X18eDvjvQ6yKo9ZSS6l//8elePK/Lf//IInrOF/FvDoADYAGBMGb7FtErm5MXMlmPAJQVgWta7Zx2go+8xJ0UiCb8LHHdftWyLJE0QIAIsI+UbXu67dZMjmgDGCGl1H+vpF4NSDckSIkk7Vd+sxEhBQMRU8j/12UIRhzSaUdQ+rQU5kGeFxm+hb1oh6pWWmv3uvmReDl0UnvtapVaIzo1jZbf/pD6ElLqSX+rUmOQNpJFa/r+sa4e/pBlAABoAAAAA3CUgShLdGIxsY7AUABPRrgCABdDuQ5GC7DqPQCgbbJUAoRSUj+NIEig0YfyWUho1VBBBA//uQZB4ABZx5zfMakeAAAAmwAAAAF5F3P0w9GtAAACfAAAAAwLhMDmAYWMgVEG1U0FIGCBgXBXAtfMH10000EEEEEECUBYln03TTTdNBDZopopYvrTTdNa325mImNg3TTPV9q3pmY0xoO6bv3r00y+IDGid/9aaaZTGMuj9mpu9Mpio1dXrr5HERTZSmqU36A3CumzN/9Robv/Xx4v9ijkSRSNLQhAWumap82WRSBUqXStV/YcS+XVLnSS+WLDroqArFkMEsAS+eWmrUzrO0oEmE40RlMZ5+ODIkAyKAGUwZ3mVKmcamcJnMW26MRPgUw6j+LkhyHGVGYjSUUKNpuJUQoOIAyDvEyG8S5yfK6dhZc0Tx1KI/gviKL6qvvFs1+bWtaz58uUNnryq6kt5RzOCkPWlVqVX2a/EEBUdU1KrXLf40GoiiFXK///qpoiDXrOgqDR38JB0bw7SoL+ZB9o1RCkQjQ2CBYZKd/+VJxZRRZlqSkKiws0WFxUyCwsKiMy7hUVFhIaCrNQsKkTIsLivwKKigsj8XYlwt/WKi2N4d//uQRCSAAjURNIHpMZBGYiaQPSYyAAABLAAAAAAAACWAAAAApUF/Mg+0aohSIRobBAsMlO//Kk4soosy1JSFRYWaLC4qZBYWFRGZdwqKiwkNBVmoWFSJkWFxX4FFRQWR+LsS4W/rFRb/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////VEFHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAU291bmRib3kuZGUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMjAwNGh0dHA6Ly93d3cuc291bmRib3kuZGUAAAAAAAAAACU=");

function beep() {
  snd1.play();
}

if (!window.console) {
  var noOp = function(){}; // no-op function
  console = {
    log: noOp,
    warn: noOp,
    error: noOp
  };
}

var accordions = {
  start: 0,
  // options : 1,
  search: 1,
  // articles : 2,
  abstract: 2
};

var _ = document.webL10n.get;

var sort_by = function(field, reverse, primer){
  var key = function (x) {return primer ? primer(x[field]) : x[field];};

  return function (a,b) {
    var A = key(a), B = key(b);
    return ( (A < B) ? -1 : ((A > B) ? 1 : 0) ) * [-1,1][+!!reverse];
  }
}

function scrollToAnchor(aid) {
  var aTag;
  try {
    aTag = $("a[name='" + aid + "']");
    $('html,body').animate({
      scrollTop: aTag.offset().top-100
    }, 'slow');
  } catch (err) {
    try {
      // console.log("ScrollTo: No matching a anchor: " + err);
      aTag = $("div[id='" + aid + "']");
      $('html,body').animate({
        scrollTop: aTag.offset().top
      }, 'slow');
    } catch (err) {
      beep();
      //console.warn("ScrollTo: No matching Div Name: " + err);
      ga('send', 'exception', {
        'exDescription': err.message,
        'exFatal': false
      });
    }
  }
}

function showGlossaryModal(termID) {
  // get glossary entry, store in currGlossaryEntryHTML
  window.vm.popupGlossaryBox(termID);
}

/* When the user clicks on the button,
   toggle between hiding and showing the dropdown content */
function openTopMenu() {
  // console.log("Open Top Menu");
  document.getElementById("topMenu").classList.toggle("show");
  //  console.log("menu opened");
  window.vm.loginStateMenuSet();
}

function doSearchAnalysis() {
  window.vm.doSearchAnalysis();
}

function closeTopMenu() {
  $("#topMenu").removeClass("show");
}

function openStart() {
  closeTopMenu();
  $("#accordion").accordion({
    active: accordions["start"]
  });
}

function openSearchTab() {
  closeTopMenu();
  $("#accordion").accordion({
    active: accordions["search"]
  });
}

// after a search, keep track of seeks to the next hit,
// which are marked by anchors in the return data.
var hitCursor = {
  currPosition: 0,
  endPosition: -1,
  hits: [],
  hitCount: 0,
  firstHit: null,
  hitTag: "",
  initialize: function () {
    // Make sure there's a hit to go to, otherwise we should disable
    this.hits = $('a[name^="hit"]');
    this.currPosition = 0;
    //    console.log(this.hits);
    this.hitCount = this.hits.length;
    this.endPosition = this.hitCount;
    //    console.log("# of hits: " + this.hitCount);
  },
  prevHit: function() {
    closeTopMenu();
    if (this.currPosition <= 1) {
      //console.log("No previous hit");
      // rescroll to current hit in case user has scrolled
      if (this.currPosition === 1) {
        this.hitTag = "hit" + this.currPosition;
        scrollToAnchor(this.hitTag);
      }
    }
    else {
      this.currPosition = this.currPosition - 1;
      this.hitTag = "hit" + this.currPosition;
      try {
        scrollToAnchor(this.hitTag);
      }
      catch(err) {
        console.warn("Can't find hit: " + this.hitTag + err);
      }
    }

    return false;
  },
  nextHit: function() {
    closeTopMenu();
    if (this.currPosition === this.endPosition) {
      console.warn("No next hit");
      // rescroll to current hit in case user has scrolled
      this.hitTag = "hit" + this.currPosition;
      scrollToAnchor(this.hitTag);
    }
    else {
      this.currPosition = this.currPosition + 1;
      this.hitTag = "hit" + this.currPosition;
      //console.log("Jump to " + this.hitTag);
      try {
        scrollToAnchor(this.hitTag);
      }
      catch(err) {
        console.warn("Can't find hit: " + this.hitTag + err);
      }
    }

    return false;
  }
};

function gotoArticleListTab() {
  closeTopMenu();
  $("#accordion").accordion({
    active: accordions["articles"]
  });
}

function openAbstractTab() {  // "Read" accordion tab
  closeTopMenu();
  $("#accordion").accordion({
    active: accordions["abstract"]
  });
}

function gotoOptionsDialog() {
  closeTopMenu();
  $("#optionsModal").modal('show');
}

function gotoFederationLoginDialog() {
  closeTopMenu();
  setCookie("federationLogin", true, 100);
  $("#federationLoginModal").modal('show');
//  checkLoginStatus(baseURL, window.vm.accessToken(), window.vm.loginStatusCallback);
//  if (window.vm.accessToken()) {
//    console.log("Back True!");
//  } else {
//    console.log("Back False!");
//  }
}

function gotoAboutPEPEasy() {
  closeTopMenu();
  $("#aboutPEPEasyModal").modal('show');
}

function gotoHelpSearchDialog() {
  ga('set', 'page', '/Search/Tips/');
  ga('send', 'pageview');
  closeTopMenu();
  $("#helpSearchSyntax").modal('show');
}

function gotoNewSearch() {
  location.hash = '/Search/';
}

function gotoSelectSortOrder() {
  closeTopMenu();
  $("#sortSelectionModal").modal('show');
}

/**
 * Figure out translated text for a retStatusMessageObject from server.
 *
 * @param {retStatusMessageObject} retStatusMessageObject The returnStatusMessage object from the server
 * @param {string} defaultID if retStatusMessageObject is null, lookup this ID and return the text
 * @returns {string} The translated string or "" if one not found
*/
function getStatusMessageObjectText(retStatusMessageObject, defaultID) {
  var retVal = "";
  if (retStatusMessageObject !== null) {
    var messageID = retStatusMessageObject.messageID;
    var description = retStatusMessageObject.description;
    if (messageID !== null && messageID !== "limited" && messageID !== "ajaxUncaught") {
      var msg = _(messageID);
      if (msg === "") {
        if (description !== "" && description !== null) {
          // show the untranslated description
          retVal = description;
        }
        else {
          // just show the id
          retVal = messageID;
        }
      } else {
        // show the translated message
        retVal = msg;
      }
    }
    else { // part of description at least will be from the server, in English
      retVal = description;
    }
  } else if (defaultID !== null && defaultID !== undefined) {
    retVal = _(defaultID);
  }

  return retVal;
}

// not sure what I was thinking with this...a kind of search/filter on the doc
//function filterFunction() {
//  var input, filter, ul, li, a, i, div;
//  input = document.getElementById("myInput");
//  filter = input.value.toUpperCase();
//  div = document.getElementById("myDropdown");
//  a = div.getElementsByTagName("a");
//  for (i = 0; i < a.length; i++) {
//    if (a[i].innerHTML.toUpperCase().indexOf(filter) > -1) {
//      a[i].style.display = "";
//    } else {
//      a[i].style.display = "none";
//    }
//  }
//}

$("form input").on('keyup', function (e) {
  if (e.keyCode == 13) {
    // Do something
    doSearchAnalysis();
  }
});

function PEPArticlesViewModel() {
  // Data
  // set KEEP_ALIVE_INTERVAL to the time where the client will send a wake up message to keep the connection alive
  // set CHECK_FOR_DISCONNECT to a time longer than the timeout, so the client can mark it's been disconnected.
  var KEEP_ALIVE_INTERVAL = 300; // 300 minutes (no real need to poll anymore, for now, just keep this high)
  var CHECK_FOR_DISCONNECT = 25; // 25 minutes (this should be a const, but unfort. that isn't supported everywhere).  I think we still need to poll to check if you are disconnected, because it's hard to handle the case where the interface thinks you are still logged in, but you are not.
  var self = this;
  var cookie;

  // To display current search "parameters" to user in interface
  //  var searchDisplayString = "";  // I think this can go and be used at local level now TBD
  // var lastSearchAPIString = "";

  self.journals = ko.observableArray([]); // list of journals for pull down in search fetched from server
  self.videos = ko.observableArray([]); // list of video sources, will be added to journals after fetching from server
  // not used, authors dynamically loaded
  //self.authors = ko.observableArray([]);

  self.isValidKWIC = ko.observable(false);
  // self.matchesNotFound = ko.observable(false);
  self.noMatchesFoundMessage = ko.observable("");

  // UI Display Objects
  self.articleList = ko.observableArray([]);

  // Abstract Area observable
  self.articleAbstract = ko.observable("");
  self.currAbstractDocumentID = ko.observable(""); // Last loaded abstract or document
  self.currDocumentID = ""; // last loaded document
  self.currGlossaryTermID = ko.observable("");
  self.currGlossaryEntryHTML = ko.observable("");

  // Welcome area lists
  self.currWhatsNewList = ko.observableArray([]);
  self.currMostCitedData = ko.observableArray([]);
  self.currMostDownloadedData = ko.observableArray([]);

  self.userName = ko.observable("");
  self.userPassword = ko.observable("");
  self.accessToken = ko.observable("");

  // self.matchCountSuffix = ko.observable(" articles");
  //self.offsetLimit = 0;
  // self.searchAdvancedQueryString = ko.observable();
  self.searchResultsLimit = ko.observable(15);
  // self.searchResultsIncrement = ko.observable(self.searchResultsLimit());
  self.searchResultsOffset = ko.observable(0);
  self.matchCount = ko.observable(0);

  // Search Fields
  self.searchTitleText = ko.observable("");
  self.searchAuthorText = ko.observable("");
  self.searchYearText = ko.observable("");
  self.searchDateTypeText = ko.observable("");
  self.searchWordsText = ko.observable("");
  self.queryString = ko.observable("");
  self.searchJournal = ko.observable("All");
  self.searchVolume = ko.observable("");
  self.searchIssue = ko.observable("");
  self.searchAnalysisArray = ko.observableArray([]);
  self.searchAnalysisPending = false;
  self.searchAnalysisClearPending = false;

  // Sharingbutton link info currently disabled
  //  var socialLinks = {
  //    facebook: "https://facebook.com/sharer/sharer.php?u=http%3A%2F%2Fwww.pep-web.org",
  //    twitter: "https://twitter.com/intent/tweet/?text=Interesting%20information%20on%20PEP-Web&amp;url=http%3A%2F%2Fwww.pep-web.org",
  //    mailTo: "mailto:?subject=Interesting%20information%20on%20PEP-Web&amp;body=http%3A%2F%2Fwww.pep-web.org"
  //  }

  self.facebookLink = ko.observable("");
  self.twitterLink = ko.observable("");
  self.mailtoLink = ko.observable("");
  self.journalFieldPlaceholder = "testing 1 2 3";

  // Options Settings
  self.selectedFontSize = ko.observable("1.5");
  self.selectedReturnSetSize = ko.observable(parseInt(getCookie("returnSetSize", "25")));

  self.searchSortOrder = ko.observable("rank");
  self.searchSortOrder(getCookie("sortOrder", "rank"));
  self.showRanks = ko.observable(false); // only show ranks for full-text search

  self.skipAbstractMode = ko.observable(getCookie("skipAbstractMode", "false") === "true");  // comparison evaluates to true/false
  //self.skipAbstractMode(true);  // for testing only...
  //console.log("Skip Abstract Mode is " + self.skipAbstractMode());

  self.showTermMatchesinCompactView = ko.observable(false);

  // self.pauseSearchAnalysis = false;
  self.showKWIC = ko.observable(false);
  if (getCookie("showKWIC") === "true") {
    self.showKWIC(true);
  } else {
    self.showKWIC(false);
  }

  // self.currentSearchString = ko.observable("");
  self.lastServerSearchString = ko.observable(""); // used to send the search string to the Document API request so hits are marked.
  self.currentSearchDisplayString = ko.observable("");
  self.currentSearchProgress = ko.observable("");

  // ********************************************************************
  // state check timer variables and constants
  // now stay logged in FALSE is the default.  When you log in, if you check
  // stay logged in on the dialog, then you will not get timed out.
  self.stayLoggedIn = ko.observable(false);

  //  console.log("Stay Logged In option loaded: " + self.stayLoggedIn());
  //  self.keepAliveTimerID = null;
  // if user opts to keep alive, then use KEEP_ALIVE_INTERVAL instead
  self.loginStateCheckInterval = CHECK_FOR_DISCONNECT;
  // ********************************************************************

  self.loginMenuState = ko.observable("");

  //  self.statusMessage = ko.observable("...Ready!...");
  self.statusMessageLocal = ko.observable(""); // Used for server status in calls to getListOfMost - eventually switch to callback TBD
  self.selectedStyleSheet = ko.observable("");
  self.extendedLoginStatus = ko.observable("");
  self.lastAction = ""; // used to resume an action which was interrupted because user was not logged in
  self.requestedHTMLAnchor = ""; // if set, when an HTML doc is loaded, will try to scroll to this anchor

  self.loggedInToServerObs = ko.observable();
  self.readModeIsDocument = ko.observable(false);
  //self.federationLogin = false;  // if the user tried to login via federation login
  //self.federationLoggedInSuccess = false; // the user tried to login via federation and it worked.

  self.getStoredAccessToken = function () {
    var token;
    token = getCookie("PHPSESSID");
    if (token !== "") {
      self.accessToken(token);
    } else {
      self.accessToken("");
    }
  };

  // experimental
  self.quickSearchTypeWords = ko.observable(false); // if true, the default short search form is Words

  self.compactSearchModeSelected = ko.observable(getCookie("compactSearchModeSelected", "titleAuthorWords"));

  if (getCookie("showFullSearchForm") === "true") {
    self.showFullSearchForm = true;
  } else {
    self.showFullSearchForm = false;
  }
  // experimental, Paul's suggested way of searching.
  self.broadenSearch = ko.observable(false);
  if (getCookie("broadenSearch") === "true") {
    self.broadenSearch(true);
  } else {
    self.broadenSearch(false);
  }


  // ********************************************************************************************
  // Login management
  //  - must be at top of most other functions, since at the end, it checks for a sessions IF
  //     and declares loggedInToServerObs
  // ********************************************************************************************

  self.currentStatusLine = ko.computed(function () {
    var retVal = "";
    if (self.loggedInToServerObs() === true) {
      if (self.readModeIsDocument() === true) {
        // viewing a document, customize message
        retVal = "This is the full document.";
      } else {
        // viewing an abstract, customize message
        retVal = "You are logged in and have access to full text to all articles other than the newer embargoed ones.";
      }
    } else {
      // not logged in
      retVal = "You are not logged in.  You must be logged in to read or download full-text."; //login link is in index.html
    }
    return retVal;
  }, this);

  self.login = function () {
    if (self.loggedInToServerObs() !== true) {
      //console.log("Apparently, not logged in, so opening login dialog.");
      $("#loginModal").modal('show');
    } else {
      alert("You are already logged in.");
    }
  };

  self.acceptCredentials = function (data) {
    // apiCall = baseURL + "/v1/Token?grant_type=password&username=zzz&password=yyyy";
    // login, now include boolean value whether the user has elected to stay logged in
    // we may still need a way to log out and have the server delete the token it saves.
    loginToServer(baseURL, self.userName(), self.userPassword(), self.loginToServerStatusCallback, self.stayLoggedIn());
    $("#loginModal").modal('hide');
  };

  // call back for actual login, not the check
  self.loginToServerStatusCallback = function (status, msg, statusCode, accessToken) {
    // Check caller response
    if (status === false) {
      console.warn("Login Failed: " + msg);
      ga('set', 'page', '/Login/Fail/');
      ga('send', 'pageview');
      //alert(msg.error_description);
      self.loggedInToServerObs(false);
      self.accessToken("");
      // XXX Should we say this here, or revert to info about abstract?  XXX
      self.extendedLoginStatus(msg.error_description);

      // not logged in, cancel timer
      if (self.intervalID !== null) {
        clearInterval(self.intervalID);
        self.intervalID = null;
      }
    } else {
      //console.log("Login succeeded: " + msg);
      // XXX we need to set this up for translation, and decide what's best to say here! XXX
      ga('set', 'page', '/Login/Success/');
      ga('send', 'pageview');

      self.extendedLoginStatus(_("jsStatusLoggedIn"));
      self.loggedInToServerObs(true);
      self.accessToken(accessToken);
      self.createHearbeatTimer();
    }
    // set menu appropriately (either case)
    self.loginStateMenuSet(); // update menu
  }; // loginToServerStatusCallback

  self.createHearbeatTimer = function () {
    var selectedHeartbeatTime;
    if (self.stayLoggedIn()) {
      // no need to poll anymore, ka option takes care of connection.
      selectedHeartbeatTime = KEEP_ALIVE_INTERVAL;
    } else {
      selectedHeartbeatTime = CHECK_FOR_DISCONNECT;
    }

    self.loginStateCheckInterval = selectedHeartbeatTime * 1000 * 60;
//    console.log("Heartbeat timer will be set to: " + selectedHeartbeatTime + " minutes. " + self.loginStateCheckInterval + " is time setting.");

    // clear any existing timer
    if (self.intervalID !== null) {
      clearInterval(self.intervalID);
    }
    // create the new timer
    self.intervalID = setInterval(function () {
      // Put keepalive function here!
      self.getCurrentLoginStatus();
      // for now, show it's working
      // if we want to log the time
        //      var d = new Date();
        //      var t = d.toLocaleTimeString();
        //      console.log("Checked Login State at " + t);

    }, self.loginStateCheckInterval); // check more frequently than timeout, that keeps alive!
  }

  self.getCurrentLoginStatus = function () {
    // Check with server if logged in or if IPLogin is active

    if (self.accessToken() === "" && self.accessToken() !== "IPLogin") {
      self.getStoredAccessToken();
    }
    // now check again, if not empty, check login status
    if (self.accessToken() !== "") {
      // call pepwebapi function library to check status
      checkLoginStatus(baseURL, self.accessToken(), self.loginStatusCallback);
    }
//    } else {
//      // not logged in
//      // console.log("No session token, not logged in.");
//      self.loggedInToServerObs(false);
//    }
  };

  self.loginStatusCallback = function (loggedInToServer, statusMessage) {
    self.loggedInToServerObs(loggedInToServer);
    if (loggedInToServer === false) {
      //console.log("StatusCallback - Not logged in! " + statusMessage);
      deleteCookie("federationLogin");
      deleteCookie("federationLoggedInSuccess");
      self.showReadandDownloadButtons(false);
      // not logged in, cancel timer
      if (self.intervalID !== null) {
        clearInterval(self.intervalID);
        self.intervalID = null;
      }
    } else { // logged in
      //console.log("StatusCallback - Logged in! " + statusMessage);
      //self.showReadandDownloadButtons(true);
      if (self.accessToken() === "") {
        if (getCookie("federationLogin") === "true") {
          setCookie("federationLoggedInSuccess", true, 100);
          deleteCookie("federationLogin");  // now we know we're logged in
          //console.log("Login Success");
          console.log("Federation IPLogin");
        }
        // if we're not logged in via token, then it must be via IP authentication
        self.accessToken("IPLogin");
        console.log("IPLogin");
      }
    }
  };

  //self.getCurrentLoginStatusAndLogin = function() {

  //if (self.loggedInToServerObs() === false) {
  //console.log("We need to log you in!");
  //self.login();
  //}

  //}

  self.showReadandDownloadButtons = function (showButtons) {
    if (self.loggedInToServerObs() !== true) {
      $('#authenticatedButtonFunctions').hide();
      //console.log("Hiding buttons inner");

    } else {
      if (showButtons === true) {
          $('#authenticatedButtonFunctions').show();
//          console.log("Showing buttons inner");
        } else {
          $('#authenticatedButtonFunctions').hide();
//          console.log("Hiding buttons inner");
        }
    }
  };


  self.loginStateMenuSet = function () {
    var retVal;
    //self.showReadandDownloadButtons(self.loggedInToServer);
    if (self.loggedInToServerObs() === false) {
      self.loginMenuState(_("jsLogIn"));
      self.accessToken("");
      retVal = false;
    } else {
      if (getCookie("federationLoggedInSuccess") !== true) {
        if (self.accessToken() === "IPLogin") {
          self.loginMenuState(_("jsLoginViaIP"));
        } else {
          self.loginMenuState(_("jsLogOut"));
        }
      } else {
        if (self.accessToken() === "IPLogin") {
          self.loginMenuState("LoggedInFederation");
        } else {
          self.loginMenuState(_("jsLogOut"));
        }
      }
      retVal = true;
    }

    return retVal;
  };

  self.logoutFromServerCallback = function (status, msg) {
      console.log("Log out acknowledged by server. " + msg);
      deleteCookie("federationLogin");
      deleteCookie("federationLoggedInSuccess");
  }

  self.loginStateToggle = function () {
    closeTopMenu();
    if (self.accessToken() !== "IPLogin") {  // only do this if not IP logged in
      if (self.loggedInToServerObs() === true) {
        // user wants to log out.
        deleteCookie("PHPSESSID");
        self.accessToken("");
        self.extendedLoginStatus(_("jsStatusNotLoggedIn"));
        self.loggedInToServerObs(false);
        logoutFromServer(baseURL, self.logoutFromServerCallback, self.stayLoggedIn());
      } else {
        // user is not logged in
        self.login();
      }
    }
  };

  // initial check for login state, e.g., after a refresh.  See if we already have a token stored, and check if it's valid
  self.getStoredAccessToken();
  checkLoginStatus(baseURL, self.accessToken(), self.loginStatusCallback);

//  if (self.accessToken() !== "") {
//    checkLoginStatus(baseURL, self.accessToken(), self.loginStatusCallback);
//  } else {
//    self.loggedInToServerObs(false);
//  }

  // ********************************************************************************************
  // END Login management
  // ********************************************************************************************

  self.closeModals = function () {
    $("#ftnModal").modal('hide');
    $("#refModal").modal('hide');
  }


  self.changeShowStateObjects = function (chosenState) {
    if (typeof chosenState !== 'undefined') {
      self.showFullSearchForm = chosenState;
    } else {
      self.showFullSearchForm = !self.showFullSearchForm;
    }

    if (self.showFullSearchForm === true) { // verbose form
      $(".searchFormFields").show(); // all fields
      $("#termMatchStatArea").show(); // stats too
      // change button to More (+)
      $(".criteriaMore").hide();
      $(".criteriaLess").show();
    } else { // compact form
      // first hide
      $("#termMatchStatArea").hide();
      $(".searchFormFields").hide();

      // now selectively show

      if (self.compactSearchModeSelected() === "authorWordsSearch") {
        $(".searchAuthorField").show();
        $(".searchWordsField").show();
        if (self.showTermMatchesinCompactView()) {
          $("#termMatchStatArea").show();
        }
      } else if (self.compactSearchModeSelected() === "wordsJournalSearch") {
        $(".searchWordsField").show();
        $(".searchJournalField").show();
        if (self.showTermMatchesinCompactView()) {
          $("#termMatchStatArea").show();
        }
      } else if (self.compactSearchModeSelected() === "authorTitleSearch") {
        $(".searchAuthorField").show();
        $(".searchTitleField").show();
      } else if (self.compactSearchModeSelected() === "wordsSearch") {
        $(".searchWordsField").show();
        $("#termMatchStatArea").show();
      } else { //if (self.compactSearchModeSelected() === "authorTitleWordsSearch") {
        $(".searchAuthorField").show();
        $(".searchTitleField").show();
        $(".searchWordsField").show();
        if (self.showTermMatchesinCompactView()) {
          $("#termMatchStatArea").show();
        }
      }

      // change button to Less (-)
      $(".criteriaMore").show();
      $(".criteriaLess").hide();
    }
    return;
  };

  self.changeShowStateObjects(self.showFullSearchForm);

  self.changedquickSearchTypeWords = function () {
    // Toggle the showKWIC variable which determines whether or not to show the KWIC
    setCookie("quickSearchTypeWords", self.quickSearchTypeWords(), 100);
    // don't invert state, just update display
    self.changeShowStateObjects(self.showFullSearchForm);
    return true;
  };

  // user options (defaults)
  self.showGlossaryTerms = ko.observable(); // follows user's option checkmark
  self.justifyText = ko.observable(); // follows user's option checkmark

  self.indexResults = {
    currAuthorIndexData: ko.observableArray([]),
    currMatchText: ko.observable(),
    limit: 15,
    // currauthorIndexLen: ko.observable(),
    // curPos: 0,
    // offset: 15,
    // maxPos: 99999
  };

  self.matchIndex = function (value) {
    //var limitStr;
    var apiURL;
    if (value.length > 3) {
      if (value != self.searchAuthorText()) {
        self.searchAuthorText(value);
        // self.indexResults.curPos = 0;
      }

      //limitStr = limitClauseStr(self.indexResults);
      apiURL = baseURL + "/v1/Authors/Index/" + self.searchAuthorText() + "?limit=" + self.indexResults.limit;
      self.indexResults.currAuthorIndexData([]);
      getListOfcurrAuthorIndexData(apiURL, self.indexResults.currAuthorIndexData);
    }
  };

  self.searchAuthorText.subscribe(self.matchIndex);

  // var currLanguage = document.webL10n.getLanguage();
  //console.log("Localization is: " + document.documentElement.lang);
  // document.webL10n.setLanguage("en-us");
  //check for navigation time API support
  self.selectedLanguage = ko.observable(getCookie("language", document.documentElement.lang)); // we may not know the language if it's just the user's settings.

  self.showGlossaryTerms(setGlossaryStyle("cookie"));
  self.justifyText(setJustifyStyle("cookie"));

  self.getSearchStringFromForm = function () {
    // Form the API and Display search strings, from the search form (not the URL)
    var searchStr = "";
    var searchYearTextString;
    var searchYearTextStringStart = "";
    // Load journals, books, videos from server call
    var marker = "?";
    var searchDisplayString = ""; // really no longer need to build a display string since the analysis does it.

    if (self.searchAuthorText() !== "") {
      if (self.searchAuthorText().indexOf(",") !== -1 && self.searchAuthorText().indexOf('"') === -1) {
        // put quotes around it
        searchStr = marker + "author=" + '"' + self.searchAuthorText() + '"';
        //console.log(searchStr);
      } else {
        searchStr = marker + "author=" + self.searchAuthorText(); // allow root
      }
      if (self.broadenSearch() === true && self.searchAuthorText().substr(self.searchAuthorText().length - 1) !== "*") {
        // change all end of words to * per email from Paul 2017-11-27
        searchStr = searchStr.replace(/([\S]+(?=[ ]|$))/g, "$1*");
        searchStr = searchStr.replace(/(\*{2,6})/g, "*");

      }

      marker = "&";
      // searchDisplayString += "<span class=\"criteriaLabel\">Author(s):</span>" + self.searchAuthorText() + " ";
    }

    if (self.searchTitleText() !== "") {
      searchStr = searchStr + marker + "title=" + self.searchTitleText();
      // change all end of words to * per email from Paul 2017-11-27
      if (self.broadenSearch() === true && self.searchTitleText().substr(self.searchTitleText().length - 1) !== "*") {
        searchStr = searchStr.replace(/([\S]+(?=[ ]|$))/g, "$1*");
        searchStr = searchStr.replace(/(\*{2,6})/g, "*");
      }
      marker = "&";
      // searchDisplayString += "<span class=\"criteriaLabel\">Title:</span>" + self.searchTitleText() + " ";
    }

    if (self.searchJournal() === undefined) {
      self.searchJournal("All");
    }

    if (self.searchJournal() !== "All" && self.searchJournal() !== undefined) {
      searchStr = searchStr + marker + "journal=" + self.searchJournal();
      marker = "&";
    }

    if (self.searchYearText() !== "") {
      var d = new Date();
      var n = d.getFullYear() + 1;
      searchYearTextString = self.searchYearText();
      searchYearTextStringStart = "";
      var searchYearTextStringEnd = "";
      // Javascript switch statement ... seems to switch to Pythonic syntax!
      switch (searchYearTextString.substring(0, 1)) {
        case "^": // Between
          self.searchDateTypeText("Between");
          var searchYearTextStringArr = searchYearTextString.split("-");
          searchYearTextStringStart = searchYearTextStringArr[0];
          searchYearTextStringStart = searchYearTextStringStart.substring(1);
          searchYearTextStringEnd = searchYearTextStringArr[1];
          searchDisplayString += "<span class=\"criteriaLabel\">Date Between:</span>" + searchYearTextString + " ";
          break;

        case ">": // After
          self.searchDateTypeText("Since");
          searchYearTextStringStart = searchYearTextString.substring(1);
          searchDisplayString += "<span class=\"criteriaLabel\">Date After:</span>" + searchYearTextString + " ";
          searchYearTextStringEnd = n;
          break;

        case "<": // Before
          self.searchDateTypeText("Before");
          searchYearTextStringStart = searchYearTextString.substring(1);
          searchDisplayString += "<span class=\"criteriaLabel\">Date Before:</span>" + searchYearTextString + " ";
          break;

        default:
          self.searchDateTypeText("On");
          searchYearTextStringStart = searchYearTextString;
          searchDisplayString += "<span class=\"criteriaLabel\">Date On:</span>" + searchYearTextString + " ";

      }

      searchStr = searchStr + marker + "datetype=" + self.searchDateTypeText() + "&startyear=" + searchYearTextStringStart + "&endyear=" + searchYearTextStringEnd;
      marker = "&";
    }

    if (self.searchWordsText() !== "") {
      searchStr = searchStr + marker + "fulltext1=" + self.searchWordsText();
      searchDisplayString += "<span class=\"criteriaLabel\">Words or phrases:</span>" + self.searchWordsText() + " ";
      marker = "&";
    }


    if (searchStr !== "") {
      searchStr += "&sort=" + self.searchSortOrder();
    }

    return {
      searchString: searchStr,
      displayString: searchDisplayString
    };
  };

  self.searchAnalysisComplete = function () {
    self.searchAnalysisPending = false;
    if (self.searchAnalysisClearPending === true) {
      self.searchAnalysisArray([]);
      self.searchAnalysisClearPending = false;
    }
  };

  self.doSearchAnalysis = function () {
    var searchStrObj = self.getSearchStringFromForm();
    var searchStr = searchStrObj["searchString"];
    var apiCall = "/v1/Database/SearchAnalysis/" + searchStr;
    self.searchAnalysisPending = true;
    getSearchAnalysis(baseURL + apiCall, self.searchAnalysisArray, self.searchAnalysisComplete);
  };


  //*********************************************************************************************************************
  function articleListPager() {
    var pagerSelf = this; // save original this reference (to object), use it within the functions to refer to "self"
    this.currentArticleListHash = location.hash; //string
    this.baseAPIRequest = ""; // string request without paging options
    this.currItemNumber = 0; // integer zero based - keep it integer
    this.limit = 25; // integer setSize - keep limit integer
    this.lastItemNumber = 0; //integer Last item in this set
    this.pageEndItemNumber = 0; // integer = currItemNumber + pageOffset
    this.availableItemCount = 0; // total possible items, some may not be possible to view
    this.fullCountComplete = false;
    this.fullCount = 0;
    this.responseInfo = ko.observable();
    this.displayString = ko.observable("");
    this.lastSearchAPIString = "";

    this.pageSize = ko.computed(function () {
      setCookie("returnSetSize", self.selectedReturnSetSize(), 100);
      pagerSelf.limit = parseInt(self.selectedReturnSetSize());
      return self.selectedReturnSetSize(); // string
    }, this);

    this.currPageNumber = ko.computed(function () {
      var currPageNumber = Math.floor(pagerSelf.currItemNumber / pagerSelf.limit);
      return currPageNumber;
    }, this);

    this.searchResultsArea = ko.computed(function () {
      var lenArea = self.articleList().length;
      // if val == 0, then hide stuff
      if (lenArea === 0) {
        // console.log("Hiding" + self.matchCount());
        $("#searchFormResults").hide();
        $("#articleListLeadin").hide();
      } else {
        $("#searchFormResults").show();
        $("#articleListLeadin").show();
        // console.log("showing:'" + self.matchCount() + "'");
      }
    }, this);

    this.searchFinishedCallback = function (responseInfoObject) {
      pagerSelf.availableItemCount = responseInfoObject.fullCount;
      if (responseInfoObject.fullCount === 0) {
        self.noMatchesFoundMessage(_("jsNoMatches"));
      } else {
        self.noMatchesFoundMessage("");
      }
      pagerSelf.availableCountCompleteBool = responseInfoObject.fullCountComplete;
      pagerSelf.virtualItemCount = responseInfoObject.totalMatchCount;
      pagerSelf.currItemNumber = responseInfoObject.offset;
      self.searchResultsOffset(pagerSelf.currItemNumber);

      // var currItemNumberInt = parseInt(pagerSelf.currItemNumber) + 1;
      // var lastItemNumberInt = Math.min(pagerSelf.lastItemNumber + 1, pagerSelf.availableItemCount);

      self.currentSearchProgress("");
      pagerSelf.displayString();
      // var displayString = "<span data-l10n-id='Viewing-items'>Viewing items</span> " + currItemNumberInt +
      // " <span data-l10n-id='through'>through</span> " + lastItemNumberInt + " <span data-l10n-id='of'>of</span> " + pagerSelf.availableItemCount;

      var displayString = _('jsViewing', {
        currItem: parseInt(pagerSelf.currItemNumber) + 1,
        lastItem: Math.min(pagerSelf.lastItemNumber + 1, pagerSelf.availableItemCount),
        itemCount: pagerSelf.availableItemCount
      });

      if (!pagerSelf.availableCountCompleteBool) {
        displayString += " " + _("jsFullSet", {
          virtualItemCount: parseInt(pagerSelf.virtualItemCount)
        });
      }

      if (displayString !== "{{jsViewing}}") {
        pagerSelf.displayString(displayString);
      }

//      var ListingForStr = _('jsSearchListingIss', {
//        jrnlCode: parseInt(pagerSelf.currItemNumber) + 1,
//        jrnlVol: Math.min(pagerSelf.lastItemNumber + 1, pagerSelf.availableItemCount),
//        jrnlIss: pagerSelf.availableItemCount
//      });

      // console.log("Search finished.  " + pagerSelf.displayString());
      self.isValidKWIC(responseInfoObject.hasKWIC);
      self.fixKWICdisplay();
    };

    this.init = function (apiCall, startNumber, setSize) {
      pagerSelf.baseAPIRequest = apiCall;
      if (typeof startNumber === 'undefined') {
        pagerSelf.currItemNumber = 0;
      } else {
        pagerSelf.currItemNumber = parseInt(startNumber);
      }

      if (typeof setSize !== 'undefined') {
        pagerSelf.limit = parseInt(setSize);
      }

      if (apiCall !== pagerSelf.lastSearchAPIString) {
        pagerSelf.currItemNumber = 0;
        // self.articleList([]);
        pagerSelf.lastSearchAPIString = apiCall;
      }

      pagerSelf.lastItemNumber = pagerSelf.currItemNumber + pagerSelf.limit - 1; // Last item in this set
      // console.log("initializing pager: hash:" + pagerSelf.currentArticleListHash + " item: " + pagerSelf.currItemNumber + " last:" + pagerSelf.lastItemNumber);
      var fullAPICall = apiCall + "&limit=" + pagerSelf.limit + "&offset=" + pagerSelf.currItemNumber;
      self.articleList([]);
      pagerSelf.currentArticleListHash = location.hash;
      self.currentSearchProgress("Please wait...Fetching article list...");
      getListOfArticles(fullAPICall, self.articleList, pagerSelf.searchFinishedCallback);
    };

    this.showPage = function () {
      // Go ahead with the search
      // location.hash = '/Search/' + searchStr;
      // remove option and limit from location.hash
      // pagerSelf.currentArticleListHash = location.hash
      //console.log("Watch out for hash here: " + pagerSelf.currentArticleListHash);
      pagerSelf.currentArticleListHash = pagerSelf.currentArticleListHash.replace(/&limit=[0-9]+/g, "");
      pagerSelf.currentArticleListHash = pagerSelf.currentArticleListHash.replace(/&offset=.*[0-9]+/g, "");
      location.hash = pagerSelf.currentArticleListHash +
        "&limit=" + pagerSelf.pageSize() + "&offset=" + pagerSelf.currItemNumber;
      // sammy does the work with the local route
      return true;
    };

    // this.displayPageSize = function () {
    //   console.log(pagerSelf.pageSize() + "is the page size");
    // }

    this.goToNextPage = function () {
      var pageIncrem = parseInt(self.selectedReturnSetSize());
      var pageOffset = parseInt(pagerSelf.currItemNumber) + pageIncrem;

      if (pageOffset + pageIncrem > pagerSelf.availableItemCount) {
        pageOffset = Math.max(pagerSelf.availableItemCount - pageIncrem, 0);
      }

      pagerSelf.currItemNumber = pageOffset;
      self.searchResultsOffset(pageOffset);
      pagerSelf.showPage();
      return false;
    };

    this.goToPrevPage = function () {
      var pageIncrem = parseInt(self.selectedReturnSetSize());
      var pageOffset = parseInt(pagerSelf.currItemNumber) - pageIncrem;
      if (pageOffset < 0) {
        pageOffset = 0;
      }

      pagerSelf.currItemNumber = pageOffset;
      self.searchResultsOffset(pageOffset);
      var active = $('.accordion').accordion('option', 'active');
      // console.log("Active Accordion:" + active);
      pagerSelf.showPage();
      return false;
    };

  } // end of articleListPager Object
  // *********************************************************************************************

  self.articleListPager1 = new articleListPager();

  // ********************************************************************************************
  // Behaviours
  // ********************************************************************************************
  // allow search form to fold and expand
  self.expandSearchForm = function () {
    // toggle and update display
    self.changeShowStateObjects(!self.showFullSearchForm);
    setCookie("showFullSearchForm", self.showFullSearchForm, 100);
    //console.log("Setting showFullSearchForm cookie: " + self.showFullSearchForm);
    return;
  };

  // ********************************************************************************************
  // KWIC display (hits in context)
  // ********************************************************************************************
  self.fixKWICdisplay = function () {
    if (self.showKWIC() === false) {
      $(".kwicList").hide();
      // self.showKWIC(false);
    } else {
      $(".kwicList").show();
      // self.showKWIC(true);
    }
    return;
  };

  self.toggleKWIC = ko.computed(function () {
    // hide or show the KWIC list (matches in the hit list)
    if (self.showKWIC() === false) {
      $(".kwicList").hide();
      // self.showKWIC(false);
    } else {
      $(".kwicList").show();
      // self.showKWIC(true);
    }
    return;
  }, this);

  self.toggleKWICCheck = function () {
    // Toggle the showKWIC variable which determines whether or not to show the KWIC
    self.showKWIC(!self.showKWIC());
    setCookie("showKWIC", self.showKWIC(), 100);
  };

  // ********************************************************************************************
  // options Callbacks
  // ********************************************************************************************
  self.fontSizeChanged = function () {
    setFontSize(self.selectedFontSize());
    // need to set cookie TBD!
  };


  // ********************************************************************************************
  // Utility functions
  // ********************************************************************************************
  self.getAbstractCallback = function (statusMessageObj, documentID, abstractObject) {
    if (abstractObject === null) {
      // there was an error, the abstract  wasn't loaded.  Put error message in abstract area
      self.articleAbstract("Abstract not found.");
      // TBD
    } else {
      // we have a new abstract
      self.currAbstractDocumentID(documentID);
      self.currDocumentID = ""; // no document is currently loaded, just an abstract
      //  XXX Important XXX - in the future, we want the access limited description to come back with an abstract,
      //  but at this time it only comes back with the limited document.
      //var accessLimitedDescription = abstractObject.accessLimitedDescription;
      self.articleAbstract(abstractObject.abstract);
    }
    if (abstractObject.accessLimited === false) {
      self.showReadandDownloadButtons(true);
//      console.log("Showing buttons");
    }
    else {
      self.showReadandDownloadButtons(false);
      //console.log("Hiding buttons");
    }
    // temporary, to show Michael
    self.getCurrentLoginStatus();
    //    console.log("Server: ", baseURL);
    //    console.log("Logged in: " + self.loggedInToServerObs());
    //    console.log("accesslimited: " + abstractObject.accessLimited);
    //    console.log("CurrentContent: " + abstractObject.accessLimitedCurrentContent);
    //console.log("Reason: " + abstractObject.accessLimitedReason);
    //console.log("Descript: " + abstractObject.accessLimitedDescription);

    self.extendedLoginStatus("");
    if (statusMessageObj !== null) {
      self.extendedLoginStatus(statusMessageObj.description);
    } else {
        if (abstractObject.accessLimitedDescription !== undefined && abstractObject.accessLimited === true) {
          self.extendedLoginStatus(abstractObject.accessLimitedDescription);
        } else {
          if (abstractObject.accessLimitedReason !== undefined && abstractObject.accessLimited === true) {
            self.extendedLoginStatus(abstractObject.accessLimitedReason);
          }
        }
    }
  };

  self.sourcesLoadedCallback = function (srcArray, status) {
    // videos now loaded
    // console.log("PreMerging: " + self.journals().length);
    //self.journals(self.journals().concat(self.videos()));
    //        self.journals(self.journals().concat("All Videos"));
    //self.journals(self.journals().concat("All Books"));
    //http://stage.pep.gvpi.net/api/v1/Database/SearchAnalysis/?journal=afcvs+or+bpsivs+or+ijpvs+or+ipsavs+or+nypsivs+or+pcvs+or+pepgrantvs+or+peptopauthvs+or+pepvs+or+sfcpvs+or+spivs+or+uclvs
    //    console.log("Pushing Video List onto Journal (source) list")
//    self.journals().push({
//      sourceType: "Videos",
//      title: "All Videos",
//      PEPCode: "afcvs+or+bpsivs+or+ijpvs+or+ipsavs+or+nypsivs+or+pcvs+or+pepgrantvs+or+peptopauthvs+or+pepvs+or+sfcpvs+or+spivs+or+uclvs",
//      volume: null,
//      //contentsAPIURL: contentsAPIURL,
//      // volListURL: volListURL,
//      documentID: null,
//      issn: null,
//      isbn: null
//    });
    //console.log("Sources Loaded Callback" + _("jsAllVideos"));

    self.journals.sort(sort_by('title', true, function(a){return a.toUpperCase()}));

    // can translate here, but it's unreliable for some reason
    self.journals.unshift({
      sourceType: "Videos",
      //      title: _("jsAllVideos"),
      title: "All Videos",
      PEPCode: videoPEPCodesSearchSpec,
      volume: null,
      //contentsAPIURL: contentsAPIURL,
      // volListURL: volListURL,
      documentID: null,
      issn: null,
      isbn: null
    });

    self.journals.unshift({
      // title: _("jsAllJournals"),
      sourceType: "Journals",
      title: "All Journals",
      PEPCode: journalPEPCodeSearchSpec,
      volume: null,
      documentID: null,
      issn: null,
      isbn: null
    });

    self.journals.unshift({
      sourceType: "Books",
      title: "All Books",
      PEPCode: bookPEPCodesSearchSpec,
      volume: null,
      documentID: null,
      issn: null,
      isbn: null
    });

    self.journals.unshift({
      // title: _("jsAllSources"),
      title: "All Sources",
      PEPCode: "All"
    });

    // console.log("Merging 1: " + self.journals().length);
  };

  self.popupGlossaryBox = function (glossaryID) {
    // console.log("Showing glossary entry for " + glossaryID);
    // get glossary entry, store in currGlossaryEntryHTML
    self.currGlossaryTermID(glossaryID);

    if (self.loggedInToServerObs() === true) {
      ga('set', 'page', '/Glossary/' + self.currGlossaryTermID());
      ga('send', 'pageview');
      $("#glossayModal").modal('show');
      self.currGlossaryEntryHTML(_("jsLoadingGlossaryEntry"));
      //var apiCall = baseURL + "/v1/Documents/" + self.currGlossaryTermID() + "/";
      getDocumentData(self.currGlossaryTermID(), self.accessToken(), self.glossaryEntryHTMLCallback);
    } else {
      // do nothing...you must be logged in.  Render glossary links inactive.
      alert(_("jsMustBeLoggedInGlossary"));
    }
  };

  // self.gotoStart = function(data) {
  //     closeTopMenu()
  //     location.hash = '/Start/';
  //     // console.log("gotoWelcome");
  // };
  //
  self.gotoArticleAbstract = function (data) {
    closeTopMenu();
    if (self.skipAbstractMode() && self.loggedInToServerObs()) {
      location.hash = '/Document/' + data.documentID;
    } else {
      location.hash = '/Abstract/' + data.documentID;
    }
  };

  self.gotoArticleFullText = function (data) {
    closeTopMenu();
    if (location.hash === '/Document/' + self.currAbstractDocumentID()) {
      // already loaded, but there might have been an error, so check.
      if (self.articleAbstract.search("Authentication error") > 0) {
        location.reload();
      }
    } else {
      location.hash = '/Document/' + self.currAbstractDocumentID();
    }
  };

  // issue contents are shown here in response to a What's New click
  self.gotoIssueContents = function (data) {
    var PEPCode = data.PEPCode.toUpperCase();
    var PEPVol = data.vol;
    var PEPIssue = data.issueInfo;
    location.hash = '/ArticleList/?journal=' + PEPCode + "&vol=" + PEPVol + "&issue=" + PEPIssue; // + "&page=" + PEPPage;
    // console.log("gotoArticleListForIssue" + data.volumeURL);
  };

  // self.gotoSearchResults = function(data) {
  //     location.hash = '/SearchResult/' + data.simpleQuery + "/" + data.queryString;
  // };
  //
  //  self.gotoNewSearch = function (data) {
  //    location.hash = '/Search/';
  //  };
  //
  // function getActiveAccordion() {
  //   var active = $('.accordion').accordion('option', 'active');
  //   // console.log("Active ACC = " + active);
  //   return active;
  // }
  //
  // ********************************************************************************************
  // Load Documents or Download Documents
  // ********************************************************************************************
  self.getDownloadEPUB = function (documentID) {
    // Downloadable EPUB version of full-text if logged in.
    if (self.getCurrentLoginStatus() === false) {
      self.login("");
      //self.lastAction = "getDownloadEPUB";
    } else {
      // Build API call
      var apiCall;
      self.extendedLoginStatus(_("DownloadRequested"));
      apiCall = baseURL + "/v1/Documents/Downloads/" + "EPUB" + "/" + self.currAbstractDocumentID() + "/";
      ga('set', 'page', '/Documents/Downloads/EPub/' + self.currAbstractDocumentID());
      ga('send', 'pageview');
      getDocumentDownload(apiCall, self.currAbstractDocumentID(), "epub", self.accessToken(), self.documentDownloadReadyCallback);
    }
  };

  self.getDownloadPDF = function () {
    // Downloadable PDF version of full-text if logged in.
    // TBD = which one, generated or scanned?
    var apiAddOn;
    var isSpecial;
    var apiCall;
    var documentIDSelection = "";

    if (self.getCurrentLoginStatus() === false) {
      self.login("");
      //self.lastAction = "getDownloadPDF";
    } else {
      // Build API call
      // String(documentIDSelection);
      self.extendedLoginStatus(_("DownloadRequested"));
      documentIDSelection = self.currAbstractDocumentID();
      isSpecial = documentIDSelection.search(/ANIJP-CHI|IJPOpen/i);

      if (isSpecial !== -1) {
        apiAddOn = "?option=embed1";
      } else {
        apiAddOn = "";
      }

      apiCall = baseURL + "/v1/Documents/Downloads/" + "PDF" + "/" + documentIDSelection + apiAddOn;
      ga('set', 'page', '/Documents/Downloads/PDF/' + self.currAbstractDocumentID());
      ga('send', 'pageview');
      getDocumentDownload(apiCall, documentIDSelection, "pdf", self.accessToken(), self.documentDownloadReadyCallback);
    }
  };

  // load the full-text...just need to set the local route here
  self.getDownloadHTML = function (requestedDocumentID) {
    // we must already be logged in, caller should have checked.
    self.articleAbstract("...loading...");
    getDocumentData(requestedDocumentID + "/" + self.lastServerSearchString(), self.accessToken(), self.documentHTMLReadyCallback);
    return;
  };

  self.documentHTMLReadyCallback = function (responseInfoObject, retStatusCode, retStatusMessageObject, responseSetObject) {

    // status message, both for errors and success!

    if (retStatusCode !== 200) {
      // there was an error
      if (retStatusMessageObject === null) {
        self.extendedLoginStatus("(Error Code " + retStatusCode + ")");
      }
      else {
        self.extendedLoginStatus(getStatusMessageObjectText(retStatusMessageObject));
      }
      // blank this out since it otherwise says "Loading..."
      self.articleAbstract("");
    } else {
      // no error
      self.readModeIsDocument(true);
      if (responseSetObject.accessLimited === true) {
        // hide download buttons
//        console.log("access limited!");
        self.showReadandDownloadButtons(false);
      }
      else {
        self.showReadandDownloadButtons(true);
      }

      // keep track of the current document
      self.currAbstractDocumentID(responseSetObject.documentID);
      self.currDocumentID = responseSetObject.documentID; // keep track so we know if reload is needed

      // now we have to load the document into the abstract/document area!
      self.articleAbstract(responseSetObject.document);

      hitCursor.initialize();

      if (self.requestedHTMLAnchor !== "") {
        //# jump to location
        scrollToAnchor(self.requestedHTMLAnchor);
        self.requestedHTMLAnchor = "";
      }

      // XXX LATER - DEAL WITH TRANSCRIPTION XXX
      // var videoTranscription = $(".video-container div:nth-child(2)").html();
      // if (videoTranscription !== undefined) {
      //   videoTranscription = document.createElement(videoTranscription);
      //   console.log(videoTranscription);
      //   $(".video-container div:nth-child(2)").appendChild(videoTranscription);
      //   //postscribe($(".video-container div:nth-child(2)"), videoTranscription);
      // }
    }

    // update document (login state) status
    self.extendedLoginStatus(getStatusMessageObjectText(retStatusMessageObject));

  };

   self.glossaryEntryHTMLCallback = function (responseInfoObject, retStatusCode, retStatusMessageObject, responseSetObject) {
    // there was an error
    if (retStatusCode !== 200) {
      // not logged in (should not happen, since we don't allow the links if not logged in)
      //self.currGlossaryEntryHTML("Not logged in.");
      self.currGlossaryEntryHTML(getStatusMessageObjectText(retStatusMessageObject, "jsMustBeLoggedInGlossary"));
    } else {
      self.currGlossaryEntryHTML(responseSetObject.document);
    }
  };


  self.documentDownloadReadyCallback = function (responseLength, retStatusCode, retStatusMessageObject, documentID, downloadLocation) {
    // there was an error
    if (retStatusCode !== 200) {
      // not logged in
      self.extendedLoginStatus(getStatusMessageObjectText(retStatusMessageObject));
      // console.warn(retStatusMessageObject.description + "(Error Code " + retStatusCode + ")");
      //self.login("");
    } else {
      // console.log(retStatusMessage + "(Code " + retStatusCode + ")");
      //self.statusMessage("");
      //self.extendedLoginStatus(retStatusMessageObject.description);
      var msg;
      if (downloadLocation === null) {
        msg = getStatusMessageObjectText(retStatusMessageObject, "downloadFail");
      } else {
        msg = _("DownloadSuccessful", {downloadFilename: downloadLocation});
      }
      self.extendedLoginStatus(msg);
      //self.extendedLoginStatus(getStatusMessageObjectText(retStatusMessageObject));
    }
  };
  // ********************************************************************************************
  // END Load Documents or Download Documents
  // ********************************************************************************************


  //******************************************************************************************
  // User options
  // called by the checkmark widget
  //******************************************************************************************
  // called by the checkmark widget per index.html
  self.changedGlossaryStyle = function (data) {
    if (self.showGlossaryTerms() === true) {
      // self.showGlossaryTerms(true);
      setGlossaryStyle(true);
    } else {
      // self.showGlossaryTerms(false);
      setGlossaryStyle(false);
    }
    return true;
  };

  // called by the checkmark widget per index.html
  self.changedBroadenSearch = function () {
    // Toggle the variable which determines whether or not to add a * to author/title per Mosher
    setCookie("broadenSearch", self.broadenSearch(), 100);
    return true;
  };

  // called by the checkmark widget per index.html
  self.changedJustifyStyle = function (data) {
    if (self.justifyText() === true) {
      // $('body').addClass('justify');
      // self.justifyText(true);
      setJustifyStyle(true);
    } else {
      // $('body').removeClass('justify');
      // self.justifyText(false);
      setJustifyStyle(false);
    }
    return true;
  };

  // called by the checkmark widget per index.html
  self.changedAbstractMode = function (data) {
    setCookie("skipAbstractMode", self.skipAbstractMode(), 100);
    ga('set', 'page', '/skipAbstractMode/' + self.skipAbstractMode());
    ga('send', 'pageview');
    //    console.log("skipAbstractMode Set to: " + self.skipAbstractMode());
    return true;
  };

  // called by the checkmark widget per index.html
  self.changedStayLoggedIn = function (data) {
    // No longer a persistent option
      //setCookie("stayLoggedIn", self.stayLoggedIn(), 100);
    // console.log("StayLoggedIn Set to: " + self.stayLoggedIn());
    // change the timer now, because the option changed, so the time must change.
    self.createHearbeatTimer();
    return true;
  };

  // ********************************************************************************************
  // Options Control callbacks
  // ********************************************************************************************
  self.compactSearchMode = ko.computed(function () {
    var retVal = this.compactSearchModeSelected();
    setCookie("compactSearchModeSelected", retVal, 100);
    //console.log("CompactSearch computed is: " + this.compactSearchModeSelected());
    //console.log("compared to: " + self.compactSearchModeSelected());
    self.changeShowStateObjects(self.showFullSearchForm);
    ga('set', 'page', '/SearchMode/' + retVal);
    ga('send', 'pageview');
    return retVal;
  }, this);

  self.languageSelection = ko.computed(function () {
    var retVal = this.selectedLanguage();
    ga('set', 'page', '/Language/' + retVal);
    ga('send', 'pageview');

    if (retVal.length > 1) {
      document.webL10n.setLanguage(retVal);
      //console.log("Selected (saved) Language: " + retVal);
      setCookie("language", retVal, 100);
    }
    return retVal;
  }, this);


  self.styleSelectionChanged = function (obj, event) {
    if (event.originalEvent) { //user changed
      // alert(self.selectedEndpoint());
      switch_style(self.selectedStyleSheet());
      ga('set', 'page', '/Theme/' + self.selectedStyleSheet());
      ga('send', 'pageview');
    } else { // program changed
      alert("event2!");
    }
  };

  // If the user changes the Sort Order pulldown, redo the search with this sort order
  self.sortOrderChanged = function (obj, event) {
    if (event.originalEvent) { //user changed
      // alert(self.selectedEndpoint());
      self.doSearch(obj, event);
      // not sure we want to save the sort order, but for now, let's try
      setCookie("sortOrder", self.searchSortOrder(), 100);
      ga('set', 'page', '/SortOrder/' + self.searchSortOrder());
      ga('send', 'pageview');
    } else { // program changed
      alert("unexpected error-cannot perform sort order!");
    }
    return;
  };

  // ********************************************************************************************
  // Interface Actions
  // ********************************************************************************************
  self.doClear = function (arrObj) {
    // location.hash = '/Search/';
    // make sure we don't analyze after every clear!
    // clear the search form
    self.searchAuthorText("");
    self.searchTitleText("");
    self.searchYearText("");
    self.searchJournal("All");
    // do we want to clear the results?
    self.isValidKWIC(false);
    self.articleList([]);
    self.searchWordsText("");
    self.noMatchesFoundMessage("");
    if (self.searchAnalysisPending) {
      self.searchAnalysisClearPending = true;
    }
    self.searchAnalysisArray([]);
    // this should trigger it.

    // clear the URL
    // otherwise, repeating a search doesn't work.
    //location.hash = '/Search/?viewperiod=';
  };

  self.gotoArticleNumber = function (data, event) {
    var offset = parseInt(self.searchResultsOffset());
    self.searchResultsOffset(offset);
    // self.doSearch(data, event);
    return false;
  };

  self.doSearch = function (data, event) {
    // Go ahead with the search
    // Load journals, books, videos from server call
    //    var marker = "?";
    searchDisplayString = "";

    var searchStrObj = self.getSearchStringFromForm();
    var searchStr = searchStrObj["searchString"];
    var displayString = searchStrObj["displayString"];
    // if (searchStr !== lastSearchString) {
    //     self.searchResultsOffset(0);
    //     // self.articleList([]);
    //     lastSearchString = searchStr;
    // }

    if (searchStr === "") {
      searchStr = "?journal=";
    }
    //console.log(fixedEncodeURIComponent(searchStr));
    // location.hash = '/Search/' + searchStr;
    location.hash = '/Search/' + searchStr +
      "&limit=" + self.selectedReturnSetSize() + "&offset=" + self.searchResultsOffset();
    // sammy does the work with the local route
    return false;
  }; // end doSearch

  //******************************************************************************************
  //******************************************************************************************
  //******************************************************************************************
  // Client-side routes (the route after the #) SAMMY.JS
  //******************************************************************************************
  //******************************************************************************************
  //******************************************************************************************
  Sammy(function () {
    // Download a linked PDF (e.g., IJP-CHI)
    this.get('#LinkedDownloads/PDF/:docID', function () {
      var docID = this.params.docID;
      self.getDownloadPDF();
    });

    this.get('#/', function () {
      // console.log("Home");
    });

    // this.get('#/ArticleList:selectedPEPCode?/:selectedVolume?/:selectedIssue?', function() {
    this.get('#/ArticleList/', function (context) {
      self.doClear();
      var limit;
      var offset;
      var queryString;
      var searchListing;

      self.currentSearchDisplayString("");

      // closeTopMenu();
      // console.log("PEPCode2: " + this.params.selectedPEPCode);
      // console.log("Volume2: " + this.params.selectedVolume);
      // console.log("Issue: " + this.params.selectedIssue);
      var selectedPEPCode = context.params.journal;
      var selectedVolume = context.params.vol;
      var selectedIssue = context.params.issue;
      var selectedPage = context.params.page;
      if (typeof context.params.limit === 'undefined') {
        limit = self.selectedReturnSetSize();
      } else {
        limit = context.params.limit;
      }
      if (typeof context.params.offset === 'undefined') {
        offset = 0;
      } else {
        offset = context.params.offset;
      }

      // translated strings
      var _ = document.webL10n.get;

      if (selectedIssue !== undefined) {
        queryString = "?journal=" + selectedPEPCode + "&" + "volume=" + selectedVolume + "&issue=" + selectedIssue; // + "&limit=" + limit;
        searchListing = _('jsSearchListingIss', {
          jrnlCode: selectedPEPCode,
          jrnlVol: selectedVolume,
          jrnlIss: selectedIssue
        });
        if (searchListing !== "{{jsSearchListingIss}}") {
          self.currentSearchDisplayString(searchListing);
        }
      } else {
        queryString = "?journal=" + selectedPEPCode + "&" + "volume=" + selectedVolume; // + "&limit=" + limit;
        searchListing = _('jsSearchListing', {
          jrnlCode: selectedPEPCode,
          jrnlVol: selectedVolume
        });
        if (searchListing !== "{{jsSearchListing}}") {
          self.currentSearchDisplayString(searchListing);
        }
      }

      ga('set', 'page', '/ArticleList/' + queryString);
      ga('send', 'pageview');

      // console.log("QueryString: " + queryString);
      var apiCall = baseURL + "/v1/Database/Search/" + queryString;
      self.articleListPager1.init(apiCall, offset, limit);

      // $("#displayRank").hide();
      self.showRanks(false);
      $("#accordion").accordion({
        active: accordions["search"]
      });
    });

    this.get('#/Search/?', function (context) {
      ga('set', 'page', '/Search/');
      ga('send', 'pageview');
      self.currentSearchDisplayString("");
      var searchDisplayString = "";
      self.doClear();
      //$("#displayRank").hide(); // only for full text queries
      self.showRanks(false);
      var searchResultsLimit; // so parameter can change value without affecting result
      // console.log("Context Param: " + context.params.limit + ", " + context.params.offset);
      if (context.params.keys("toHash").length === 0) {
        // no arguments
        //console.log("No args.  Do a clear.");
        /// XXX (cleared above)
      } else {
        if (context.params.limit !== undefined) {
          if (context.params.offset >= 0) { // just to make sure it's numeric
            searchResultsLimit = context.params.limit;
          } else {
            searchResultsLimit = self.selectedReturnSetSize();
          }
        }
        if (context.params.offset !== undefined) {
          if (context.params.offset >= 0) {
            self.searchResultsOffset(context.params.offset);
          }
        } else {
          self.searchResultsOffset(0);
        }

        // dummy start of string so it starts with ?
        var queryString = "";
        var dateTypeAddOn = "";
        // var l10AuthorStr = document.webL10n.get('Author');
        // var l10TitleStr = document.webL10n.get('Title');
        // var l10DateBetweenStr = document.webL10n.get('Date-Between');
        // var l10DateAfterStr = document.webL10n.get('Date-After');
        // var l10DateBeforeStr = document.webL10n.get('Date-Before');
        // var l10DateOnStr = document.webL10n.get('Date-On');

        if (typeof context.params.journal !== 'undefined') {
          queryString = queryString + "?journal=" + context.params.journal;
          self.searchJournal(context.params.journal);
          if (context.params.journal.search(/ipl or/i) > -1)
          { //?journal=gw+or+ipl+or+nlp+or+se+or+zbk
            // all books
            self.searchJournal(bookPEPCodesSearchSpec);
          }
          else if (context.params.journal.search(/afcvs/i) > -1) {
            // videos
           self.searchJournal(videoPEPCodesSearchSpec);
          }
          else if (context.params.journal.search(/pdpsy/i) > -1) {
            // videos
           self.searchJournal(journalPEPCodeSearchSpec);
          }
          else // book
          { //?journal=gw+or+ipl+or+nlp+or+se+or+zbk
            console.log("Why here?: '" + context.params.journal + "' ")
            self.searchJournal(context.params.journal);
          }
          searchDisplayString += " in <b>Source(s): " + context.params.journal + "</b>";
        } else {
          //console.log("Else?: '" + context.params.journal + "' ")
          self.searchJournal("All");
          queryString = queryString + "?journal=";
        }

        if (typeof context.params.author != 'undefined') {
          queryString = queryString + "&author=" + context.params.author;
          self.searchAuthorText(decodeHtml(context.params.author));
          searchDisplayString += "<span class=\"criteriaLabel\">Author(s):</span>" + self.searchAuthorText() + " ";
        }

        if (typeof context.params.title != 'undefined') {
          queryString = queryString + "&title=" + context.params.title;
          self.searchTitleText(decodeHtml(context.params.title));
          searchDisplayString += "<span class=\"criteriaLabel\">Title:</span>" + self.searchTitleText() + " ";
        }

        if (typeof context.params.startyear != 'undefined') {
          queryString = queryString + "&startyear=" + context.params.startyear;
          if (typeof context.params.endyear != 'undefined') {
            queryString = queryString + "&endyear=" + context.params.endyear;
          }
          if (typeof context.params.datetype != 'undefined') {
            queryString = queryString + "&datetype=" + context.params.datetype;
            self.searchDateTypeText(context.params.datetype);
          } else {
            queryString = queryString + "&datetype=On";
            self.searchDateTypeText("On");
          }

          switch (self.searchDateTypeText()) {
            case ("Between"): // After
              dateTypeAddOn = "^";
              self.searchYearText(dateTypeAddOn + context.params.startyear + "-" + context.params.endyear);
              searchDisplayString += "<span class=\"criteriaLabel\">Date Between:</span>" + context.params.startyear + "-" + context.params.endyear + " ";
              break;
            case ("Since"): // After
              dateTypeAddOn = ">";
              self.searchYearText(dateTypeAddOn + context.params.startyear);
              searchDisplayString += "<span class=\"criteriaLabel\">Date After:</span>" + dateTypeAddOn + context.params.startyear + " ";
              break;
            case "Before": // Before
              dateTypeAddOn = "<";
              self.searchYearText(dateTypeAddOn + context.params.startyear);
              searchDisplayString += "<span class=\"criteriaLabel\">Date Before:</span>" + context.params.startyear + " ";
              break;
            case "On": // default
              dateTypeAddOn = "";
              self.searchYearText(dateTypeAddOn + context.params.startyear);
              searchDisplayString += "<span class=\"criteriaLabel\">Date On:</span>" + context.params.startyear + " ";
              break;
              // fall through
            default:
              dateTypeAddOn = "";
              self.searchYearText(dateTypeAddOn + context.params.startyear);
          }
        }

        if (typeof context.params.volume != 'undefined') {
          queryString = queryString + "&volume=" + context.params.volume;
          self.searchVolume(context.params.volume);
          if (self.searchJournal() === "") {
            searchDisplayString += " in <b>volume " + context.params.volume + "</b>";
          } else {
            searchDisplayString += " and <b>volume " + context.params.volume + "</b>";
          }
        } else {
          self.searchVolume("");
        }

        if (typeof context.params.issue != 'undefined') {
          queryString = queryString + "&issue=" + context.params.issue;
          self.searchIssue(context.params.issue);
          searchDisplayString += " in <b>issue " + context.params.issue + "</b>";
        } else {
          self.searchIssue("");
        }

        if (typeof context.params.artqual != 'undefined') {
          queryString = queryString + "&artqual=" + context.params.artqual;
          searchDisplayString += "<span data-l10n-id='Related-documents' class=\"criteriaLabel\">Related Documents</span>" + " ";
        }

        if (typeof context.params.origrx != 'undefined') {
          queryString = queryString + "&origrx=" + context.params.origrx;
          searchDisplayString += "<span data-l10n-id='Translations' class=\"criteriaLabel\">Available Translations</span>" + " ";
        }

        if (typeof context.params.fulltext1 != 'undefined') {
          queryString = queryString + "&fulltext1=" + context.params.fulltext1;

          var wordsOrPhrases = _('jsWordsOrPhrases', {
            searchWordsText: self.searchWordsText()
          });

          self.searchWordsText(context.params.fulltext1);
          searchDisplayString += "<span data-l10n-id='Words-or-phrases' class='criteriaLabel'>Words or phrases:</span>" + " " + self.searchWordsText() + " ";
          // $("#displayRank").show(); // only for full text queries
          self.showRanks(true);

        } else {
          self.searchWordsText("");
        }

        if (queryString === "") {
          alert("Please enter some search criteria");
        }
        // record analytics before sort added.
        ga('set', 'page', '/Search/' + queryString);
        ga('send', 'pageview');

        if (typeof context.params.sort != 'undefined') {
          queryString = queryString + "&sort=" + context.params.sort;
          self.searchSortOrder(context.params.sort);
        }

        self.lastServerSearchString("?search='" + fixedEncodeURIComponent(queryString) + "'");
        // console.log("Server API Search to be included in a document call to show hits: ", self.lastServerSearchString());

        // queryString += "&limit=" + searchResultsLimit + "&offset=" + self.searchResultsOffset();
        // console.log("Client Side: " + queryString);
        queryString += "&sort=" + self.searchSortOrder();

        // do analysis, just in case
        self.doSearchAnalysis();

        var apiCall = baseURL + "/v1/Database/Search/" + queryString;
        self.articleListPager1.init(apiCall, self.searchResultsOffset(), searchResultsLimit);
        // self.currentSearchDisplayString("<span data-l10n-id='Results' class='criteriaLabel'>Results: </span>" + searchDisplayString);
        // try showing nothing instead
        //self.currentSearchDisplayString("Searching...");
      }

      // self.currentSearchDisplayString(searchDisplayString);
      $("#accordion").accordion({
        active: accordions["search"]
      });

    });

    this.get('#/Abstract/?', function () {
      $("#accordion").accordion({
        active: accordions["abstract"]
      });
      ga('set', 'page', '/Abstract/');
      ga('send', 'pageview');
      // don't refresh the panel if the route is just to the accordion itself
      //$("#detailPanel").innerHTML = self.articleAbstract();
    });

    this.get('#/Start/?', function () {
      $("#accordion").accordion({
        active: accordions["start"]
      });
      // don't refresh the panel if the route is just to the accordion itself
      //$("#detailPanel").innerHTML = self.articleAbstract();
    });

    this.get('#/Abstract/:documentID', function () {
      // Get the abstract, put it in the observable self.articleAbstract
      var documentID = this.params.documentID;
      ga('set', 'page', '/Abstract/');
      ga('send', 'pageview');
      self.currAbstractDocumentID(documentID);
      self.currDocumentID = ""; // no fulltext document loaded
      self.extendedLoginStatus("");
      self.readModeIsDocument(false);
      self.articleAbstract("...fetching abstract...");
      // function is in pepwebapi convenience library
      if (self.loggedInToServerObs() === undefined) {
        checkLoginStatus(baseURL, self.accessToken(), self.loginStatusCallback);
      }
      ga('set', 'page', '/Abstract/' + documentID);
      ga('send', 'pageview');
      getAbstractWithCred(documentID, self.accessToken(), self.getAbstractCallback);
      $("#accordion").accordion({
        active: accordions["abstract"]
      });
    });

    this.get('#/Document/:documentID', function () {
      // Get the full document when coming from a link in another document
      // We may want to always go to the abstract though since this is mobile.
      // Pros: speed
      // Cons: Can't jump to a sublocation within a document based on the URL.
      var documentID = this.params.documentID;
      ga('set', 'page', '/Document/');
      ga('send', 'pageview');
      var subLocation = documentID.search("#");
      var reloadNeeded = true;
      self.closeModals();
      checkLoginStatus(baseURL, self.accessToken(), self.loginStatusCallback);
      if (self.loggedInToServerObs() === false) {
      //        console.log("We need to log you in!");
        self.login();
      }

      if (self.loggedInToServerObs() === false) {
        // try previous URL
        window.history.back();
        return false;
      }

      // XXX we need to make sure we're in the right document before we do this!
      if (subLocation !== -1) {
        self.requestedHTMLAnchor = documentID.substring(subLocation + 1);
        var baseDocumentID = documentID.substring(0, subLocation);
        if (baseDocumentID === self.currDocumentID) {
          //  just jump there
          scrollToAnchor(self.requestedHTMLAnchor);
          // self.requestedHTMLAnchor = ""; (done in scroll)
          reloadNeeded = false;
        }
        // console.log("Anchor Location Requested in URL: " + self.requestedHTMLAnchor);
      } else {
        self.requestedHTMLAnchor = "";
      }

      if (reloadNeeded) {
        self.articleAbstract("... Loading Document ...");
        ga('set', 'page', '/Document/' + documentID);
        ga('send', 'pageview');
        // function is in pepwebapi convenience library
        // as long as function is successful, the new currDocumentID and currAbstractDocumentID will be stored in the callback
        self.getDownloadHTML(documentID);
        // getAbstract(documentID, self.articleAbstract);
        $("#accordion").accordion({
          active: accordions["abstract"]
        });
        window.scrollTo(0, 0);
      } else { // we still need to make sure we're in the right tab/section
        $("#accordion").accordion({
          active: accordions["abstract"]
        });
      }

    });

    this.get('', function () {
      // console.log("Home");
    });


  }).run();

  // Initializaton Action!
  getListOfWhatsNew(self.currWhatsNewList);
  // Changed both to 5 for testing
  // Most Cited
//  getListOfMost(baseURL + "/v1/Database/Search/?citecount=100&limit=5", self.currMostCitedData, self.statusMessageLocal, serverFlag = false);
  getListOfMost(baseURL + "/v1/Database/MostCited/?period=5&limit=5", self.currMostCitedData, self.statusMessageLocal, serverFlag = false);
    // console.log("Back!");
    //  getListOfMost(baseURL + "/v1/Database/Search/?viewcount=90&viewperiod=month&limit=5", self.currMostDownloadedData, self.statusMessageLocal, serverFlag = true);
  getListOfMost(baseURL + "/v1/Database/MostDownloaded/?viewcount=90&viewperiod=month&limit=5", self.currMostDownloadedData, self.statusMessageLocal, serverFlag = true);
  // console.log("Back2!");
  getListOfSources(baseURL + "/v1/Metadata/Journals/", self.journals, self.sourcesLoadedCallback);
  // extra item for none.
  // blank entry for none.
//  self.journals().push({
//    title: _("jsAllSources"),
//    PEPCode: "All"
//  });
//  self.journals().push({
//    sourceType: "Videos",
//    title: _("jsAllVideos"),
//    PEPCode: "afcvs+or+bpsivs+or+ijpvs+or+ipsavs+or+nypsivs+or+pcvs+or+pepgrantvs+or+peptopauthvs+or+pepvs+or+sfcpvs+or+spivs+or+uclvs",
//    volume: null,
//    //contentsAPIURL: contentsAPIURL,
//    // volListURL: volListURL,
//    documentID: null,
//    issn: null,
//    isbn: null
//  });
  //  console.log("Pushing Book List onto Journal (source) list")
//  self.journals().push({
//    sourceType: "Books",
//    title: _("jsAllBooks"),
//    PEPCode: "gw+or+ipl+or+nlp+or+se+or+zbk",
//    volume: null,
//    //contentsAPIURL: contentsAPIURL,
//    // volListURL: volListURL,
//    documentID: null,
//    issn: null,
//    isbn: null
//  });

//  self.journals().sort(sort_by('title', false, function(a){return a.toUpperCase()}));

  cookie = getCookie("style");
  self.selectedStyleSheet(cookie);
  cookie = getCookie("fontSize", "1.5");
  // console.log("Fontsize: " + cookie);
  self.selectedFontSize(cookie);
} //end of function viewModel

//var baseURL = "http://api.pep-web.info";
//var baseURL = "http://stage.pep.gvpi.net/api";
//var baseURL = "https://www.pep-web.org/api";
var baseURL = "http://127.0.0.1:8000";


// save the instance so we can  easily call inside of the view model
window.vm = new PEPArticlesViewModel();
ko.applyBindings(window.vm);

// ko.applyBindings(new PEPArticlesViewModel());
