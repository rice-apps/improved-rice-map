'use strict';

var atlasApp = angular.module('atlasApp', ['ngRoute']);

atlasApp.config(function($routeprovider) {
    $routeprovider
      .when('/', {
        templateUrl: '/views/main.html',
        controller: 'MainCtrl'
      })
      .otherwise({
        redirectTo: '/'
      });
  });

console.log('Atlas App loaded.');