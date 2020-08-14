/*** set configuration parameters & routing parameters ***/
'use strict';

angular.module('sarciDrilsDocCmp')

.config(function($stateProvider) {
	// to set the views
	$stateProvider
    .state('docTool', {
		url         : '/docTool', 
		templateUrl : '../doctool/tpl/home-doctool.html', 
		params		: { viewType : "cards", viewId: "" },
        controller  : 'docToolCtrl'
	});    
});
