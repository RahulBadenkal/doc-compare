/*** controller for all the forms of the doc tool ***/
'use strict';

angular.module('sarciDrilsDocCmp')

.controller('docToolCtrl', function($scope, $state, $filter, $timeout, $interval, $stateParams, $mdDialog, $mdMedia, $window, $localStorage, $http, 
			hotkeys, $rootScope,sarciUIConfig) {
    
	if ($rootScope.isDebug) {console.log("docToolCtrl controller");}
	
	$scope.uiStyles = sarciUIConfig.uiStyles;
        // const selectFilesDivID = 'selectFiles';
        const file1inputID = "file1input";
        const file2inputID = "file2input";

        // const showPdfsDivID = "showPdfs";
        const leftPdfIframeID = "left-comparision-content-document";
        const rightPdfIframeID = "right-comparision-content-document";
        const viewerContainerID = "viewerContainer";
        const leftPdfScrollMarkID = 'left-comparision-scroll-mark';
        const rightPdfScrollMarkID = 'right-comparision-scroll-mark';
        const pdfUrlPrefix = "pdfjs/web/pdf-viewer.html?file=";

        let pdfsScrollEventObj = null;
        let diffs = null;
        let elem = document.documentElement;

        $scope.display_file1name = "Master File";
        $scope.display_file2name = "Revised File";
        $scope.fullscreen = true;
        $scope.input_default_filepaths = ["", ""];
        $scope.input_file1path = $scope.input_default_filepaths[0];
        $scope.input_file2path = $scope.input_default_filepaths[1];
        $scope.input_default_filenames = ["Choose Source file", "Choose Destination file"];
        $scope.input_file1name = $scope.input_default_filenames[0];
        $scope.input_file2name = $scope.input_default_filenames[1];
        $scope.isErr = true;
        $scope.progressBarMsg = '';
        $scope.isProcessCancelled = false;
	
		$scope.toggle = function () {
      $scope.state = !$scope.state;
    };

		//IIFE
    (function() {
        if ($rootScope.isDebug) {console.log("inside login ctrl iife");}

		$state.go('docTool');
		
	})();

        $scope.setCancelProcess = function(){
          $scope.isProcessCancelled = true;
        };

        $scope.getFile = async function (file_id) {
            // Find out which file (master or revised) is being uploaded by user
            let docNo = -1;
            console.log(file_id);
            if (file_id === file1inputID) {
                docNo = 0;
            } else if (file_id === file2inputID) {
                docNo = 1;
            }
            // Open desktop native choose file dialog
            let result = await eel.ask_file(docNo)();
            console.log(result);
            let filepath = result['data']['filepath'];
            let filename = result['data']['filename'];
            // Set the chosen file filepath and display the filename
            if (docNo === 0) {
                if (filepath === "") {
                    $scope.input_file1path = $scope.input_default_filepaths[0];
                    $scope.input_file1name = $scope.input_default_filenames[0];
                } else {
                    $scope.input_file1path = filepath;
                    $scope.input_file1name = filename;
                }
            } else if (docNo === 1) {
                if (filepath === "") {
                    $scope.input_file2path = $scope.input_default_filepaths[1];
                    $scope.input_file2name = $scope.input_default_filenames[1];
                } else {
                    $scope.input_file2path = filepath;
                    $scope.input_file2name = filename;
                }
            }
        };

        async function startProcess() {
            $scope.moduleError = "";
            console.log(`Input Original file: ${$scope.input_file1path}`);
            console.log(`Input Revised file: ${$scope.input_file2path}`);

            let result1 = await eel.check_if_file_exists($scope.input_file1path)();
            let result2 = await eel.check_if_file_exists($scope.input_file2path)();
            if (result1['data']['isfile'] && result2['data']['isfile']) {
                $scope.progressBarMsg = "Loading.....";
                $scope.isProcessCancelled = false;
                $scope.startProgressBar();
                let api_result = await eel.get_diff($scope.input_file1path, $scope.input_file2path,
                    functionName(updateProgressBarMsg),
                    functionName(isProcessCancelled))();
                console.log("get_diff_api:");
                console.log(api_result);
                // Add error handling here
                if (api_result['result'] === false) {
                    $scope.isErr = api_result['result'];
                    $scope.moduleError = api_result['errmsg'];
                    $scope.stopProgressBar();
                    // TODO: Display error msg in a better way
                    window.alert("ERROR:\n" + api_result['errmsg']);
                    console.log(api_result['errmsg'], $scope.isErr);
                    return;
                }
                let api_output = api_result['data'];
                diffs = api_output['diff_locs'];
                let outfilespath = api_output['outfilespath'];

                    // //In case the pdf file is present within the root of server then:
                    // leftPdfUrl = api_output['outfilespath'][0] // The path here should be relative to root folder (if not then make it)
                    // setPdfUrl(leftPdfIframeID, leftPdfUrl)
                    // function setPdfUrl(iframeID, url){
                    //     let iframe = document.getElementById(iframeID);
                    //     let rand = Math.floor((Math.random() * 1000000) + 1);
                    //     iframe.src = pdfUrlPrefix + url + "?uid=" + rand;
                    // }

                // Get the base64 representation of pdfs
                result1 = await eel.pdf_to_base64(outfilespath[0])();
                result2 = await eel.pdf_to_base64(outfilespath[1])();
                let leftPdfB64Str = result1['data']['blob'];
                let rightPdfB64Str = result2['data']['blob'];
                // Get pdf urls from base64Str
                let leftPdfUrl = getPdfUrlsFromB64Str(leftPdfB64Str);
                let rightPdfUrl = getPdfUrlsFromB64Str(rightPdfB64Str);
                // Set pdf urls
                setPdfUrl(leftPdfIframeID, leftPdfUrl);
                setPdfUrl(rightPdfIframeID, rightPdfUrl);

                // Set the output filenames
                $scope.display_file1name = api_output['outfilesname'][0];
                $scope.display_file2name = api_output['outfilesname'][1];

                // Highlight the scroll bars
                hightlightScollbar();

                // Resetting the variables values
                $scope.input_file1name = $scope.input_default_filenames[0];
                $scope.input_file2name = $scope.input_default_filenames[1];
                $scope.input_file1path = $scope.input_default_filepaths[0];
                $scope.input_file2path = $scope.input_default_filepaths[1];

                // Remove loading page sign
                $scope.stopProgressBar();

            } else {
                // TODO: Display error msg in a better way
                window.alert("ERROR\nPlease select files to compare");
                console.log("Please select files to compare");
            }
        }

        function getPdfUrlsFromB64Str(base64Str) {
            let uint8Array = convertDataURIToBinary(base64Str); // Convert base64Str to Uint8Array Binary
            const blob = new Blob([uint8Array], {type: "application/pdf"}); // Convert uint8Array to blob
            let url = webkitURL.createObjectURL(blob); // Convert blob to url
            let encodedUrl = encodeURIComponent(url); // Encoding the url
            return encodedUrl;
        }

        function setPdfUrl(iframeID, url) {
            let iframe = document.getElementById(iframeID);
            iframe.src = pdfUrlPrefix + url;
        }

        function convertDataURIToBinary(b64Str) {
            let raw = window.atob(b64Str);
            let rawLength = raw.length;
            let array = new Uint8Array(new ArrayBuffer(rawLength));
            for (let i = 0; i < rawLength; i++) {
                array[i] = raw.charCodeAt(i);
            }
            return array;
        }

        // TODO: Correct the positions of highlight
        function hightlightScollbar() {
            // Removing already present highlights
            let parentID = [leftPdfScrollMarkID, rightPdfScrollMarkID];
            for (let i = 0; i < parentID.length; i++) {
                let parentElem = document.getElementById(parentID[i]);
                while (parentElem.firstChild) {
                    parentElem.removeChild(parentElem.firstChild);
                }
            }
            // Adding new highlights
            console.log("Diffs length: ", diffs.length);
            for (let i = 0; i < diffs.length; i++) {
                let docNo = diffs[i]['index'];
                let newDiv = document.createElement('div');
                let normYPos = diffs[i]['normYPos'];
                let normHeight = diffs[i]['normHeight'];
                newDiv.style.top = normYPos + "%";
                newDiv.style.height = normHeight + "%";
                if (docNo === 0) {
                    // Deletions
                    let parentDiv = document.getElementById(leftPdfScrollMarkID);
                    parentDiv.appendChild(newDiv);
                    newDiv.className = "highlight-left";
                } else if (docNo === 1) {
                    // Deletions
                    let parentDiv = document.getElementById(rightPdfScrollMarkID);
                    parentDiv.appendChild(newDiv);
                    newDiv.className = "highlight-right";
                }

            }
        }

        $scope.setSyncScroll = function () {
            let leftIframe = document.getElementById(leftPdfIframeID);
            let leftInnerDoc = leftIframe.contentDocument || leftIframe.contentWindow.document;
            let leftViewerContainer = leftInnerDoc.getElementById(viewerContainerID);

            let rightIframe = document.getElementById(rightPdfIframeID);
            let rightInnerDoc = rightIframe.contentDocument || rightIframe.contentWindow.document;
            let rightViewerContainer = rightInnerDoc.getElementById(viewerContainerID);

            // If the elements are not loaded, don't set scrollObj
            if (leftViewerContainer === undefined || leftViewerContainer === null ||
                rightViewerContainer === undefined || rightViewerContainer === null) {
                return;
            }

            // If Start of the app or start of next compare
            if (pdfsScrollEventObj === null ||
                !(leftViewerContainer.isSameNode(pdfsScrollEventObj.leftElem) &&
                    rightViewerContainer.isSameNode(pdfsScrollEventObj.rightElem))) {
                pdfsScrollEventObj = new SyncScroll(leftViewerContainer, rightViewerContainer);
            }

            // Switch status
            if (pdfsScrollEventObj.isActivated) {
                pdfsScrollEventObj.removeScrollEvent();
            } else {
                pdfsScrollEventObj.addScrollEvent();
            }
        };

        $scope.showfileDialog = function (ev) {
			$scope.dlgTitle = "Select Files";
            $scope.closeErrMsg();
            var useFullScreen = ($mdMedia('sm') || $mdMedia('xs')) && $scope.customFullscreen;
            $mdDialog.show({
                controller: DialogController,
                templateUrl: './tpl/dlg-chosefile.html',
                parent: angular.element(document.body),
                targetEvent: ev,
                clickOutsideToClose: false,
                escapeToClose: true,
                fullscreen: useFullScreen,
                scope: $scope,
                preserveScope: true,
                focusOnOpen: false
            })
                .then(function (answer) {
                        $scope.dlgStatus = 'You chose to "' + answer + '".';
                        $scope.dlgOpen = false;
                        if (answer === 'save') {
                            console.log("save dialog");
                            startProcess()
                        }
                    }, function () {
                        $scope.dlgStatus = 'You closed the dialog.';
                        $scope.dlgOpen = false;
                    }
                );
        };

        function DialogController($scope, $mdDialog) {
            $scope.hide = function () {
                $mdDialog.hide();
            };
            $scope.cancel = function () {
                $mdDialog.cancel();
            };
            $scope.answer = function (answer) {
                $mdDialog.hide(answer);
            };
        }

        /* Function to open fullscreen mode */
        $scope.openFullscreen = function () {
            $scope.fullscreen = false;
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.mozRequestFullScreen) { /* Firefox */
                elem.mozRequestFullScreen();
            } else if (elem.webkitRequestFullscreen) { /* Chrome, Safari & Opera */
                elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) { /* IE/Edge */
                elem.msRequestFullscreen();
            }
        };

        /* Function to close fullscreen mode */
        $scope.closeFullscreen = function () {
            $scope.fullscreen = true;
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
        };

        $scope.startProgressBar = function () {
            //if ($rootScope.isDebug) {console.log("start progress----------------------");}
            $scope.dlgProgress = true;

            $mdDialog.show({
                // controller: ctrl,
                template: '<md-dialog id="dlgIdWait" style="box-shadow:none">' +
                    '<md-dialog-content layout="row" layout-margin layout-padding layout-align="center center" aria-label="wait">' +
                    '<md-progress-circular md-mode="indeterminate" md-diameter="30"></md-progress-circular>' +
                    '{{progressBarMsg}}.....' +
                    '</md-dialog-content>' +
                    // '<md-button ng-click="setCancelProcess()">Cancel</md-button>' +
                    '</md-dialog>',
                scope: $scope,
                preserveScope: true,
                parent: angular.element(document.body),
                clickOutsideToClose: false,
                escapeToClose: false,
                fullscreen: false,
            });
        };

        $scope.closeErrMsg = function () {
            $scope.isErr = true;
        };

        $scope.stopProgressBar = function () {
            $mdDialog.cancel();
            $scope.dlgProgress = false;
            //if ($rootScope.isDebug) {console.log("stop progress------------------------");}
        };


        //---------------GENERAL PURPOSE HELPER FUNCTION------------//
        // Class to sync scrolling of two elements
        class SyncScroll {
            constructor(leftElem, rightElem) {
                this.leftElem = leftElem;
                this.rightElem = rightElem;
                this.isActivated = false;
                this.forcedScroll = false;
                this.syncHandler1 = this.sync.bind(this, leftElem, rightElem);
                this.syncHandler2 = this.sync.bind(this, rightElem, leftElem);
            }

            // If we are sure that the visible height doesn't change for the elements then we can store the effectRatio value
            // in a variable instead of computing it every time
            // Visible Height might change when we purposefully resize it in case the browser size becomes small
            static getEffectRatio(causeElem, effectElem) {
                let causeVisibleHeight = causeElem.getBoundingClientRect().height;
                let causeScrollHeight = causeElem.scrollHeight;
                let causeRemHeight = causeScrollHeight - causeVisibleHeight;

                let effectVisibleHeight = effectElem.getBoundingClientRect().height;
                let effectScrollHeight = effectElem.scrollHeight;
                let effectRemHeight = effectScrollHeight - effectVisibleHeight;

                return effectRemHeight / causeRemHeight;
            }

            sync(causeElem, effectElem) {
                console.log("Syncing scroll");
                if (this.forcedScroll) {
                    this.forcedScroll = false;
                } else {
                    let effectRatio = SyncScroll.getEffectRatio(causeElem, effectElem);
                    effectElem.scrollTop = causeElem.scrollTop * effectRatio;
                    this.forcedScroll = true;
                }
            }

            addScrollEvent() {
                console.log("Adding Sync Event");
                this.leftElem.addEventListener('scroll', this.syncHandler1);
                this.rightElem.addEventListener('scroll', this.syncHandler2);
                this.isActivated = true;
            }

            removeScrollEvent() {
                console.log("Removing Sync Event");
                this.leftElem.removeEventListener('scroll', this.syncHandler1);
                this.rightElem.removeEventListener('scroll', this.syncHandler2);
                this.isActivated = false;
            }
        }

    });


