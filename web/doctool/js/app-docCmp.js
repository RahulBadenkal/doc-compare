/*** create application object, inject dependencies, set configuration parameters ***/
'use strict';

angular.module('sarciDrilsDocCmp',['ui.router', 'ngMaterial', 'ngMessages', 'ngStorage', 'cfp.hotkeys', 'ngIdle', 'pikaday'])

.config(function($httpProvider, $mdDateLocaleProvider, $localStorageProvider, hotkeysProvider) {
    
    // to  allow cross domain call
    $httpProvider.defaults.useXDomain = true;
    $httpProvider.defaults.withCredentials = true;

    // to set date format for datePicker control
    $mdDateLocaleProvider.formatDate = function(date) {
        return date ? moment(date).format('DD-MM-YYYY') : '';
    };
    
    // to set date format for keyboard input
    $mdDateLocaleProvider.parseDate = function(dateString) {
        var m = moment(dateString, 'DD-MM-YYYY', true);
        return m.isValid() ? m.toDate() : new Date(NaN);
    }; 
    
    // to change the prefix used by ngStorage
    $localStorageProvider.setKeyPrefix('sarciDRILL');
    
    // to disable the cheatsheet displayed by hotkeys
    hotkeysProvider.includeCheatSheet = true;
})


.config(['$idleProvider', function($idleProvider) {
	$idleProvider.idleDuration(20 * 60); //in seconds
	$idleProvider.warningDuration(60); // in seconds
	$idleProvider.autoResume(true);
	$idleProvider.keepalive(false);
	
	var idleEvents = [ 'keydown', 'DOMMouseScroll', 'mousewheel', 'mousedown', 'mousemove' ];
	$idleProvider.activeOn(idleEvents.join(' '));
}])


.run(function($rootScope) {
	$rootScope.isDebug = true;

	$rootScope.isOnline = navigator.onLine ? true : false;
	$rootScope.$apply();

	window.addEventListener("online", function() {
		$rootScope.isOnline = true;
		$rootScope.$apply();
	}, true);

	window.addEventListener("offline", function() {
		$rootScope.isOnline = false;
		$rootScope.$apply();
	}, true);
	
/*
	$rootScope.consoleLog = function() {
		for (var i = 0; i < arguments.length; i++) {
			console.log(arguments[i]);
		}
	};
*/
	
})
.factory('sarciUIConfig', function() {
	var cardSt = {};

	
  	return {
		uiStyles : {
			cloudOff  	: {'color': 'lightgrey'}, 
			cloudGood  	: {'color': 'green'}, 
			cloudBad	: {'color': 'yellow'}, 
			logo  	  	: {'width': '40px', 'height': '40px'}, 
			minilogo  	: {'width': '20px', 'height': '20px'}, 
			toolbar	  	: {'background-color':'#424242'}, 
			appIcon	  	: {'color':'white'}, 
			appBtn	  	: {'background':'white', 'color':'black'}, 
			rptIcon	  	: {'color':'black'}, 
			hdrNormal 	: {'color':'#ffffff'}, 
			hdrAlert  	: {'color':'#CC0000'}, 
			hdrPositive	: {'color':'#2F74D0'}, 
			hdrStatus 	: {'color':'#FF8A8A', 'font-size':'28px'}, 
			 
			
			
//			keySelect	: { 'border': '1px solid silver' }, 
//			keyUnselect	: { 'border': '0px' }, 
			keySelect	: { 'color': 'white' }, 
			keyUnselect	: { 'color': 'black' }, 
            keySelectBtn   : { 'background-color': 'transparent' },
            keyUnselectBtn : { 'background-color': '' },
			
			cntrlState	: {
				disabled : {'color': 'lightgrey'}, 
				keys  : {'color': 'white'}, 	email   : {'color': 'white'}, 		print   : {'color': 'white'}, 
				notes : {'color': 'white'},	 	save    : {'color': '#95A9F5'}, 	close   : {'color': '#D8D8D8'},  
				open  : {'color': '#A8D6AB'}, 	lock    : {'color': '#AF6161'},		unlock  : {'color': '#A8D6AB'},		
				task  : {'color': '#F9AE63'}, 	cancel  : {'color': '#CF7EEC'}, 	archive : {'color': '#D8D8D8'},	
				copy  : {'color': 'white'}, 	tmsheet : {'color': 'white'},		post	: {'color': '#F9AE63'}, 
												history : {'color': 'white'}, 	
			},
			
		}, 
	
  	};
})