// This is called by python but not required by front end
eel.expose(diff_text);
function diff_text(text1, text2, diff_mode, timeout) {
    return getTextDiffs(text1, text2, diff_mode, timeout);
}

function updateProgressBarMsg(msg) {
    let ctrlScope = angular.element(document.getElementsByTagName('body')[0]).scope();
    ctrlScope.progressBarMsg = msg;
}

function isProcessCancelled() {
    let ctrlScope = angular.element(document.getElementsByTagName('body')[0]).scope();
    return ctrlScope.isProcessCancelled;
}

// Library functions
function functionName(func) {
    // Match:
    // - ^          the beginning of the string
    // - function   the word 'function'
    // - \s+        at least some white space
    // - ([\w\$]+)  capture one or more valid JavaScript identifier characters
    // - \s*        optionally followed by white space (in theory there won't be any here,
    //              so if performance is an issue this can be omitted[1]
    // - \(         followed by an opening brace
    //
    let result = /^function\s+([\w\$]+)\s*\(/.exec(func.toString());

    return result ? result[1] : '' // for an anonymous function there won't be a match
}


// The function name passed must be available from 'window'
eel.expose(executeFunctionByName);
function executeFunctionByName(functionName, /*, args */) {
    let context = window;
    let args = Array.prototype.slice.call(arguments, 1);
    let namespaces = functionName.split(".");
    let func = namespaces.pop();
    for (let i = 0; i < namespaces.length; i++) {
        context = context[namespaces[i]];
    }
    return context[func].apply(context, args);
}

//----- General Purpose Helper Functions -----//

// Class to sync scrolling of two elements
class SyncScroll {
    constructor(leftElem, rightElem) {
        this.leftElem = leftElem;
        this.rightElem = rightElem;
        this.isActivated = false;
        this.forcedScroll = false;
        this.syncHandler1 = this.sync.bind(this, leftElem, rightElem);
        this.syncHandler2 = this.sync.bind(this, rightElem, leftElem);
    }

    sync(causeElem, effectElem) {
        console.log("Syncing scroll");
        if (this.forcedScroll) {
            this.forcedScroll = false;
        } else {
            let effectRatio = SyncScroll.getEffectRatio(causeElem, effectElem);
            effectElem.scrollTop = causeElem.scrollTop * effectRatio;
            this.forcedScroll = true;
        }
    }

    // If we are sure that the visible height doesn't change for the elements then we can store the effectRatio value
    // in a variable instead of computing it every time
    // Visible Height might change when we purposefully resize it in case the browser size becomes small
    static getEffectRatio(causeElem, effectElem) {
        let causeVisibleHeight = causeElem.getBoundingClientRect().height;
        let causeScrollHeight = causeElem.scrollHeight;
        let causeRemHeight = causeScrollHeight - causeVisibleHeight;

        let effectVisibleHeight = effectElem.getBoundingClientRect().height;
        let effectScrollHeight = effectElem.scrollHeight;
        let effectRemHeight = effectScrollHeight - effectVisibleHeight;

        return effectRemHeight / causeRemHeight;
    }

    addScrollEvent() {
        console.log("Adding Sync Event");
        this.leftElem.addEventListener('scroll', this.syncHandler1);
        this.rightElem.addEventListener('scroll', this.syncHandler2);
        this.isActivated = true;
    }

    removeScrollEvent() {
        console.log("Removing Sync Event");
        this.leftElem.removeEventListener('scroll', this.syncHandler1);
        this.rightElem.removeEventListener('scroll', this.syncHandler2);
        this.isActivated = false;
    }
}


window.onload = function () {
    console.log("Time until everything loaded: ", Date.now()-timerStart);
};